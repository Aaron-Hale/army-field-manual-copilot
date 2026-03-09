# Army Field Manual Copilot (AFMC)

Army Field Manual Copilot (AFMC) is a FastAPI-based retrieval-augmented generation (RAG) service for answering questions over public U.S. Army Field Manuals. The system uses Amazon Bedrock Knowledge Bases for retrieval and Amazon Nova Micro for answer generation, and returns structured JSON responses with citations.

The repository is intended to demonstrate a production-oriented RAG application with:

- grounded answers with citations
- refusal behavior when supporting evidence is insufficient
- token and latency telemetry
- evaluation reports and CI checks
- Docker-based local execution

---

## Overview

AFMC retrieves relevant evidence from a Bedrock Knowledge Base backed by Army Field Manual content and generates a structured response with citations. The service follows a cite-or-refuse policy: if retrieval is empty or confidence is too low, the system returns a refusal with clarifying questions instead of fabricating an answer.

Primary characteristics:

- FastAPI service with JSON-first API design
- Amazon Bedrock Knowledge Bases for retrieval
- Amazon Nova Micro for response generation
- citation-grounded answers
- configurable cost and latency guardrails
- evaluation reports and CI gating

---

## API Response Shape

The service returns strict JSON with the following shape:

~~~json
{
  "answer": "…",
  "citations": [
    {
      "doc": "FM_5-0.pdf",
      "location": "s3://…",
      "snippet": "…"
    }
  ],
  "refusal": false,
  "needs_clarification": []
}
~~~

Key response behaviors:

- `answer`: generated answer when evidence is sufficient
- `citations`: evidence used to support the answer
- `refusal`: boolean indicating whether the system declined to answer
- `needs_clarification`: follow-up questions returned when evidence is weak or missing

---

## Architecture

At a high level, the service performs the following steps:

1. accept a user question through a FastAPI endpoint
2. retrieve relevant passages from Amazon Bedrock Knowledge Bases
3. apply confidence checks and cite-or-refuse logic
4. call the language model with bounded context and output limits
5. return a structured JSON response with citations and telemetry headers

Architecture notes and diagrams are available in:

- `docs/architecture.md`

---

## Repository Structure

~~~text
app/        FastAPI service code
docs/       setup notes, architecture, reports, and diagrams
eval/       evaluation scripts and metrics
scripts/    utility scripts for setup and testing
tests/      automated tests
~~~

---

## Core Design Principles

### Grounded responses
Answers should be supported by retrieved evidence and returned with citations.

### Refusal over fabrication
If supporting evidence is not available or confidence is below threshold, the service should refuse to answer and request clarification.

### Structured API behavior
The service is designed around predictable JSON responses rather than free-form chat output.

### Operational visibility
The service exposes cost and latency-related telemetry so behavior can be inspected during testing and iteration.

---

## Running Locally

### 1. Create and activate a virtual environment

~~~bash
python3 -m venv .venv
source .venv/bin/activate
~~~

### 2. Install dependencies

~~~bash
pip install -r requirements.txt
~~~

### 3. Configure environment variables

Set the environment variables required by the service, including:

- AWS credentials / profile
- AWS region
- Bedrock Knowledge Base identifier
- model identifier if configurable in your setup

If the repository includes an example environment file, copy and adapt it before running locally.

### 4. Start the API

~~~bash
uvicorn app.main:app --reload --port 8000
~~~

### 5. Test the endpoint

~~~bash
curl -X POST http://127.0.0.1:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"question":"What does FM 5-0 say about commander’s intent?"}'
~~~

---

## Docker

If Docker support is configured in the repository, the application can also be built and run in a containerized workflow.

Typical flow:

~~~bash
docker build -t afmc-rag .
docker run --rm -p 8000:8000 \
  -e AFMC_KB_ID="YOUR_KB_ID" \
  -e AWS_REGION="us-east-1" \
  -e AFMC_MODEL_ID="amazon.nova-micro-v1:0" \
  afmc-rag
~~~

Adjust environment variables to match your local AWS and Bedrock configuration.

---

## Evaluation

The repository includes evaluation artifacts and reports intended to measure retrieval quality, answer grounding, and refusal behavior.

Relevant files may include:

- `docs/report_ci.md`
- `docs/retrieval_smoketest_day5.md`
- `eval/`
- CI workflows under `.github/workflows/`

The project is structured so that quality checks can run in CI and produce artifacts for review.

---

## Example Use Cases

This project is intended for scenarios such as:

- asking doctrine questions against Army Field Manuals
- testing retrieval quality over long-form technical documents
- evaluating cite-or-refuse behavior in a RAG service
- demonstrating production-minded API design for LLM applications

---

## Development Focus

This repository emphasizes:

- retrieval quality before generation quality
- deterministic and inspectable API behavior
- modular service organization
- reproducible testing and reporting
- practical tradeoffs between latency, cost, and answer quality

---

## Recommended Entry Points

For a quick review, start with:

1. `app/main.py`
2. `app/routes/`
3. `app/services/`
4. `docs/architecture.md`
5. `docs/report_ci.md`
6. `eval/`

---

## Current Status

The repository currently represents a RAG API over Army Field Manual content with:

- FastAPI-based serving
- Bedrock retrieval integration
- structured JSON responses with citations
- refusal and clarification behavior
- local and containerized execution paths
- evaluation and CI support

Future extensions could include:

- broader document coverage
- improved retrieval quality
- richer monitoring and observability
- expanded evaluation sets
- tighter cost and latency controls
