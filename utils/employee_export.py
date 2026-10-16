"""Utilities for exporting employee records to CSV."""

import csv
from pathlib import Path
from typing import Iterable, Sequence


def export_employee_rows(
    file_path: str | Path,
    headers: Sequence[str],
    rows: Iterable[Sequence[object]],
) -> int:
    """Write employee records to a spreadsheet-friendly UTF-8 CSV.

    Returns the number of exported records.
    """
    with open(
        file_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)

        count = 0
        for row in rows:
            writer.writerow(row)
            count += 1

    return count
