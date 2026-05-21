from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
)


DEFAULT_CLASSIFIER_MODEL_DIR = "models/classifier/distilbert_issue_classifier"
DEFAULT_SUMMARIZER_MODEL = "models/summarizer/distilbart-cnn-6-6"


def get_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


@lru_cache(maxsize=1)
def load_classifier():
    model_dir = Path(os.getenv("CLASSIFIER_MODEL_DIR", DEFAULT_CLASSIFIER_MODEL_DIR))

    if not model_dir.exists():
        raise FileNotFoundError(
            f"Classifier model directory not found: {model_dir}. "
            "Expected your fine-tuned model under models/classifier/distilbert_issue_classifier."
        )

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))

    device = get_device()
    model.to(device)
    model.eval()

    return tokenizer, model, device


@lru_cache(maxsize=1)
def load_summarizer():
    model_path = os.getenv(
    "SUMMARIZER_MODEL",
    DEFAULT_SUMMARIZER_MODEL,
)

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

    device = get_device()

    model.to(device)
    model.eval()

    return tokenizer, model, device