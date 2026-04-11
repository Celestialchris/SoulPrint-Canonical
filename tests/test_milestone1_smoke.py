"""Milestone 1 smoke tests for app boot and baseline routes."""

import importlib
import unittest


class Milestone1SmokeTest(unittest.TestCase):
    """Validate the verified Milestone 1 baseline without behavior changes."""

    def test_app_imports(self):
        module = importlib.import_module("src.main")
        self.assertTrue(hasattr(module, "main"))

    def test_app_boots_and_has_required_routes(self):
        from src.app import create_app

        app = create_app()
        self.assertIsNotNone(app)

        routes = {rule.rule for rule in app.url_map.iter_rules()}
        self.assertIn("/", routes)
        self.assertIn("/save", routes)
        self.assertIn("/chats", routes)


if __name__ == "__main__":
    unittest.main()
