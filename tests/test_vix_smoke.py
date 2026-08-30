"""Offscreen smoke check for the original hover interaction."""
import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF
from PySide6.QtGui import QEnterEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMenu

from app import DEFAULT_CONFIG
from src.pet_window import PetWindow

FIXTURE = Path(__file__).parent / "fixtures" / "vix_history.csv"


class TestOriginalHoverSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_hover_shows_card_without_opening_menu(self):
        window = PetWindow(Path(__file__).parent.parent, DEFAULT_CONFIG.copy())
        window.refresh_timer.stop()
        window.vix_loader = lambda: FIXTURE.read_bytes()
        window.show()
        self.app.processEvents()

        enter = QEnterEvent(QPointF(1, 1), QPointF(1, 1), QPointF(1, 1))
        QApplication.sendEvent(window, enter)
        QTest.qWait(400)

        self.assertTrue(window.card_visible)
        menus = [w for w in QApplication.topLevelWidgets()
                 if isinstance(w, QMenu) and w.isVisible()]
        self.assertEqual(menus, [])
        window.close()


if __name__ == "__main__":
    unittest.main()
