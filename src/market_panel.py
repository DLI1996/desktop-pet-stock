"""Compact in-window market list and lazy detail panel."""
from __future__ import annotations

import math
import threading
from typing import Callable

from PySide6.QtCore import QEvent, QRectF, Signal, Qt
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget

from .quote_provider import QuoteResult
from .vix_provider import VixSummary, fetch_vix_csv, parse_vix_summary
from .vix_view import VixDetailView


INDEX_PRESETS = [
    ("上证指数", "sh000001"),
    ("深证成指", "sz399001"),
    ("创业板指", "sz399006"),
    ("沪深300", "sh000300"),
    ("科创50", "sh000688"),
    ("中证500", "sh000905"),
    ("博腾股份", "sz300363"),
]


class MarketPanel(QWidget):
    """A single China/US list/detail surface shown beside the pet."""

    entered = Signal()
    left = Signal()
    symbol_selected = Signal(str, str)

    def __init__(self, loader: Callable[[], bytes] = fetch_vix_csv,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.loader = loader
        self.market_view = "US"
        self.content_view = "list"
        self.rows = ["VIX"]
        self.china_rows = INDEX_PRESETS
        self.active_row: str | None = None
        self.list_status = "loading"
        self.error = ""
        self.summary: VixSummary | None = None
        self.detail: VixDetailView | None = None
        self.china_quote: QuoteResult | None = None
        self.china_error = ""
        self._raw: bytes | None = None
        self._summary_done = threading.Event()
        self.summary_ready.connect(self._summary_result_ready)
        self.setFixedSize(360, 350)
        self.setMouseTracking(True)

    def open(self) -> None:
        self.content_view = "list"
        if self.detail:
            self.detail.hide()
        self.show()
        if self.summary is None and not self._summary_done.is_set():
            self._load_summary()
        self.update()

    def _load_summary(self) -> None:
        self.list_status = "loading"
        self._summary_done.clear()

        def run() -> None:
            try:
                raw = self.loader()
                result = ("ready", (raw, parse_vix_summary(raw)))
            except Exception as error:  # noqa: BLE001
                result = ("failure", str(error))
            self.summary_ready.emit(result)
            self._summary_done.set()

        threading.Thread(target=run, daemon=True).start()

    summary_ready = Signal(object)

    def _summary_result_ready(self, result: tuple[str, object]) -> None:
        self.list_status = result[0]
        if self.list_status == "ready":
            self._raw, self.summary = result[1]
        else:
            self.error = str(result[1])
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#161A22"))
        if self.content_view != "detail":
            painter.setPen(QColor("#F4F5F7"))
            painter.setFont(QFont("PingFang SC", 14, QFont.Weight.Bold))
            painter.drawText(18, 28, "Market")
        painter.setFont(QFont("PingFang SC", 10, QFont.Weight.Bold))
        painter.setPen(QColor("#FFB454" if self.market_view == "CN" else "#8F98A8"))
        painter.drawText(180, 27, "中国")
        painter.setPen(QColor("#FFB454" if self.market_view == "US" else "#8F98A8"))
        painter.drawText(236, 27, "美国")
        if self.content_view == "detail":
            self._paint_detail_header(painter)
            if self.market_view == "CN":
                self._paint_china_detail(painter)
            return

        painter.setFont(QFont("PingFang SC", 10))
        painter.setPen(QColor("#8F98A8"))
        painter.drawText(18, 50, "中国市场" if self.market_view == "CN" else "美国市场")
        if self.market_view == "CN":
            for index, (name, _) in enumerate(self.china_rows):
                y = 64 + index * 36
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor("#2C3442" if self.active_row == name else "#202631"))
                painter.drawRoundedRect(QRectF(12, y, 336, 32), 7, 7)
                painter.setPen(QColor("#F4F5F7"))
                painter.setFont(QFont("PingFang SC", 11))
                painter.drawText(28, y + 21, name)
            painter.setPen(QColor("#697384"))
            painter.drawText(18, 322, "＋ 添加指标")
            return
        if self.list_status == "loading":
            for y in (78, 104):
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor("#2B313D"))
                painter.drawRoundedRect(QRectF(18, y, 324, 18), 5, 5)
        elif self.list_status == "failure":
            painter.setPen(QColor("#D27C78"))
            painter.drawText(18, 92, "VIX 摘要暂不可用")
            painter.setPen(QColor("#8F98A8"))
            painter.drawText(QRectF(18, 104, 324, 50),
                             Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                             self.error)
        else:
            active = self.active_row == "VIX"
            row = QRectF(12, 64, 336, 58)
            path = QPainterPath()
            path.addRoundedRect(row, 9, 9)
            painter.fillPath(path, QColor("#2C3442" if active else "#202631"))
            painter.setPen(QColor("#F4F5F7"))
            painter.setFont(QFont("PingFang SC", 12, QFont.Weight.Bold))
            painter.drawText(28, 99, "VIX")
            painter.setPen(QColor("#FFB454"))
            painter.drawText(262, 99, f"{self.summary.value:.2f}")
            painter.setFont(QFont("PingFang SC", 9))
            painter.setPen(QColor("#9BA4B2"))
            painter.drawText(28, 114, self.summary.date)
        painter.setPen(QColor("#697384"))
        painter.setFont(QFont("PingFang SC", 10))
        painter.drawText(18, 322, "＋ 添加指标")

    def _paint_detail_header(self, painter: QPainter) -> None:
        painter.setPen(QColor("#F4F5F7"))
        painter.setFont(QFont("PingFang SC", 11, QFont.Weight.Bold))
        painter.drawText(18, 29, "‹ 返回")

    def _paint_china_detail(self, painter: QPainter) -> None:
        painter.setPen(QColor("#F4F5F7"))
        painter.setFont(QFont("PingFang SC", 16, QFont.Weight.Bold))
        painter.drawText(18, 78, self.active_row or "中国行情")
        if self.china_quote:
            quote = self.china_quote
            painter.setFont(QFont("PingFang SC", 20, QFont.Weight.Bold))
            painter.drawText(18, 118, f"{quote.price:.2f}")
            painter.setPen(QColor("#E23B34" if quote.change >= 0 else "#1E9E4C"))
            painter.setFont(QFont("PingFang SC", 11, QFont.Weight.Bold))
            painter.drawText(18, 148,
                             f"{quote.change:+.2f}  {quote.change_percent:+.2f}%")
            painter.setPen(QColor("#9BA4B2"))
            painter.setFont(QFont("PingFang SC", 9))
            try:
                ohlc = tuple(float(quote.raw[key])
                             for key in ("open", "high", "low"))
            except (KeyError, TypeError, ValueError):
                ohlc = ()
            if ohlc and all(math.isfinite(value) and value > 0 for value in ohlc):
                open_, high, low = ohlc
                previous_close = quote.price - quote.change
                painter.drawText(18, 178, f"开 {open_:.2f}  高 {high:.2f}")
                painter.drawText(18, 200,
                                 f"低 {low:.2f}  昨收 {previous_close:.2f}")
            else:
                painter.drawText(18, 178, "OHLC 暂不可用")
            painter.drawText(18, 226, quote.timestamp)
            painter.drawText(18, 246, quote.source)
        elif self.china_error:
            painter.setPen(QColor("#D27C78"))
            painter.setFont(QFont("PingFang SC", 10, QFont.Weight.Bold))
            painter.drawText(18, 108, "行情暂不可用")
            painter.setPen(QColor("#8F98A8"))
            painter.drawText(QRectF(18, 120, 324, 52),
                             Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                             self.china_error)
        else:
            painter.setPen(QColor("#9BA4B2"))
            painter.setFont(QFont("PingFang SC", 10))
            painter.drawText(18, 108, "行情刷新中…")
        painter.setPen(QColor("#697384"))
        painter.setFont(QFont("PingFang SC", 10))
        painter.drawText(18, 280, "历史数据暂不可用")

    def set_china_quote(self, result: QuoteResult) -> None:
        """Accept the active China row's quote and ignore stale requests."""
        expected = next((symbol for name, symbol in self.china_rows
                         if name == self.active_row), None)
        if result.symbol != expected:
            return
        self.china_quote = result if result.ok else None
        self.china_error = "" if result.ok else (result.error or "接口返回空数据")
        self.update()

    def _set_market_view(self, market_view: str) -> None:
        self.market_view = market_view
        self.content_view = "list"
        self.active_row = None
        self.china_quote = None
        self.china_error = ""
        if self.detail:
            self.detail.hide()
        if market_view == "CN":
            self.rows = [name for name, _ in self.china_rows]
            self.list_status = "ready"
        else:
            self.rows = ["VIX"]
            self.list_status = "loading" if self.summary is None else "ready"
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = event.position()
        if QRectF(156, 8, 72, 32).contains(pos):
            self._set_market_view("CN")
            return
        if QRectF(228, 8, 72, 32).contains(pos):
            self._set_market_view("US")
            return
        if self.content_view == "detail":
            if pos.y() < 45:
                self.back_to_list()
            return
        if self.market_view == "CN":
            for index, (name, symbol) in enumerate(self.china_rows):
                row = QRectF(12, 64 + index * 36, 336, 32)
                if row.contains(pos):
                    self.active_row = name
                    self.content_view = "detail"
                    self.china_quote = None
                    self.china_error = ""
                    self.symbol_selected.emit(symbol, name)
                    self.update()
                    return
            return
        if self.list_status == "ready" and QRectF(12, 64, 336, 58).contains(pos):
            self.open_vix_detail()
        super().mousePressEvent(event)

    def open_vix_detail(self) -> None:
        self.active_row = "VIX"
        self.content_view = "detail"
        if self.detail is None:
            loader = (lambda: self._raw) if self._raw is not None else self.loader
            self.detail = VixDetailView(loader, self)
            self.detail.setGeometry(0, 42, self.width(), self.height() - 42)
            self.detail.entered.connect(self.entered)
        else:
            self.detail.show()
            if self.detail.status == "failure":
                self.detail.load()
        self.detail.show()
        self.update()

    def back_to_list(self) -> None:
        self.content_view = "list"
        if self.detail:
            self.detail.hide()
        self.update()

    def enterEvent(self, event: QEvent) -> None:
        self.entered.emit()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.left.emit()
        super().leaveEvent(event)
