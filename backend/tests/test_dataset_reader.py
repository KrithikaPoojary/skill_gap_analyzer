"""Unit tests for the DatasetReader utility."""

import json
import pytest

from app.services.dataset_reader import DatasetReader, DatasetReaderError, dataset_reader


class TestDatasetReader:
    """Test suite for multi-format dataset reading and parsing."""

    def test_detect_format(self) -> None:
        assert dataset_reader.detect_format("data/jobs.json") == "json"
        assert dataset_reader.detect_format("data/jobs.csv") == "csv"
        assert dataset_reader.detect_format("data/jobs.ndjson") == "ndjson"
        with pytest.raises(DatasetReaderError):
            dataset_reader.detect_format("data/jobs.xml")

    def test_read_json(self, tmp_path) -> None:
        file = tmp_path / "jobs.json"
        payload = [{"title": "Python Dev", "company_name": "Acme"}]
        file.write_text(json.dumps(payload), encoding="utf-8")

        result = dataset_reader.read_file(str(file))
        assert len(result) == 1
        assert result[0]["title"] == "Python Dev"

    def test_read_csv(self, tmp_path) -> None:
        file = tmp_path / "jobs.csv"
        file.write_text("title,company_name\nLead SRE,CloudCo\n", encoding="utf-8")

        result = dataset_reader.read_file(str(file))
        assert len(result) == 1
        assert result[0]["company_name"] == "CloudCo"

    def test_read_csv_string(self) -> None:
        csv_text = "title,location\nData Engineer,Austin\n"
        records = dataset_reader.read_csv_string(csv_text)
        assert len(records) == 1
        assert records[0]["location"] == "Austin"

    def test_read_nonexistent_file_raises_error(self) -> None:
        with pytest.raises(FileNotFoundError):
            dataset_reader.read_file("nonexistent_path.json")
