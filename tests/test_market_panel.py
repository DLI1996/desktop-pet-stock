"""Deterministic offscreen checks for the US/VIX market panel."""
import os
import threading
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QApplication

from app import DEFAULT_CONFIG
from src.pet_window import PetWindow


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
        self.assertEqual(window.market_panel.screen, "list")
        self.assertEqual(window.market_panel.active_row, "VIX")
        window.close()


if __name__ == "__main__":
    unittest.main()
