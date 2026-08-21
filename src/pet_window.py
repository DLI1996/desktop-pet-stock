"""牛来行情桌宠主窗口：透明无边框置顶窗口 + 角色 + 气泡 + 行情卡 + 右键菜单。"""
from __future__ import annotations

import logging
import os
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal, QRectF, QPointF
from PySide6.QtGui import (QAction, QColor, QFont, QFontMetrics, QPainter,
                           QPainterPath, QPixmap, QTransform)
from PySide6.QtWidgets import QInputDialog, QMenu, QWidget

from .animation_controller import AnimationController
from .audio_controller import AudioController
from .bubble import BubbleController
from .quote_provider import StockDataProvider, is_market_open, validate_symbol
from .state_machine import MarketState, StateMachine

log = logging.getLogger("pet.window")

SIDE_MARGIN = 150    # 左侧留给行情卡
TOP_MARGIN = 240     # 顶部留给气泡
BOTTOM_MARGIN = 16

# 迷你行情卡（人物左侧）：指数名称 + 股价 + 涨跌幅，三项
CARD_W, CARD_H = 216, 92

FIXED_CHAR_H = 200  # 角色高度固定 200px，不支持调节

# 涨跌自动动作：涨了打开抖音摸鱼；跌了打开文档上班
DOUYIN_URL = "https://www.douyin.com/?recommend=1"
WORK_DOC = Path.home() / "Documents" / "牛来上班记录.txt"
AUTO_ACTION_COOLDOWN = 1800  # 同类动作 30 分钟内不重复触发

# 各状态角色在帧内的内容高度占比（实测），用于统一视觉大小：
# 显示帧高 = char_h / ratio，保证不同状态的角色大小一致
STATE_CONTENT_RATIO = {
    MarketState.FLAT: 0.997,  # 思考图（坐问号箱）
    MarketState.RISE: 0.925,   # GIF 牛来欢呼
    MarketState.SURGE: 0.717,  # GIF 双人舞（动作峰值）
    MarketState.FALL: 0.884,   # GIF 拉链变熊（牛形态阶段峰值）
}
MAX_FRAME_SCALE = 1.0 / min(STATE_CONTENT_RATIO.values())  # ≈1.42（surge 最扁）

RED = QColor("#E23B34")     # 中国习惯：红涨
GREEN = QColor("#1E9E4C")   # 绿跌
GRAY = QColor("#8A8F99")

DEMO_VALUES = {
    MarketState.FLAT: 0.02,
    MarketState.RISE: 1.25,
    MarketState.SURGE: 5.80,
    MarketState.FALL: -2.40,
}

# 快捷指数标的（右键菜单）
INDEX_PRESETS = [
    ("上证指数", "sh000001"),
    ("深证成指", "sz399001"),
    ("创业板指", "sz399006"),
    ("沪深300", "sh000300"),
    ("科创50", "sh000688"),
    ("中证500", "sh000905"),
    ("博腾股份", "sz300363"),  # 今日 +20% 涨停的爆拉标的
]


