"""Runnable example for one course handout."""

import base64

import requests

from course_delivery import CourseIngestRequest
from infrai_course_ingest import service_from_environment


def main() -> None:
    response = requests.get(
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        timeout=30,
    )
    response.raise_for_status()
    request = CourseIngestRequest(
        course_id="biology-101",
        educator_id="educator-42",
        learner_due_date="2026-10-02",
        pdf=base64.b64encode(response.content).decode("ascii"),
    )
    result = service_from_environment().ingest(request)
    print(result.model_dump_json())


if __name__ == "__main__":
    main()
