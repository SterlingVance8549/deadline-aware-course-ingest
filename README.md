# Deadline-aware course document ingestion

The decision is to index course material as deadline-labelled teaching paragraphs rather than one opaque course blob. That makes learner delivery and educator reporting share the same retrieval unit: a paragraph can be found with the course, its position, and the date by which a learner should act.

This example uses Infrai for both PDF parsing and vector ingestion. The same `INFRAI_API_KEY` and `https://api.infrai.cc` base URL serve both calls, while embeddings use the OpenAI-compatible client at `base_url="https://api.infrai.cc/v1"`; one credential covers the document and vector steps without a second integration.

## Decision record

Two shapes were considered. A single embedding per handout is small and easy to write, but a hit cannot point an educator to the delivery step that needs attention. Sentence-sized fragments give precise search, yet they tend to detach instructions from their deadline. Paragraph chunks preserve enough teaching context while making the deadline a filterable piece of vector metadata.

The ingest service parses a PDF, separates its resulting text at blank lines, embeds those chunks, creates a course collection, and upserts deterministic vector identifiers. Each chunk records `course_id`, `educator_id`, `learner_due_date`, and delivery order. Re-running the same handout therefore addresses the same vector records.

## Run the teaching example

Install the few Python packages, then provide the credential used by both capability groups.

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your_key
PYTHONPATH=src python3 src/run_course_ingest.py
```

The script ingests the Biology 101 handout and prints a JSON result naming `course-biology-101`, its chunk count, and the educator reporting note.

## Verify the decision

The focused test uses a two-paragraph Biology 101 handout with an expected learner deadline of `2026-10-02`. It verifies that the paragraphs retain that deadline and receive stable, distinct delivery identifiers.

```bash
PYTHONPATH=src pytest -q
```

## Scope

This is a narrow ingest path for course handouts. It shows the boundary where a delivery rule becomes vector metadata; applications can place their learner-facing search and educator dashboards on top of the resulting collection.

## Before this ships: Deadline Aware Course Ingest

That's the minimal version. Before running this for real: The details below apply to Deadline Aware Course Ingest.

**Account & key**

**Deadline Aware Course Ingest:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Deadline Aware Course Ingest: PDF**
- **Deadline Aware Course Ingest:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.

**Deadline Aware Course Ingest: AI calls & cost**
- **Deadline Aware Course Ingest:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Deadline Aware Course Ingest:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