class PetWindow(QWidget):
    quoteReady = Signal(object)  # 后台线程 -> 主线程

    def __init__(self, base_dir: Path, config: dict):
        super().__init__()
        self.base_dir = base_dir
        self.cfg = config
        self.assets = base_dir / "assets"

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | (Qt.WindowType.WindowStaysOnTopHint if config.get("always_on_top", True)
               else Qt.WindowType.WindowType(0))
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # macOS：Tool 窗口在程序失焦时默认自动隐藏（如浏览器打开抢焦点），
        # 必须显式保持常显，否则桌宠会“消失”
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)
        self.setMouseTracking(True)
        self.setWindowTitle("牛来行情桌宠")

        # --- 组件 ---
        self.anim = AnimationController()
        self.bubble = BubbleController()
        self.audio = AudioController(
            self.assets / "audio",
            cooldown_seconds=float(config.get("audio_cooldown_seconds", 120)),
            muted=bool(config.get("muted", False)),
        )
        self.sm = StateMachine(
            rise=float(config["rise_threshold"]),
            surge=float(config["surge_threshold"]),
            fall=float(config["fall_threshold"]),
        )
        self.provider = StockDataProvider(str(base_dir / "quote.json"))

        self.state = MarketState.FLAT
        self.last_quote = None          # 最近一次成功行情
        self.net_error = False
        self.demo_state: MarketState | None = None  # 演示模式（None=实时）
        self.card_visible = False
        self.hovering = False          # 悬停时才变身/显示行情卡
        self._stock_selected = False   # 用户本次会话选过标的才进入行情形态；否则永远思考图
        self._market_view = False      # 行情形态视图（双击关闭，回到普通思考状态）
        self._action_fired_at: dict[str, float] = {}  # 涨跌自动动作冷却
        self._effects_state: MarketState | None = None  # 已播过效果的状态

        self._frames: dict[str, list[QPixmap]] = {}      # 仅当前状态 + FLAT 常驻
        self._frame_paths: dict[str, list[Path]] = {}
        self._aspect: dict[str, float] = {}
        self._scaled_cache: dict[tuple, QPixmap] = {}
        self._scan_frames()  # 普通状态：思考图，无卡片无气泡

        self.char_h = FIXED_CHAR_H  # 固定 200px
        self._drag_start = None
        self._dragging = False
        self._press_pos = None

        # --- 计时器 ---
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._tick)
        self.anim_timer.start(33)

        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.setInterval(350)
        self.hover_timer.timeout.connect(lambda: self._set_card(True))

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(500)
        self.hide_timer.timeout.connect(lambda: self._set_card(False))

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._fetch_quote)
        self._set_refresh_interval()
        self.refresh_timer.start()

        self.quoteReady.connect(self._on_quote)

        # --- 窗口尺寸与位置：每次启动都用默认位置（不记忆上次） ---
        self._apply_char_size(self.char_h, move_to_default=True)
        self._clamp_to_screen()

        QTimer.singleShot(600, self._fetch_quote)

    # ---------------- 素材 ----------------
    def _scan_frames(self):
        """启动时一次性预载全部状态帧（缩放到显示分辨率）。

        之前按需加载会在每次状态切换时从磁盘读 50+ 张 PNG、阻塞主线程，
        导致玩久了音频/动画出得慢。预载后运行时零磁盘 IO。
        帧按固定显示高度缩放缓存，内存占用小（约几十 MB）。"""
        from PySide6.QtGui import QImageReader
        for state, folder in (("FLAT", "idle"), ("RISE", "rise"),
                              ("SURGE", "surge"), ("FALL", "fall")):
            ms = MarketState(state)
            d = self.assets / folder
            paths = sorted(d.glob("frame_*.png")) if d.exists() else []
            if paths:
                reader = QImageReader(str(paths[0]))
                size = reader.size()
                self._aspect[state] = size.width() / size.height() if size.height() else 0.75
            else:
                log.warning("素材缺失: %s（使用占位）", folder)
                self._aspect[state] = 0.75
            self._frame_paths[state] = paths
            # 预载：缩放到该状态的显示高度
            target_h = int(FIXED_CHAR_H / STATE_CONTENT_RATIO[ms])
            frames = []
            for p in paths:
                pm = QPixmap(str(p))
                w = int(pm.width() * target_h / pm.height())
                frames.append(pm.scaled(
                    w, target_h, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))
            if not frames:
                pm = QPixmap(1, 1)
                pm.fill(Qt.GlobalColor.transparent)
                frames.append(pm)
            self._frames[state] = frames
        log.info("素材预载完成: %s",
                 {k: len(v) for k, v in self._frames.items()})

    def _ensure_frames(self, state: MarketState):
        """帧已全部预载，无运行时加载（保留接口兼容）。"""
        return

    def _frame(self, state: MarketState, idx: int = 0) -> QPixmap:
        self._ensure_frames(state)
        frames = self._frames[state.value]
        return frames[min(idx, len(frames) - 1)]

    def _scaled(self, pm: QPixmap, h: int) -> QPixmap:
        if pm.height() == h:  # 已预载到目标尺寸，直接用
            return pm
        key = (pm.cacheKey(), h)
        if key not in self._scaled_cache:
            w = int(pm.width() * h / pm.height())
            self._scaled_cache[key] = pm.scaled(
                w, h, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            if len(self._scaled_cache) > 256:
                self._scaled_cache.pop(next(iter(self._scaled_cache)))
        return self._scaled_cache[key]

    def _frame_h(self, state: MarketState) -> int:
        """某状态帧的显示高度：按内容占比归一，统一角色视觉大小。"""
        return int(self.char_h / STATE_CONTENT_RATIO[state])

    def _char_width_for(self, h: int) -> int:
        """按宽高比计算（不加载像素）。"""
        return max(
            int(self._aspect.get(s.value, 0.75) * h / STATE_CONTENT_RATIO[s])
            for s in MarketState)

    def _max_char_h(self) -> int:
        """当前屏幕可容纳的最大角色高度（帧含留白需放大显示）。"""
        screen = self.screen() or QWidget.screen(self)
        avail = screen.availableGeometry()
        return max(160, int((avail.height() - TOP_MARGIN - BOTTOM_MARGIN)
                            / MAX_FRAME_SCALE))

    # ---------------- 尺寸 / 位置 ----------------
    def _apply_char_size(self, h: int, move_to_default: bool = False):
        h = FIXED_CHAR_H  # 固定 200px，忽略传入值
        old_geo = self.geometry()
        w_needed = max(self._char_width_for(h) + 2 * SIDE_MARGIN, CARD_W + 40)
        h_needed = int(h * MAX_FRAME_SCALE) + TOP_MARGIN + BOTTOM_MARGIN
        if move_to_default:
            screen = self.screen() or QWidget.screen(self)
            avail = screen.availableGeometry()
            x = avail.right() - w_needed - 40
            y = avail.bottom() - h_needed - 20
            self.setGeometry(x, y, w_needed, h_needed)
        else:
            # 保持脚底（底部中心）不动
            foot_gx = old_geo.center().x()
            foot_gy = old_geo.bottom() - BOTTOM_MARGIN
            x = foot_gx - w_needed // 2
            y = foot_gy - h_needed + BOTTOM_MARGIN
            self.setGeometry(x, y, w_needed, h_needed)
        self.char_h = h
        self._mask_key = None  # 尺寸变化后重算点击区域
        self._clamp_to_screen()

    def _clamp_to_screen(self):
        geo = self.geometry()
        screen = self.screen() or QWidget.screen(self)
        avail = screen.availableGeometry()
        x = max(avail.left(), min(geo.x(), avail.right() - geo.width()))
        y = max(avail.top(), min(geo.y(), avail.bottom() - geo.height()))
        if (x, y) != (geo.x(), geo.y()):
            self.move(x, y)

    # ---------------- 行情 ----------------
    def _set_refresh_interval(self):
        secs = self.cfg.get(
            "refresh_seconds_market_open" if is_market_open()
            else "refresh_seconds_market_closed", 15)
        self.refresh_timer.setInterval(int(secs) * 1000)

    def _fetch_quote(self):
        self.provider.get_quote_async(self.cfg["symbol"], self.quoteReady.emit)

    def _on_quote(self, result):
        self._set_refresh_interval()
        if not result.ok:
            self.net_error = True
            log.warning("行情获取失败: %s", result.error)
            self.update()
            return
        self.net_error = False
        self.last_quote = result
        log.info("行情成功 %s %.2f %+.2f%% 源=%s 实时=%s",
                 result.symbol, result.price, result.change_percent,
                 result.source, result.is_realtime)
        if self.demo_state is not None:
            self.update()
            return  # 演示模式：不覆盖展示，仅后台更新
        new_state = self.sm.feed(result.change_percent)
        if new_state is not None and new_state != self.state:
            self._switch_state(new_state)
        self.update()

    def _switch_state(self, state: MarketState, play_audio: bool = True):
        """切换行情状态。副作用（气泡台词/音频/自动开网页）只在被“看到”时触发：
        未选标的或未悬停时静默切换。"""
        self.state = state
        self._ensure_frames(state)  # 按需加载该状态帧序列（释放旧状态）
        self.anim.on_state_changed()
        if self._stock_selected and (self.hovering or self.demo_state is not None):
            self._fire_state_effects(state, play_audio)
        log.info("状态切换 -> %s%s",
                 state.value,
                 "" if self._stock_selected and (self.hovering or self.demo_state)
                 else "（静默，待悬停揭示）")

    def _fire_state_effects(self, state: MarketState, play_audio: bool = True):
        """状态被揭示时触发：气泡短句 + 台词音频 → 音频播完后自动动作。
        平盘/普通状态无任何效果。同一状态只播一次。
        演示模式的爆拉也开抖音（用户要求）。"""
        if state == MarketState.FLAT:
            self._effects_state = state
            self.bubble.clear()  # 普通状态无气泡
            return
        if self._effects_state == state:
            return  # 该状态已播过，不重复
        self._effects_state = state
        self._market_view = True  # 进入行情形态视图（双击才回普通状态）
        self.bubble.show_random(state.value)
        delay = 0.0
        if play_audio and self.audio.play_for_state(state.value):
            delay = self.audio.duration(state.value)  # 等台词说完再开网页
        # 自动动作：真实行情的涨跌 + 演示模式的爆拉（都要开抖音）
        if self.demo_state is None or state == MarketState.SURGE:
            self._auto_action(state, delay)

    def _reveal_if_needed(self):
        """悬停揭示：若状态在未展示期间变过，现在补播效果。"""
        if self.state != self._effects_state:
            self._fire_state_effects(self.state)

    def _auto_action(self, state: MarketState, delay: float = 0.0):
        """涨了打开抖音摸鱼；跌了打开 WPS 开始上班。
        先让台词音频播完（delay 秒），再触发。带冷却防重复。"""
        import time as _time
        kind = None
        if state == MarketState.SURGE:
            kind = "douyin"  # 仅狂涨开抖音；普通上涨只庆祝不开网页
        elif state == MarketState.FALL:
            kind = "work"
        if not kind:
            return
        now = _time.monotonic()
        if now - self._action_fired_at.get(kind, 0.0) < AUTO_ACTION_COOLDOWN:
            return
        self._action_fired_at[kind] = now

        def fire():
            try:
                if kind == "douyin":
                    log.info("行情上涨：打开抖音（不干了）")
                    webbrowser.open(DOUYIN_URL)
                else:
                    log.info("行情下跌：打开 WPS 上班")
                    # 优先 WPS；未安装则退回文本编辑器打开上班记录
                    r = subprocess.run(["open", "-a", "wpsoffice"],
                                       capture_output=True, timeout=10)
                    if r.returncode != 0:
                        WORK_DOC.parent.mkdir(parents=True, exist_ok=True)
                        with open(WORK_DOC, "a", encoding="utf-8") as f:
                            f.write(f"{datetime.now():%Y-%m-%d %H:%M} 熊来打卡。\n")
                        subprocess.Popen(["open", str(WORK_DOC)])
            except Exception as e:  # noqa: BLE001
                log.warning("自动动作失败: %s", e)

        if delay > 0:
            QTimer.singleShot(int(delay * 1000), fire)  # 等音频播完
        else:
            fire()

    def _display_state(self) -> MarketState:
        """当前显示的状态：行情形态视图（悬停揭示后保持，双击关闭）显示行情形态，
        普通状态显示思考图。"""
        if self._market_view or self.demo_state is not None:
            return self.state
        return MarketState.FLAT

    # ---------------- 演示模式 ----------------
    def _enter_demo(self, state: MarketState):
        self.demo_state = state
        self._stock_selected = True  # 演示也算选择，可正常展示
        self._switch_state(state)
        self._set_card(True)
        self.update()

    def _exit_demo(self):
        self.demo_state = None
        if self.last_quote and self.last_quote.ok:
            self.sm.force(MarketState.FLAT)
            self.sm._first = True
            new_state = self.sm.feed(self.last_quote.change_percent)
            if new_state is not None:
                self._switch_state(new_state, play_audio=False)
        self.update()

    def _demo_quote(self):
        base = 3900.0
        if self.last_quote and self.last_quote.ok:
            q = self.last_quote
            base = q.price / (1 + q.change_percent / 100) if q.change_percent != -100 else q.price
        # 演示模式下用最近真实行情的名称，避免显示空代码
        if self.last_quote and self.last_quote.ok and self.last_quote.name:
            name = self.last_quote.name
        else:
            name = self.cfg.get("display_name") or self.cfg["symbol"]
        cp = DEMO_VALUES[self.demo_state]
        price = base * (1 + cp / 100)
        return {
            "name": name,
            "symbol": self.cfg["symbol"],
            "price": price,
            "change": price - base,
            "change_percent": cp,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "模拟数据",
            "is_realtime": False,
            "market_open": is_market_open(),
        }

    # ---------------- 绘制 ----------------
    def _tick(self):
        self._update_mask()
        self.update()

    def _update_mask(self):
        """可点击区域限制为角色/卡片/气泡；透明空隙点穿到桌面。"""
        from PySide6.QtGui import QRegion
        bubble_on = self.bubble.visible_text() is not None
        market_view = self._market_view or self.demo_state is not None
        key = (self.width(), self.height(), self.char_h,
               self.card_visible, bubble_on, market_view)
        if key == getattr(self, "_mask_key", None):
            return
        self._mask_key = key
        foot_y = self.height() - BOTTOM_MARGIN
        cw = self._char_width_for(self.char_h)
        ch_area = int(self.char_h * MAX_FRAME_SCALE)
        r = QRegion(int(self.width() / 2 - cw / 2) - 8,
                    int(foot_y - ch_area) - 8, cw + 16, ch_area + 16)
        if self.card_visible:
            cr = self._card_rect().toRect().adjusted(-8, -8, 8, 8)
            r = r.united(QRegion(cr))
        if bubble_on:  # 行情形态下气泡常驻
            r = r.united(QRegion(int(self.width() / 2 - 160),
                                 int(foot_y - ch_area) - 110, 320, 110))
        self.setMask(r)

    def paintEvent(self, event):
        import time as _time
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        disp = self._display_state()  # 悬停/演示时显示行情形态，平时思考图
        tr = self.anim.current(disp.value)

        foot = QPointF(w / 2, h - BOTTOM_MARGIN)
        # 行情卡先画：红涨绿跌半透明卡垫在人物左侧（仅悬停/演示时显示）
        if self.card_visible:
            q_card = self._demo_quote() if self.demo_state else self._current_quote()
            self._draw_card(p, q_card)

        # 帧序列：RISE/SURGE 循环，FALL 播完定格，FLAT 静态思考图
        self._ensure_frames(disp)
        frames = self._frames[disp.value]
        if len(frames) > 1:
            t = _time.monotonic() - self.anim.state_start
            idx = self.anim.video_frame(disp.value, t, len(frames))
        else:
            idx = 0
        frame = frames[min(idx, len(frames) - 1)]
        # 按内容占比归一缩放：各状态角色视觉大小一致
        pm = self._scaled(frame, self._frame_h(disp))
        cw, ch = pm.width(), pm.height()

        p.save()
        p.translate(foot + QPointF(tr.x_off, tr.y_off))
        p.rotate(tr.rotate)
        p.scale(tr.scale_x, tr.scale_y)
        p.drawPixmap(-cw // 2, -ch, pm)
        p.restore()

        # 气泡（不透明，不挡脸：画在头顶上方）
        text = self.bubble.visible_text()
        if text:
            head_y = foot.y() - ch * tr.scale_y + tr.y_off - 12
            self._draw_bubble(p, QPointF(foot.x(), max(head_y, 60)), text)

    def _current_quote(self):
        if self.last_quote and self.last_quote.ok:
            return {
                "name": self.last_quote.name or self.cfg.get("display_name", ""),
                "symbol": self.last_quote.symbol,
                "price": self.last_quote.price,
                "change": self.last_quote.change,
                "change_percent": self.last_quote.change_percent,
                "timestamp": self.last_quote.timestamp,
                "source": self.last_quote.source,
                "is_realtime": self.last_quote.is_realtime,
                "market_open": self.last_quote.market_open,
            }
        return None

    def _draw_bubble(self, p: QPainter, anchor: QPointF, text: str):
        f = QFont("PingFang SC", 11)
        fm = QFontMetrics(f)
        tw = fm.horizontalAdvance(text)
        # 窄气泡：内边距收紧，文字过长时两行显示
        max_w = 190
        if tw + 16 > max_w:  # 拆两行
            half = len(text) // 2
            for cut in range(half, len(text)):
                if text[cut] in "！，,.… ":
                    break
            lines = [text[:cut], text[cut:]]
            bw = min(max_w, max(fm.horizontalAdvance(l) for l in lines) + 16)
            bh = fm.height() * 2 + 10
        else:
            lines = [text]
            bw = tw + 16
            bh = fm.height() + 8
        rect = QRectF(anchor.x() - bw / 2, anchor.y() - bh - 12, bw, bh)
        rect.translate(0, max(0, 6 - rect.top()))
        path = QPainterPath()
        path.addRoundedRect(rect, 9, 9)
        # 小尾巴
        tail = QPainterPath()
        tail.moveTo(anchor.x() - 6, rect.bottom())
        tail.lineTo(anchor.x() + 6, rect.bottom())
        tail.lineTo(anchor.x(), rect.bottom() + 9)
        tail.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 245))
        p.drawPath(path)
        p.drawPath(tail)
        p.setPen(QColor("#33383F"))
        p.setFont(f)
        if len(lines) > 1:
            p.drawText(QRectF(rect), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                       lines[0] + "\n" + lines[1])
        else:
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def _card_rect(self) -> QRectF:
        """迷你行情卡：人物左侧，垫在人物背后。"""
        disp = self._display_state()
        foot_y = self.height() - BOTTOM_MARGIN
        frame_h = self._frame_h(disp)
        frame_w = int(self._aspect.get(disp.value, 0.75) * frame_h)
        frame_left = self.width() / 2 - frame_w / 2
        # 卡片右缘轻搭角色左肩，主体在左侧
        right = frame_left + int(frame_w * 0.18)
        left = max(4, right - CARD_W)
        top = foot_y - int(self.char_h * MAX_FRAME_SCALE) + int(self.char_h * 0.18)
        top = max(8, min(top, foot_y - CARD_H - 8))
        return QRectF(left, top, CARD_W, CARD_H)

    def _text(self, p: QPainter, pos: QPointF, text: str, font: QFont, color: QColor):
        """透明背景上的文字：深色投影 + 亮色主体，任意壁纸上可读。"""
        p.setFont(font)
        p.setPen(QColor(0, 0, 0, 150))
        p.drawText(QPointF(pos.x() + 1.3, pos.y() + 1.3), text)
        p.setPen(color)
        p.drawText(pos, text)

    def _draw_card(self, p: QPainter, q: dict | None):
        from PySide6.QtGui import QPen
        rect = self._card_rect()
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)

        # 半透明色框：涨（含狂涨）红、跌绿、平盘中性
        up = q is not None and q["change_percent"] > 0
        down = q is not None and q["change_percent"] < 0
        frame_color = RED if up else GREEN if down else QColor(200, 204, 212)
        fill = QColor(frame_color)
        fill.setAlpha(46)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(fill)
        p.drawPath(path)
        border = QColor(frame_color)
        border.setAlpha(210)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(border, 1.5))
        p.drawPath(path)

        lx, ty = rect.left() + 14, rect.top()
        rx = rect.right() - 14
        bright = QColor("#FF7A70") if up else QColor("#3ED98B") if down \
            else QColor("#E6E9EE")

        if q is None:
            self._text(p, QPointF(lx, ty + 30), "行情走丢了",
                       QFont("PingFang SC", 12, QFont.Weight.Bold),
                       QColor(255, 255, 255, 220))
            self._text(p, QPointF(lx, ty + 56), "保留最后数据" if self.last_quote else "重连中……",
                       QFont("PingFang SC", 10), QColor(255, 255, 255, 170))
            if self.last_quote:
                self._text(p, QPointF(lx, ty + 76),
                           f'{self.last_quote.price:.2f}  '
                           f'{self.last_quote.change_percent:+.2f}%',
                           QFont("PingFang SC", 11, QFont.Weight.Bold), bright)
            return

        # 三项数据：指数名称 / 股价 / 涨跌幅（涨红▲ 跌绿▼，三角与数字垂直居中）
        name = q["name"] or self.cfg.get("display_name", q["symbol"])
        self._text(p, QPointF(lx, ty + 26), name,
                   QFont("PingFang SC", 11), QColor(255, 255, 255, 225))
        self._text(p, QPointF(lx, ty + 58), f'{q["price"]:.2f}',
                   QFont("PingFang SC", 18, QFont.Weight.Bold), bright)
        sign = "+" if up else ""
        pf = QFont("PingFang SC", 13, QFont.Weight.Bold)
        pfm = QFontMetrics(pf)
        pct_text = f'{sign}{q["change_percent"]:.2f}%'
        baseline = ty + 58
        # 数字行的视觉垂直中心：基线 - 数字高度的一半（数字高≈ ascent*0.72）
        mid_y = baseline - pfm.capHeight() / 2
        # 先画三角（在数字左侧），三角与文字间距 5px
        tri_right = rx - pfm.horizontalAdvance(pct_text)
        if up or down:
            self._draw_triangle(p, QPointF(tri_right - 5 - 8, mid_y),
                                up=up, color=bright, size=9)
        self._text(p, QPointF(tri_right, baseline), pct_text, pf, bright)

    def _draw_triangle(self, p: QPainter, center: QPointF, up: bool,
                       color: QColor, size: float = 6.5):
        """涨跌三角：涨向上红、跌向下绿。center 为三角几何中心（与数字行对齐）。"""
        from PySide6.QtGui import QPolygonF
        s = size
        if up:
            pts = [QPointF(center.x(), center.y() - s),
                   QPointF(center.x() - s * 0.9, center.y() + s * 0.7),
                   QPointF(center.x() + s * 0.9, center.y() + s * 0.7)]
        else:
            pts = [QPointF(center.x(), center.y() + s),
                   QPointF(center.x() - s * 0.9, center.y() - s * 0.7),
                   QPointF(center.x() + s * 0.9, center.y() - s * 0.7)]
        poly = QPolygonF(pts)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawPolygon(poly)

    def _is_lunch_break(self) -> bool:
        from datetime import time as dtime, datetime as _dt
        now = _dt.now()
        return now.weekday() < 5 and dtime(11, 30) < now.time() < dtime(13, 0)

    # ---------------- 交互 ----------------
    def _set_card(self, v: bool):
        self.card_visible = v
        self.update()

    def enterEvent(self, event):
        self.hovering = True   # 悬停：进入行情形态视图 + 显示红/绿卡
        self.hide_timer.stop()
        self.hover_timer.start()
        if self._stock_selected and self.state != MarketState.FLAT:
            self._market_view = True
        if self._stock_selected:
            self._reveal_if_needed()  # 补播未展示期间的状态效果（音频/气泡/自动动作）
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovering = False  # 移开：行情卡收起，角色保持行情形态（双击才回普通状态）
        self.hover_timer.stop()
        if self.demo_state is None:
            self.hide_timer.start()
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """双击：回到普通状态（思考图，无卡片无气泡）。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._market_view = False
            self.bubble.clear()
            self._set_card(False)
            self.demo_state = None  # 双击也退出演示模式
            self.anim.trigger_click()  # 小动效反馈
            self.update()
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._drag_start = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if not self._dragging and self._press_pos is not None:
                moved = (event.globalPosition().toPoint() - self._press_pos).manhattanLength()
                if moved > 6:
                    self._dragging = True
            if self._dragging:
                self.move(event.globalPosition().toPoint() - self._drag_start)
                self._clamp_to_screen()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._dragging:  # 单击：轮换点击动画；行情形态下换气泡台词
                self.anim.trigger_click()
                if self._display_state() != MarketState.FLAT:
                    self.bubble.show_random(self.state.value)
            self._drag_start = None
            self._dragging = False
            self._press_pos = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        # 大小固定 200px，不支持滚轮调节（避免尺寸反复变化）
        event.ignore()

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        a_refresh = QAction("立即刷新行情", menu)
        a_refresh.triggered.connect(self._fetch_quote)
        menu.addAction(a_refresh)

        symbol_menu = menu.addMenu("更换关注标的")
        for name, sym in INDEX_PRESETS:
            act = QAction(name, symbol_menu)
            act.setCheckable(True)
            act.setChecked(self.cfg["symbol"] == sym)
            act.triggered.connect(
                lambda checked, s=sym, n=name: self._change_symbol(s, n))
            symbol_menu.addAction(act)
        symbol_menu.addSeparator()
        # 爆拉：直接进入狂涨形态（演示），播完台词开抖音
        a_baola = QAction("爆拉！", symbol_menu)
        a_baola.triggered.connect(lambda: self._enter_demo(MarketState.SURGE))
        symbol_menu.addAction(a_baola)
        symbol_menu.addSeparator()
        a_custom = QAction("自定义代码…", symbol_menu)
        a_custom.triggered.connect(lambda: self._change_symbol())
        symbol_menu.addAction(a_custom)

        a_top = QAction("置顶", menu)
        a_top.setCheckable(True)
        a_top.setChecked(bool(self.cfg.get("always_on_top")))
        a_top.triggered.connect(self._toggle_topmost)
        menu.addAction(a_top)

        a_mute = QAction("静音", menu)
        a_mute.setCheckable(True)
        a_mute.setChecked(self.audio.muted)
        a_mute.triggered.connect(self._toggle_mute)
        menu.addAction(a_mute)

        demo_menu = menu.addMenu("演示模式")
        labels = [("平盘", MarketState.FLAT), ("上涨", MarketState.RISE),
                  ("狂涨", MarketState.SURGE), ("下跌", MarketState.FALL)]
        for label, st in labels:
            act = QAction(label, demo_menu)
            act.triggered.connect(lambda checked, s=st: self._enter_demo(s))
            demo_menu.addAction(act)
        demo_menu.addSeparator()
        a_live = QAction("恢复实时行情", demo_menu)
        a_live.triggered.connect(self._exit_demo)
        demo_menu.addAction(a_live)

        menu.addSeparator()
        a_quit = QAction("退出程序", menu)
        a_quit.triggered.connect(self.close)
        menu.addAction(a_quit)

        menu.exec(event.globalPos())

    # ---------------- 菜单动作 ----------------
    def _change_symbol(self, sym: str = "", name: str = ""):
        """更换标的：来自快捷指数菜单（带名称）或自定义输入。"""
        if not sym:
            text, ok = QInputDialog.getText(
                self, "更换关注标的", "输入 6 位代码（如 600519 / 000001）或 sh000001：",
                text=self.cfg["symbol"])
            if not ok:
                return
            sym = validate_symbol(text)
            if not sym:
                QInputDialog.getText(self, "代码无效", "代码格式不正确，请输入 6 位数字。")
                return
            name = ""
        self.cfg["symbol"] = sym
        self.cfg["display_name"] = name
        self.sm = StateMachine(
            rise=float(self.cfg["rise_threshold"]),
            surge=float(self.cfg["surge_threshold"]),
            fall=float(self.cfg["fall_threshold"]))
        self.bubble.clear()
        self.net_error = False
        self._stock_selected = True   # 本次会话用户已主动选择标的
        self._effects_state = None    # 重置效果，新标的揭示时重新播
        self._action_fired_at.clear()
        self._market_view = True
        self._fetch_quote()
        self._set_card(True)  # 换标的后立即展示新行情卡

    def _toggle_topmost(self, checked: bool):
        self.cfg["always_on_top"] = checked
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.show()

    def _toggle_mute(self, checked: bool):
        self.audio.muted = checked
        self.cfg["muted"] = checked

    # ---------------- 生命周期 ----------------
    def persist(self):
        """不做任何持久化：每次启动都是全新初始状态（默认标的、默认位置、有声）。"""
        return

    def closeEvent(self, event):
        self.anim_timer.stop()
        self.refresh_timer.stop()
        self.audio.shutdown()
        self.persist()
        super().closeEvent(event)
