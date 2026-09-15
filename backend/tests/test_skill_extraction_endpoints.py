"""Integration tests for /skills/extract and /skills/extract/batch REST endpoints.

Validates the full HTTP request-response cycle for the skill extraction API,
including response envelope shape, field presence, min_confidence filtering,
and batch aggregation semantics.
"""

import pytest
from starlette.testclient import TestClient


class TestSingleExtractEndpoint:
    """Tests for POST /api/v1/skills/extract."""

    def test_extract_basic_job_description(self, client: TestClient) -> None:
        payload = {
            "text": (
                "We are looking for a Python developer experienced in FastAPI, "
                "PostgreSQL, Redis, Docker and AWS cloud services."
            )
        }
        response = client.post("/api/v1/skills/extract", json=payload)
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True

        data = body["data"]
        assert "total_extracted" in data
        assert "skills" in data
        assert "processing_time_ms" in data
        assert isinstance(data["total_extracted"], int)
        assert data["total_extracted"] >= 4

    def test_extract_skill_fields_shape(self, client: TestClient) -> None:
        payload = {"text": "Proficiency in Python and Kubernetes required."}
        response = client.post("/api/v1/skills/extract", json=payload)
        assert response.status_code == 200

        skills = response.json()["data"]["skills"]
        assert len(skills) >= 2

        for skill in skills:
            assert "name" in skill
            assert "confidence" in skill
            assert "occurrences" in skill
            assert "matched_variants" in skill
            assert "context_snippets" in skill
            assert isinstance(skill["confidence"], float)
            assert 0.0 <= skill["confidence"] <= 1.0

    def test_extract_with_min_confidence_filter(self, client: TestClient) -> None:
        payload = {
            "text": (
                "Solid Python, Flask, AWS, Terraform, and Ansible experience needed. "
                "Bonus: knowledge of Haskell."
            ),
            "min_confidence": 0.6,
        }
        response = client.post("/api/v1/skills/extract", json=payload)
        assert response.status_code == 200

        skills = response.json()["data"]["skills"]
        for skill in skills:
            assert skill["confidence"] >= 0.6

    def test_extract_empty_text_returns_zero_skills(self, client: TestClient) -> None:
        payload = {"text": "   "}
        response = client.post("/api/v1/skills/extract", json=payload)
        assert response.status_code == 200
        assert response.json()["data"]["total_extracted"] == 0

    def test_extract_skills_sorted_by_confidence(self, client: TestClient) -> None:
        payload = {
            "text": (
                "5 years Python, 3 years JavaScript, experience with Docker, "
                "AWS, Kubernetes, Terraform, and PostgreSQL."
            )
        }
        response = client.post("/api/v1/skills/extract", json=payload)
        assert response.status_code == 200

        skills = response.json()["data"]["skills"]
        confidences = [s["confidence"] for s in skills]
        assert confidences == sorted(confidences, reverse=True), (
            "Skills must be sorted by confidence descending"
        )

    def test_extract_processing_time_is_positive(self, client: TestClient) -> None:
        payload = {"text": "Experience with Python, React, and Node.js required."}
        response = client.post("/api/v1/skills/extract", json=payload)
        assert response.status_code == 200
        assert response.json()["data"]["processing_time_ms"] > 0


class TestBatchExtractEndpoint:
    """Tests for POST /api/v1/skills/extract/batch."""

    def test_batch_extract_basic(self, client: TestClient) -> None:
        payload = {
            "documents": [
                {"id": "jd-1", "text": "Python engineer with FastAPI and PostgreSQL."},
                {"id": "jd-2", "text": "React and TypeScript frontend developer needed."},
                {"id": "jd-3", "text": "DevOps engineer skilled in Docker and Kubernetes."},
            ]
        }
        response = client.post("/api/v1/skills/extract/batch", json=payload)
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True

        data = body["data"]
        assert data["total_documents"] == 3
        assert data["total_skills_found"] >= 6
        assert len(data["results"]) == 3

    def test_batch_extract_result_item_shape(self, client: TestClient) -> None:
        payload = {
            "documents": [
                {"id": "resume-001", "text": "Experienced in Python, Machine Learning, TensorFlow."}
            ]
        }
        response = client.post("/api/v1/skills/extract/batch", json=payload)
        assert response.status_code == 200

        item = response.json()["data"]["results"][0]
        assert item["id"] == "resume-001"
        assert "total_skills" in item
        assert "skills" in item
        assert isinstance(item["skills"], list)

    def test_batch_extract_processing_time_present(self, client: TestClient) -> None:
        payload = {
            "documents": [
                {"id": "d1", "text": "Python and AWS developer."},
            ]
        }
        response = client.post("/api/v1/skills/extract/batch", json=payload)
        assert response.status_code == 200
        assert response.json()["data"]["processing_time_ms"] > 0

    def test_batch_extract_empty_documents_list(self, client: TestClient) -> None:
        payload = {"documents": []}
        response = client.post("/api/v1/skills/extract/batch", json=payload)
        assert response.status_code == 200

        data = response.json()["data"]
        assert data["total_documents"] == 0
        assert data["total_skills_found"] == 0
        assert data["results"] == []

    def test_batch_extract_with_min_confidence(self, client: TestClient) -> None:
        payload = {
            "min_confidence": 0.5,
            "documents": [
                {"id": "x", "text": "React, Node.js, MongoDB, Docker, Kubernetes, Terraform."},
            ],
        }
        response = client.post("/api/v1/skills/extract/batch", json=payload)
        assert response.status_code == 200

        for item in response.json()["data"]["results"]:
            for skill in item["skills"]:
                assert skill["confidence"] >= 0.5
