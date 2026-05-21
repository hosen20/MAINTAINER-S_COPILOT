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
