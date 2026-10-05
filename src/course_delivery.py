"""Course-shaped models and the deadline-aware chunking decision."""

from __future__ import annotations

from datetime import date
from hashlib import sha256

from pydantic import BaseModel, Field


class CourseIngestRequest(BaseModel):
    course_id: str = Field(min_length=1)
    educator_id: str = Field(min_length=1)
    learner_due_date: date
    pdf: str = Field(min_length=1)


class CourseChunk(BaseModel):
    id: str
    text: str
    metadata: dict[str, str]


class CourseIngestResult(BaseModel):
    collection: str
    chunk_count: int
    reporting_note: str


def split_for_delivery(request: CourseIngestRequest, parsed_document: str) -> list[CourseChunk]:
    """Keep each teaching paragraph separate and label its learner deadline."""
    paragraphs = [line.strip() for line in parsed_document.split("\n\n") if line.strip()]
    chunks: list[CourseChunk] = []
    for position, paragraph in enumerate(paragraphs, start=1):
        digest = sha256(f"{request.course_id}:{paragraph}".encode()).hexdigest()[:16]
        chunks.append(
            CourseChunk(
                id=f"{request.course_id}-{digest}",
                text=paragraph,
                metadata={
                    "course_id": request.course_id,
                    "educator_id": request.educator_id,
                    "learner_due_date": request.learner_due_date.isoformat(),
                    "delivery_order": str(position),
                },
            )
        )
    return chunks
