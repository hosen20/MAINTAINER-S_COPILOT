# Maintainer's Copilot

Maintainer's Copilot is an authenticated chatbot for open-source maintainers.

It classifies issues into:

- bug
- feature
- docs
- question

It also:

- extracts code-shaped entities
- summarizes issue threads
- answers maintainer questions using RAG
- stores conversation memory
- exposes Streamlit admin/chat interfaces
- exposes an embeddable React widget

---

## Day 1 status

Implemented:

- repository skeleton
- layered FastAPI application
- Docker infrastructure
- Vault adapter
- Redis adapter
- MinIO adapter
- tracing setup
- redaction layer
- structured logging
- SQLAlchemy models
- Alembic baseline migration
- GitHub issue fetching script
- stratified split script

---

## Day 2 status

Implemented:

- DistilBERT issue classifier
- model server
- classifier endpoint
- NER endpoint
- summarization endpoint
- tool wrappers
- model card generation
- evaluation pipeline
- Vault-backed startup
- backend ↔ model server integration

---

## Architecture

The project follows strict layering:

```text
app/api/            HTTP routes only
app/services/       business logic
app/repositories/   persistence layer
app/domain/         domain schemas
app/infra/          external integrations
model_server/       ML inference
chatbot/            Streamlit UI
widget/             React widget

---

## Local development

Start Vault:

```bash
docker compose up -d vault
```

Start model server:

```bash
uvicorn model_server.main:app --reload --port 8001
```

Start backend:

```bash
uvicorn app.main:app --reload --port 8000
```

Open:

```text
http://localhost:8000/docs
```

---

## Evaluation

Outputs:

```text
data/reports/
MODEL_CARD.md
EVALS.md
```

Primary metric:

```text
Macro F1
```

Reason:

Issue labels are imbalanced.

---

## Future work

Planned for later milestones:

- RAG
- memory
- widgets
- Streamlit dashboard
- pgvector retrieval
- reranking
- chatbot orchestration