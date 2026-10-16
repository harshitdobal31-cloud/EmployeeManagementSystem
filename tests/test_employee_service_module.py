import importlib
import unittest
from unittest.mock import patch


class TestEmployeeServiceModule(unittest.TestCase):
    def test_employee_service_module_imports(self):
        """Ensure the employee service module can be imported."""
        module = importlib.import_module("services.employee_service")
        self.assertIsNotNone(module)

    def test_add_employee_function_exists(self):
        """Ensure the service exposes the function used by the UI."""
        module = importlib.import_module("services.employee_service")
        self.assertTrue(
            callable(getattr(module, "add_employee", None)),
            "services.employee_service must define add_employee()",
        )


if __name__ == "__main__":
    unittest.main()
