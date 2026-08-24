"""Safety policy tests for desktop side effects."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.pet_window import PetWindow
from src.state_machine import MarketState


class TestAutoActions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_disabled_by_default(self):
        window = PetWindow.__new__(PetWindow)
        window.cfg = {}
        window._action_fired_at = {}

        with patch("src.pet_window.webbrowser.open") as browser_open:
            window._auto_action(MarketState.SURGE)

        browser_open.assert_not_called()

    def test_explicit_opt_in_enables_action(self):
        window = PetWindow.__new__(PetWindow)
        window.cfg = {"enable_auto_actions": True}
        window._action_fired_at = {}

        with patch("src.pet_window.webbrowser.open") as browser_open:
            window._auto_action(MarketState.SURGE)

        browser_open.assert_called_once()


if __name__ == "__main__":
    unittest.main()
