from pathlib import Path
import csv
import tempfile
import unittest

from utils.employee_export import export_employee_rows


class EmployeeExportTests(unittest.TestCase):
    def test_exports_headers_and_employee_records(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "employees.csv"
            count = export_employee_rows(
                output,
                ["Employee ID", "Full Name", "Department"],
                [
                    ["EMP001", "Harshit Dobal", "IT"],
                    ["EMP002", "Amit Sharma", "Finance"],
                ],
            )

            self.assertEqual(count, 2)

            with output.open(
                "r", newline="", encoding="utf-8-sig"
            ) as file:
                records = list(csv.reader(file))

            self.assertEqual(
                records,
                [
                    ["Employee ID", "Full Name", "Department"],
                    ["EMP001", "Harshit Dobal", "IT"],
                    ["EMP002", "Amit Sharma", "Finance"],
                ],
            )

    def test_exports_unicode_names_correctly(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "employees.csv"
            export_employee_rows(
                output,
                ["Full Name"],
                [["Harshit Dobal"], ["José García"]],
            )

            with output.open(
                "r", newline="", encoding="utf-8-sig"
            ) as file:
                records = list(csv.reader(file))

            self.assertEqual(records[2], ["José García"])

    def test_exports_headers_when_no_employee_rows_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "empty.csv"
            count = export_employee_rows(output, ["Employee ID"], [])

            self.assertEqual(count, 0)

            with output.open(
                "r", newline="", encoding="utf-8-sig"
            ) as file:
                self.assertEqual(list(csv.reader(file)), [["Employee ID"]])


if __name__ == "__main__":
    unittest.main()
