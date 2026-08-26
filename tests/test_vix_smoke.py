"""Offscreen smoke check for the single VIX desktop interaction."""
import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMenu

from app import DEFAULT_CONFIG
from src.pet_window import PetWindow


FIXTURE = Path(__file__).parent / "fixtures" / "vix_history.csv"


class TestVixDesktopSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_hover_menu_opens_vix_detail_with_loading_success_and_failure(self):
        window = PetWindow(Path(__file__).parent.parent, DEFAULT_CONFIG.copy())
        window.refresh_timer.stop()
        window.show()
        self.app.processEvents()
        window.vix_loader = lambda: FIXTURE.read_bytes()

        enter = QEnterEvent(QPointF(1, 1), QPointF(1, 1), QPointF(1, 1))
        QApplication.sendEvent(window, enter)
        QTest.qWait(400)

        menus = [w for w in QApplication.topLevelWidgets()
                 if isinstance(w, QMenu) and w.isVisible()]
        self.assertEqual(len(menus), 1)
        self.assertEqual([a.text() for a in menus[0].actions()], ["VIX"])

        action = menus[0].actions()[0]
        QTest.mouseClick(menus[0], Qt.MouseButton.LeftButton,
                         pos=menus[0].actionGeometry(action).center())
        detail = window.vix_detail
        self.assertEqual(detail.status, "loading")
        self.assertTrue(detail._load_done.wait(1))
        self.app.processEvents()
        self.assertEqual(detail.status, "ready")
        self.assertEqual(detail.latest_value, 15.42)
        self.assertEqual(detail.observation_date, "2026-08-25")
        self.assertIn("Cboe", detail.source)
        self.assertGreater(len(detail.points), 1)

        detail.loader = lambda: (_ for _ in ()).throw(OSError("offline"))
        detail.load()
        self.assertTrue(detail._load_done.wait(1))
        self.app.processEvents()
        self.assertEqual(detail.status, "failure")
        window.close()


if __name__ == "__main__":
    unittest.main()
