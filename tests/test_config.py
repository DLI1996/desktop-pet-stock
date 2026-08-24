"""User configuration safety tests."""
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

import app


class TestConfig(unittest.TestCase):
    def test_malformed_json_uses_safe_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text("{not json", encoding="utf-8")
            with patch.object(app, "BASE", Path(directory)):
                config = app.load_config()

        self.assertEqual(config["symbol"], "sh000001")
        self.assertFalse(config["enable_auto_actions"])

    def test_invalid_values_fall_back_per_field(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(json.dumps({
                "symbol": "not-a-symbol", "rise_threshold": "high",
                "always_on_top": "yes", "enable_auto_actions": True,
            }), encoding="utf-8")
            with patch.object(app, "BASE", Path(directory)):
                config = app.load_config()

        self.assertEqual(config["symbol"], "sh000001")
        self.assertEqual(config["rise_threshold"], 0.1)
        self.assertTrue(config["always_on_top"])
        self.assertTrue(config["enable_auto_actions"])


if __name__ == "__main__":
    unittest.main()
