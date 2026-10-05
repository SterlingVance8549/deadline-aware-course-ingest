from datetime import date

from course_delivery import CourseIngestRequest, split_for_delivery


def test_delivery_chunks_keep_a_shared_learner_deadline_for_reporting() -> None:
    request = CourseIngestRequest(
        course_id="biology-101",
        educator_id="educator-42",
        learner_due_date=date(2026, 10, 2),
        pdf="https://example.edu/biology-101-week-1.pdf",
    )

    chunks = split_for_delivery(request, "Read chapter one.\n\nSubmit the observation journal.")

    assert [chunk.metadata["delivery_order"] for chunk in chunks] == ["1", "2"]
    assert {chunk.metadata["learner_due_date"] for chunk in chunks} == {"2026-10-02"}
    assert len({chunk.id for chunk in chunks}) == 2
