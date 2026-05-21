from __future__ import annotations

from typing import Any

import torch

from model_server.loaders import load_summarizer


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def build_issue_text(title: str, body: str) -> str:
    return f"Title: {clean_text(title)}\n\nBody: {clean_text(body)}"


def summarize_text(
    text: str,
    max_chars: int = 3500,
    max_new_tokens: int = 130,
    min_new_tokens: int = 30,
) -> dict:
    text = clean_text(text).strip()

    if not text:
        return {
            "summary": "",
            "model": "sshleifer/distilbart-cnn-12-6",
            "input_chars": 0,
        }

    tokenizer, model, device = load_summarizer()

    clipped = text[:max_chars]

    inputs = tokenizer(
        clipped,
        return_tensors="pt",
        truncation=True,
        max_length=1024,
    )

    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            min_new_tokens=min_new_tokens,
            num_beams=4,
            do_sample=False,
            early_stopping=True,
        )

    summary = tokenizer.decode(
        output_ids[0],
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    ).strip()

    return {
        "summary": summary,
        "model": "sshleifer/distilbart-cnn-12-6",
        "input_chars": len(text),
        "used_chars": len(clipped),
    }


def summarize_issue(title: str, body: str) -> dict:
    text = build_issue_text(title, body)
    return summarize_text(text)