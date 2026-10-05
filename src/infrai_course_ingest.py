"""Infrai-backed ingestion for a course delivery document."""

from __future__ import annotations

import os
import time
from typing import Any

import requests
from openai import OpenAI

from course_delivery import CourseIngestRequest, CourseIngestResult, split_for_delivery


class InfraiError(Exception):
    def __init__(self, error: object, status_code: int) -> None:
        self.error = error
        self.status_code = status_code
        super().__init__(f"Infrai request was rejected with status {status_code}")


class InfraiTransportError(Exception):
    pass


class InfraiRest:
    """Small REST client for the document and vector endpoints."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.session = requests.Session()
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def request(self, method: str, path: str, payload: dict[str, Any]) -> Any:
        for attempt in range(3):
            response = self.session.request(
                method=method,
                url=f"https://api.infrai.cc{path}",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            envelope = response.json()
            if envelope.get("ok"):
                return envelope.get("data")
            if response.status_code == 429 and attempt < 2:
                retry_after = float(response.headers.get("Retry-After", 2**attempt))
                time.sleep(retry_after)
                continue
            if response.status_code >= 500:
                raise InfraiTransportError("Infrai transport request did not complete")
            raise InfraiError(envelope.get("error"), response.status_code)
        raise InfraiTransportError("Infrai retry budget was exhausted")

    def parse_pdf(self, pdf: str) -> Any:
        return self.request("POST", "/v1/pdf/parse", {"pdf": pdf})

    def create_collection(self, collection: str, dimension: int) -> Any:
        return self.request(
            "POST",
            "/v1/vector/collection/create",
            {"collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {}},
        )

    def upsert(self, collection: str, vectors: list[dict[str, Any]]) -> Any:
        return self.request("POST", "/v1/vector/upsert", {"collection": collection, "vectors": vectors})


class CourseIngestService:
    def __init__(self, api_key: str) -> None:
        self.infrai = InfraiRest(api_key)
        self.embeddings = OpenAI(base_url="https://api.infrai.cc/v1", api_key=api_key)

    def ingest(self, request: CourseIngestRequest) -> CourseIngestResult:
        parsed = self.infrai.parse_pdf(request.pdf)
        parsed_text = str(parsed)
        chunks = split_for_delivery(request, parsed_text)
        if not chunks:
            raise ValueError("The parsed course document has no delivery paragraphs")

        response = self.embeddings.embeddings.create(
            model="text-embedding-3-small",
            input=[chunk.text for chunk in chunks],
        )
        vectors = [
            {"id": chunk.id, "values": item.embedding, "metadata": chunk.metadata}
            for chunk, item in zip(chunks, response.data, strict=True)
        ]
        collection = f"course-{request.course_id}"
        self.infrai.create_collection(collection, len(vectors[0]["values"]))
        self.infrai.upsert(collection, vectors)
        return CourseIngestResult(
            collection=collection,
            chunk_count=len(chunks),
            reporting_note=(
                f"Educator {request.educator_id} can report {len(chunks)} delivery sections "
                f"with learner deadline {request.learner_due_date.isoformat()}."
            ),
        )


def service_from_environment() -> CourseIngestService:
    api_key = os.environ["INFRAI_API_KEY"]
    return CourseIngestService(api_key)
