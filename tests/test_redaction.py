from app.infra.redaction import REDACTION, redact_text, redact_value


def test_redacts_api_keys_and_tokens() -> None:
    raw = (
        "OpenAI key sk-abcdefghijklmnopqrstuvwxyz123456 "
        "GitHub token ghp_abcdefghijklmnopqrstuvwxyz123456 "
        "Header Authorization: Bearer abc.def.ghi "
        "password=super-secret"
    )

    redacted = redact_text(raw)

    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in redacted
    assert "ghp_abcdefghijklmnopqrstuvwxyz123456" not in redacted
    assert "Bearer abc.def.ghi" not in redacted
    assert "password=super-secret" not in redacted
    assert REDACTION in redacted


def test_redacts_nested_values() -> None:
    raw = {
        "message": "token github_pat_abcdefghijklmnopqrstuvwxyz1234567890",
        "items": ["password=hunter2"],
    }

    redacted = redact_value(raw)

    assert "github_pat_" not in redacted["message"]
    assert redacted["items"][0] == REDACTION