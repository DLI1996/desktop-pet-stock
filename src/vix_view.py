"""Cboe VIX daily-history detail content for the market panel."""
from __future__ import annotations

import threading
from typing import Callable

from PySide6.QtCore import QEvent, QPointF, QRectF, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QEnterEvent, QFont, QMouseEvent, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from .vix_provider import VIX_SOURCE, VixSummary, fetch_vix_csv, parse_vix_csv, parse_vix_summary


class VixDetailView(QWidget):
    """Load and paint VIX detail only after the row is activated."""

    loaded = Signal(object)
    entered = Signal()

    def __init__(self, loader: Callable[[], bytes] = fetch_vix_csv,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.loader = loader
        self.status = "loading"
        self.points: list[tuple[str, float]] = []
        self.summary: VixSummary | None = None
        self.latest_value: float | None = None
        self.latest_change = 0.0
        self.latest_open = 0.0
        self.latest_high = 0.0
        self.latest_low = 0.0
        self.previous_close = 0.0
        self.observation_date = ""
        self.source = VIX_SOURCE
        self.error = ""
        self.tooltip_text = ""
        self.tooltip_visible = False
        self._hover_index: int | None = None
        self._load_done = threading.Event()
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(350)
        self._hover_timer.timeout.connect(self._show_hover_tooltip)
        self._tooltip_hide_timer = QTimer(self)
        self._tooltip_hide_timer.setSingleShot(True)
        self._tooltip_hide_timer.setInterval(200)
        self._tooltip_hide_timer.timeout.connect(self._hide_tooltip)
        self.setMinimumSize(300, 280)
        self.setMouseTracking(True)
        self.loaded.connect(self._on_loaded)
        self.load()

    def load(self) -> None:
        self.status = "loading"
        self.error = ""
        self._load_done.clear()
        self.update()

        def run() -> None:
            try:
                raw = self.loader()
                result = ("ready", (parse_vix_csv(raw), parse_vix_summary(raw)))
            except Exception as error:  # noqa: BLE001
                result = ("failure", str(error))
            try:
                self.loaded.emit(result)
            except RuntimeError:
                pass  # Detail view closed while the request was in flight.
            finally:
                self._load_done.set()

        threading.Thread(target=run, daemon=True).start()

    def _on_loaded(self, result: tuple[str, object]) -> None:
        self.status = result[0]
        if self.status == "ready":
            self.points, self.summary = result[1]
            self.observation_date = self.summary.date
            self.latest_value = self.summary.value
            self.latest_change = self.summary.change
            self.latest_open = self.summary.open
            self.latest_high = self.summary.high
            self.latest_low = self.summary.low
            self.previous_close = self.summary.previous_close
        else:
            self.error = str(result[1])
        self.update()

    def _chart_rect(self) -> QRectF:
        return QRectF(16, 172, self.width() - 32, self.height() - 190)

    def _point_positions(self) -> list[QPointF]:
        chart = self._chart_rect()
        values = [value for _, value in self.points]
        low, high = min(values), max(values)
        span = high - low or 1.0
        return [
            QPointF(chart.left() + i * chart.width() / max(1, len(values) - 1),
                    chart.bottom() - (value - low) * chart.height() / span)
            for i, value in enumerate(values)
        ]

    def _index_at(self, pos: QPointF) -> int | None:
        if not self._chart_rect().contains(pos) or len(self.points) < 2:
            return None
        index, point = min(enumerate(self._point_positions()),
                           key=lambda item: (item[1] - pos).manhattanLength())
        return index if (point - pos).manhattanLength() <= 10 else None

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        index = self._index_at(event.position()) if self.status == "ready" else None
        self._tooltip_hide_timer.stop()
        if index is None:
            self._hover_timer.stop()
            self._hover_index = None
            self._tooltip_hide_timer.start()
        elif index != self._hover_index:
            self._hover_index = index
            self.tooltip_visible = False
            self._hover_timer.start()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._hover_timer.stop()
        self._hover_index = None
        self._tooltip_hide_timer.start()
        super().leaveEvent(event)

    def enterEvent(self, event: QEnterEvent) -> None:
        self.entered.emit()
        super().enterEvent(event)

    def _show_hover_tooltip(self) -> None:
        if self._hover_index is not None and self.status == "ready":
            date, value = self.points[self._hover_index]
            self.tooltip_text = f"{date}  {value:.2f}"
            self.tooltip_visible = True
            self.update()

    def _hide_tooltip(self) -> None:
        self.tooltip_visible = False
        self.tooltip_text = ""
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#141820"))
        painter.setPen(QColor("#F1F3F5"))
        painter.setFont(QFont("PingFang SC", 16, QFont.Weight.Bold))
        painter.drawText(16, 28, "VIX")

        if self.status == "loading":
            self._draw_message(painter, "正在加载 Cboe VIX 日线…")
            return
        if self.status == "failure":
            self._draw_message(painter, "VIX 数据加载失败")
            painter.setPen(QColor("#9AA2AF"))
            painter.drawText(QRectF(16, 70, self.width() - 32, 70),
                             Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                             self.error)
            return

        summary = self.summary
        painter.setFont(QFont("PingFang SC", 20, QFont.Weight.Bold))
        painter.setPen(QColor("#FFB454"))
        painter.drawText(16, 62, f"{summary.value:.2f}")
        painter.setFont(QFont("PingFang SC", 10))
        painter.setPen(QColor("#AAB2BF"))
        painter.drawText(92, 50, f"变化 {summary.change:+.2f}")
        painter.drawText(92, 67, f"日期 {summary.date}")
        painter.drawText(16, 89, f"开 {summary.open:.2f}  高 {summary.high:.2f} 低 {summary.low:.2f}")
        painter.drawText(16, 106, f"前收 {summary.previous_close:.2f}   来源 {summary.source}")

        chart = self._chart_rect()
        path = QPainterPath()
        path.addRoundedRect(chart, 8, 8)
        painter.fillPath(path, QColor("#1D2330"))
        values = [value for _, value in self.points]
        polyline = QPolygonF(self._point_positions())
        painter.setPen(QPen(QColor("#FFB454"), 2))
        painter.drawPolyline(polyline)
        if self.tooltip_visible and self._hover_index is not None:
            i = self._hover_index
            point = polyline[i]
            painter.setPen(QPen(QColor("#F1F3F5"), 1))
            painter.drawLine(QPointF(point.x(), chart.top()),
                             QPointF(point.x(), chart.bottom()))
            painter.setBrush(QColor("#F1F3F5"))
            painter.drawEllipse(point, 3, 3)
            painter.setPen(QColor("#F1F3F5"))
            painter.drawText(QRectF(max(chart.left(), point.x() - 70), chart.top() + 4,
                                    140, 20), Qt.AlignmentFlag.AlignCenter,
                             self.tooltip_text)
        painter.setPen(QColor("#788191"))
        painter.drawText(16, self.height() - 6,
                         f"最近 {len(values)} 个交易日收盘")

    def _draw_message(self, painter: QPainter, text: str) -> None:
        painter.setFont(QFont("PingFang SC", 12))
        painter.setPen(QColor("#C7CDD6"))
        painter.drawText(16, 64, text)
