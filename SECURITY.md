# SECURITY

## Redaction policy

The project redacts sensitive strings before data leaves the service boundary.

The redaction layer lives in:

```text
app/infra/redaction.py
```

It is used before:

```text
logs
trace span attributes
memory writes
tool inputs and outputs
```

## Patterns redacted

The current redaction layer covers:

```text
OpenAI-style API keys: sk-...
GitHub fine-grained tokens: github_pat_...
GitHub classic tokens: ghp_..., gho_...
Bearer tokens
Authorization headers
password=... fragments
Postgres URLs
PEM private keys
```

## Why these patterns

Maintainers often paste issue text, stack traces, CI logs, `.env` fragments, package manager logs, and GitHub workflow errors into chat. These can contain tokens, credentials, database URLs, or authorization headers.

## Boundary rule

No service should write raw user text directly to logs, traces, or memory. Raw text must pass through:

```python
redact_text(...)
```

or:

```python
redact_value(...)
```

first.

## Test

The test file:

```text
tests/test_redaction.py
```

checks that fake API keys and tokens are not preserved in redacted output.