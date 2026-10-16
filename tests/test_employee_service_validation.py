import unittest

from services.employee_service import add_employee


class TestEmployeeServiceValidation(unittest.TestCase):

    def test_add_employee_requires_arguments(self):
        with self.assertRaises(TypeError):
            add_employee()


if __name__ == "__main__":
    unittest.main()
