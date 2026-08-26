"""Cboe VIX daily-history detail view."""
from __future__ import annotations

import threading
from typing import Callable

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from .vix_provider import VIX_SOURCE, fetch_vix_csv, parse_vix_csv


class VixDetailView(QWidget):
    loaded = Signal(object)

    def __init__(self, loader: Callable[[], bytes] = fetch_vix_csv,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.Tool)
        self.loader = loader
        self.status = "loading"
        self.points: list[tuple[str, float]] = []
        self.latest_value: float | None = None
        self.observation_date = ""
        self.source = VIX_SOURCE
        self.error = ""
        self._load_done = threading.Event()
        self.setWindowTitle("VIX 详情")
        self.setMinimumSize(540, 320)
        self.loaded.connect(self._on_loaded)
        self.load()

    def load(self) -> None:
        self.status = "loading"
        self.error = ""
        self._load_done.clear()
        self.update()

        def run() -> None:
            try:
                result = ("ready", parse_vix_csv(self.loader()))
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
            self.points = result[1]
            self.observation_date, self.latest_value = self.points[-1]
        else:
            self.error = str(result[1])
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#141820"))
        painter.setPen(QColor("#F1F3F5"))
        painter.setFont(QFont("PingFang SC", 18, QFont.Weight.Bold))
        painter.drawText(24, 38, "VIX")

        if self.status == "loading":
            self._draw_message(painter, "正在加载 Cboe VIX 日线…")
            return
        if self.status == "failure":
            self._draw_message(painter, "VIX 数据加载失败")
            painter.setPen(QColor("#9AA2AF"))
            painter.drawText(QRectF(24, 88, self.width() - 48, 50),
                             Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                             self.error)
            return

        painter.setFont(QFont("PingFang SC", 22, QFont.Weight.Bold))
        painter.setPen(QColor("#FFB454"))
        painter.drawText(24, 76, f"{self.latest_value:.2f}")
        painter.setFont(QFont("PingFang SC", 10))
        painter.setPen(QColor("#AAB2BF"))
        painter.drawText(120, 70, f"观测日期  {self.observation_date}")
        painter.drawText(120, 88, f"数据来源  {self.source}")

        chart = QRectF(24, 112, self.width() - 48, self.height() - 144)
        path = QPainterPath()
        path.addRoundedRect(chart, 8, 8)
        painter.fillPath(path, QColor("#1D2330"))
        values = [value for _, value in self.points]
        low, high = min(values), max(values)
        span = high - low or 1.0
        polyline = QPolygonF([
            QPointF(chart.left() + i * chart.width() / max(1, len(values) - 1),
                    chart.bottom() - (value - low) * chart.height() / span)
            for i, value in enumerate(values)
        ])
        painter.setPen(QPen(QColor("#FFB454"), 2))
        painter.drawPolyline(polyline)
        painter.setPen(QColor("#788191"))
        painter.drawText(24, self.height() - 10,
                         f"最近 {len(values)} 个交易日收盘")

    def _draw_message(self, painter: QPainter, text: str) -> None:
        painter.setFont(QFont("PingFang SC", 13))
        painter.setPen(QColor("#C7CDD6"))
        painter.drawText(24, 82, text)
