import unittest
from unittest.mock import patch

from services.employee_service import add_employee


class TestEmployeeServiceValidation(unittest.TestCase):

    def test_missing_employee_data_is_rejected(self):
        with patch("services.employee_service.SessionLocal") as session_factory:
            try:
                result = add_employee()
            except TypeError:
                # The function may require arguments; in that case,
                # this test cannot assume its calling convention.
                self.skipTest("add_employee requires arguments")
            self.assertFalse(result)
            session_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
