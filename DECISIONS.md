
---

# 7. `DECISIONS.md`

**Role:** Explain and defend project decisions.

```md
# Decisions

## Dataset

Chosen repository:

kubernetes/kubernetes

Reason:
- Supports 4 mapped classes:
  - bug
  - docs
  - feature
  - question
- Better label quality than previous repositories.
- Large enough after filtering.

---

## Day 2 Decisions

### Model choice

- Classical ML removed from scope.
- DistilBERT selected as final classifier.
- Fine-tuned in Google Colab.

Reason:
- Faster inference than larger encoder models.
- Good macro-F1 under class imbalance.
- Small enough for local serving.

---

### Training decisions

- Class-weighted loss enabled.
- Stratified train/validation/test split used.
- Macro-F1 selected as primary metric.

Reason:
- Feature and question classes were underrepresented.
- Accuracy alone would hide imbalance.

---

### Serving decisions

- Separate FastAPI model server introduced.
- Main API communicates through HTTP.

Reason:
- Separation between ML inference and business logic.
- Easier deployment and scaling.

---

### NER decisions

- Rule-based NER selected.

Reason:
- Faster than training an additional sequence tagger.
- Works well for:
  - file paths
  - versions
  - issue references
  - commands
  - Kubernetes entities

---

### Summarization decisions

- DistilBART summarizer integrated.

Reason:
- Lightweight.
- No additional fine-tuning required.

---

### Security decisions

- Vault used for secret storage.
- Boot checks enabled for production-like startup.

The first fine-tuned classifier is functional but weak on the small imbalanced Kubernetes split. Macro-F1 is currently 0.3820. The threshold is intentionally set slightly below the observed score so CI catches regressions while remaining realistic for this prototype.

## Day 3 — Advanced RAG decisions

### Corpus

The RAG corpus is built from project documentation plus a held-out slice of resolved issues from the local test split. The held-out issues are not used to train the classifier.

### Chunking

I use markdown/paragraph-aware chunking with overlap instead of naive fixed-size chunking.

Chosen parameters:

```text
max_chars = 1200
overlap_chars = 180
```

Reason:

```text
1200 characters keeps chunks small enough for reranking and answer grounding.
180 characters preserves context at chunk boundaries.
Markdown and paragraph boundaries reduce broken code blocks and broken explanations.
```

### Embedding model

Chosen model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Reason:

```text
It is small, local, fast on CPU, produces 384-dimensional vectors compatible with the existing pgvector schema, and is good enough for project-document retrieval.
```

### Retrieval

The retriever uses hybrid scoring:

```text
0.65 dense cosine similarity
0.35 sparse TF-IDF similarity
```

Reason:

```text
Dense retrieval handles paraphrase.
Sparse retrieval preserves exact terms like FastAPI, Alembic, JWT, Vault, MinIO, Redis, pgvector, and error names.
```

### Reranking

The top hybrid candidates are reranked with:

```text
cross-encoder/ms-marco-MiniLM-L-6-v2
```

Reason:

```text
The cross-encoder reads the query and passage together, which improves precision on the final top chunks.
```

### Query transformation

The query rewrite step adds project-specific synonyms for terms such as auth, db, docker, trace, secret, classifier, and RAG.

### Metadata filtering

The RAG API supports filters for:

```text
repo
source_type
```

This allows documentation-only retrieval, issue-only retrieval, or repository-specific retrieval.

### Evaluation

The RAG eval uses:

```text
hit@5
MRR@10
average retrieved chunks
```

The first golden set is small and should be expanded to 25 examples before final submission.