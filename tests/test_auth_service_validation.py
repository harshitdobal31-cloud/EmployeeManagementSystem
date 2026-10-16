import unittest
from unittest.mock import patch

from services.auth_service import login_user


class TestLoginInputValidation(unittest.TestCase):

    def test_empty_username_is_rejected(self):
        with patch("services.auth_service.SessionLocal") as session_factory:
            self.assertIsNone(login_user("", "ValidPassword123"))
            session_factory.assert_not_called()

    def test_whitespace_username_is_rejected(self):
        with patch("services.auth_service.SessionLocal") as session_factory:
            self.assertIsNone(login_user("   ", "ValidPassword123"))
            session_factory.assert_not_called()

    def test_empty_password_is_rejected(self):
        with patch("services.auth_service.SessionLocal") as session_factory:
            self.assertIsNone(login_user("admin", ""))
            session_factory.assert_not_called()

    def test_none_username_is_rejected(self):
        with patch("services.auth_service.SessionLocal") as session_factory:
            self.assertIsNone(login_user(None, "ValidPassword123"))
            session_factory.assert_not_called()

    def test_none_password_is_rejected(self):
        with patch("services.auth_service.SessionLocal") as session_factory:
            self.assertIsNone(login_user("admin", None))
            session_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
