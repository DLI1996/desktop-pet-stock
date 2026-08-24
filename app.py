"""牛来行情桌宠 入口。

用法：
    python app.py                 # 正常启动
    python app.py --state SURGE   # 强制初始状态（测试/拍摄用）
    python app.py --no-audio      # 静音启动（测试用）
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from PySide6.QtNetwork import QLocalServer, QLocalSocket  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from src.pet_window import PetWindow  # noqa: E402
from src.quote_provider import validate_symbol  # noqa: E402
from src.state_machine import MarketState  # noqa: E402

INSTANCE_KEY = "niulai-pet-singleton"

DEFAULT_CONFIG = {
    "symbol": "sh000001",
    "display_name": "上证指数",
    "rise_threshold": 0.1,
    "surge_threshold": 3.0,
    "fall_threshold": -0.1,
    "refresh_seconds_market_open": 15,
    "refresh_seconds_market_closed": 60,
    "audio_cooldown_seconds": 120,
    "character_height": 200,
    "always_on_top": True,
    "muted": False,
    "enable_auto_actions": False,
}


def setup_logging():
    logs = BASE / "logs"
    logs.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(logs / "pet.log", encoding="utf-8"),
        ],
    )


def load_config() -> dict:
    try:
        with open(BASE / "config.json", "r", encoding="utf-8") as f:
            loaded = json.load(f)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()
    if not isinstance(loaded, dict):
        return DEFAULT_CONFIG.copy()
    config = DEFAULT_CONFIG.copy()
    for key, default in DEFAULT_CONFIG.items():
        if type(loaded.get(key, default)) is type(default):
            config[key] = loaded.get(key, default)
    config["symbol"] = validate_symbol(config["symbol"]) or DEFAULT_CONFIG["symbol"]
    if not config["fall_threshold"] < config["rise_threshold"] <= config["surge_threshold"]:
        config.update({key: DEFAULT_CONFIG[key] for key in (
            "rise_threshold", "surge_threshold", "fall_threshold")})
    return config


def already_running() -> bool:
    sock = QLocalSocket()
    sock.connectToServer(INSTANCE_KEY)
    running = sock.waitForConnected(300)
    if running:
        sock.disconnectFromServer()
    return running


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", choices=[s.value for s in MarketState], default=None)
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--screenshot", metavar="PREFIX",
                        help="渲染各状态自截图后退出（测试用）")
    args = parser.parse_args()

    setup_logging()
    log = logging.getLogger("pet.app")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setApplicationName("牛来行情桌宠")

    # 单实例锁：重复启动不出现第二只桌宠
    if already_running():
        log.info("已有实例在运行，退出。")
        return 0
    QLocalServer.removeServer(INSTANCE_KEY)
    server = QLocalServer()
    server.listen(INSTANCE_KEY)

    cfg = load_config()

    win = PetWindow(BASE, cfg)
    if args.no_audio:
        win.audio.muted = True  # 临时静音，不写入配置持久化
    if args.state:
        win._switch_state(MarketState(args.state), play_audio=not args.no_audio)
    win.show()

    if args.screenshot:
        # 测试模式：依次渲染四态 + 演示模式行情卡，自截图后退出
        from PySide6.QtCore import QTimer

        def grab_state(state, demo, path):
            win._switch_state(state, play_audio=False)
            if demo:
                win.demo_state = state
            else:
                win.demo_state = None
            win.card_visible = True
            win.repaint()
            app.processEvents()
            win.grab().save(path)
            print("saved", path)

        seq = []
        out = BASE / "logs"
        for st in MarketState:
            seq.append((st, True, str(out / f"shot_{args.screenshot}_{st.value}.png")))
        seq.append((MarketState.FALL, True, str(out / f"shot_{args.screenshot}_FALL_cry.png")))

        def run(i=0):
            if i >= len(seq):
                app.quit()
                return
            st, demo, path = seq[i]
            grab_state(st, demo, path)
            QTimer.singleShot(300, lambda: run(i + 1))

        QTimer.singleShot(800, run)
        return app.exec()

    log.info("牛来行情桌宠启动：%s", cfg["symbol"])
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
