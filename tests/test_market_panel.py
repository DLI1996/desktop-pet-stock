"""Deterministic offscreen checks for the US/VIX market panel."""
import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QEnterEvent, QMouseEvent
from PySide6.QtWidgets import QApplication

from app import DEFAULT_CONFIG
from src.pet_window import PetWindow
from src.state_machine import MarketState
from src.vix_view import VixDetailView


FIXTURE = Path(__file__).parent / "fixtures" / "vix_history.csv"


class TestMarketPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_hover_opens_us_list_and_vix_detail_in_same_panel(self):
        window = PetWindow(Path(__file__).parent.parent, DEFAULT_CONFIG.copy())
        window.refresh_timer.stop()
        window.vix_loader = lambda: FIXTURE.read_bytes()
        window.show()
        self.app.processEvents()

        QApplication.sendEvent(window, QEnterEvent(QPointF(1, 1), QPointF(1, 1),
                                                   QPointF(1, 1)))
        self.assertTrue(window.hover_timer.isActive())
        self.assertEqual(window.hover_timer.interval(), 350)
        window.hover_timer.timeout.emit()
        self.assertTrue(window.market_panel.isVisible())
        self.assertEqual(window.market_panel.market_view, "US")
        self.assertEqual(window.market_panel.rows, ["VIX"])
        self.assertIsNone(window.market_panel.detail)

        self.assertTrue(window.market_panel._summary_done.wait(1))
        self.app.processEvents()
        self.assertEqual(window.market_panel.list_status, "ready")
        original_state = window.state
        window.market_panel.open_vix_detail()
        self.assertIsNotNone(window.market_panel.detail)
        self.assertEqual(window.market_panel.detail.status, "loading")
        self.assertTrue(window.market_panel.detail._load_done.wait(1))
        self.app.processEvents()
        detail = window.market_panel.detail
        self.assertEqual(detail.status, "ready")
        self.assertEqual(detail.latest_value, 15.42)
        self.assertEqual(detail.latest_change, 0.37)
        self.assertEqual(detail.latest_open, 15.0)
        self.assertEqual(detail.latest_high, 15.7)
        self.assertEqual(detail.latest_low, 14.9)
        self.assertEqual(detail.previous_close, 15.05)
        self.assertIn("Cboe", detail.source)
        self.assertEqual(window.state, original_state)
        self.assertIsNone(window.last_quote)

        window.market_panel.back_to_list()
        self.assertEqual(window.market_panel.content_view, "list")
        self.assertEqual(window.market_panel.active_row, "VIX")
        window.close()

    def test_panel_stays_hidden_until_hover_intent(self):
        window = PetWindow(Path(__file__).parent.parent, DEFAULT_CONFIG.copy())
        window.refresh_timer.stop()
        window.show()
        self.app.processEvents()

        self.assertFalse(window.market_panel.isVisible())
        QApplication.sendEvent(window, QEnterEvent(QPointF(1, 1), QPointF(1, 1),
                                                   QPointF(1, 1)))
        self.assertFalse(window.market_panel.isVisible())
        window.hover_timer.timeout.emit()
        self.assertTrue(window.market_panel.isVisible())
        window.close()

    def test_demo_mode_still_closes_panel_after_leaving(self):
        window = PetWindow(Path(__file__).parent.parent, DEFAULT_CONFIG.copy())
        window.refresh_timer.stop()
        window._enter_demo(MarketState.SURGE)
        window.leaveEvent(QEvent(QEvent.Type.Leave))

        self.assertTrue(window.hide_timer.isActive())
        self.assertEqual(window.hide_timer.interval(), 200)
        window.close()

    def test_tooltip_requires_nearby_rendered_point_and_uses_delays(self):
        detail = VixDetailView(lambda: FIXTURE.read_bytes())
        self.assertTrue(detail._load_done.wait(1))
        self.app.processEvents()
        detail.resize(360, 308)
        point = detail._point_positions()[0]
        event = QMouseEvent(QEvent.Type.MouseMove, point, Qt.MouseButton.NoButton,
                            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
        detail.mouseMoveEvent(event)
        self.assertTrue(detail._hover_timer.isActive())
        self.assertEqual(detail._hover_timer.interval(), 350)

        far = QPointF(point.x(), detail._chart_rect().center().y())
        event = QMouseEvent(QEvent.Type.MouseMove, far, Qt.MouseButton.NoButton,
                            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
        detail.mouseMoveEvent(event)
        self.assertFalse(detail._hover_timer.isActive())
        self.assertTrue(detail._tooltip_hide_timer.isActive())
        self.assertEqual(detail._tooltip_hide_timer.interval(), 200)
        detail.close()


if __name__ == "__main__":
    unittest.main()
