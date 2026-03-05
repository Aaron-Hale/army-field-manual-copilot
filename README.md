# Doctrine (Spec v0)

## What it does
TBD (1–2 sentences)

## Output schema
{
  "example": "value"
}

## Metrics
- TBD

## Guardrails / caps
- TBD

## Repo structure
- app/ FastAPI service
- eval/ evaluation scripts + metrics
- scripts/ one-off utilities
- docs/ notes / diagrams

---

## Demo (30 seconds)

Terminal 1 (server + logs):

    cd ~/projects/army-field-manual-copilot
    export AFMC_KB_ID=48Q5IV9XZ1
    export AWS_REGION=us-east-1
    export AFMC_MODEL_ID=amazon.nova-micro-v1:0
    ./scripts/run_local.sh

Terminal 2 (demo calls):

    cd ~/projects/army-field-manual-copilot
    ./scripts/demo.sh

## Architecture

See docs/architecture.md (includes a Mermaid diagram).

