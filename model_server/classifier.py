from __future__ import annotations

from typing import Any

import torch

from model_server.loaders import load_classifier


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def build_issue_text(title: str, body: str) -> str:
    return f"Title: {clean_text(title)}\n\nBody: {clean_text(body)}"


def classify_issue(
    title: str,
    body: str,
    max_length: int = 384,
) -> dict:

    tokenizer, model, device = load_classifier()

    text = build_issue_text(title, body)

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    )

    # DistilBERT fix
    if "token_type_ids" in inputs:
        inputs.pop("token_type_ids")

    inputs = {
        k: v.to(device)
        for k, v in inputs.items()
    }

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits

    probs = torch.softmax(
        logits,
        dim=-1,
    )[0]

    probs = probs.cpu().numpy()

    id2label = {
        int(k): v
        for k, v in model.config.id2label.items()
    }

    pred = int(probs.argmax())

    return {
        "label": id2label[pred],
        "confidence": float(probs[pred]),
        "probabilities": {
            id2label[i]: float(probs[i])
            for i in range(len(probs))
        },
        "model": "distilbert_issue_classifier",
    }