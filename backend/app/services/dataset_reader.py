"""Dataset reader and format parsing utility.

Provides unified streaming and batch reading from JSON, CSV, and NDJSON files
with encoding safety, header validation, and error reporting.
"""

from __future__ import annotations

import csv
import io
import json
import os
from typing import Any, Generator


class DatasetReaderError(Exception):
    """Base exception for dataset reading failures."""

    pass


class DatasetReader:
    """Unified reader for structured job dataset files."""

    @staticmethod
    def detect_format(file_path: str) -> str:
        """Infer format from file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".json":
            return "json"
        elif ext == ".csv":
            return "csv"
        elif ext in (".jsonl", ".ndjson"):
            return "ndjson"
        else:
            raise DatasetReaderError(f"Unsupported dataset file extension '{ext}'")

    @classmethod
    def read_file(cls, file_path: str) -> list[dict[str, Any]]:
        """Read all records from a file into memory."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        fmt = cls.detect_format(file_path)
        if fmt == "json":
            return cls.read_json(file_path)
        elif fmt == "csv":
            return list(cls.read_csv(file_path))
        elif fmt == "ndjson":
            return list(cls.read_ndjson(file_path))
        raise DatasetReaderError(f"Unknown format: {fmt}")

    @staticmethod
    def read_json(file_path: str) -> list[dict[str, Any]]:
        """Parse a JSON array of job postings."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise DatasetReaderError(f"JSON root must be an array, got {type(data).__name__}")
        return data

    @staticmethod
    def read_csv(file_path: str) -> Generator[dict[str, Any], None, None]:
        """Stream parsed records from a CSV file."""
        with open(file_path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise DatasetReaderError("CSV file is empty or missing headers")
            for row in reader:
                yield dict(row)

    @staticmethod
    def read_ndjson(file_path: str) -> Generator[dict[str, Any], None, None]:
        """Stream parsed records from a newline-delimited JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    yield json.loads(clean_line)
                except json.JSONDecodeError as err:
                    raise DatasetReaderError(f"Invalid JSON at line {line_no}: {err}") from err

    @staticmethod
    def read_csv_string(csv_content: str) -> list[dict[str, Any]]:
        """Parse raw CSV string into list of dicts."""
        f = io.StringIO(csv_content.strip())
        reader = csv.DictReader(f)
        return list(reader)


dataset_reader = DatasetReader()
