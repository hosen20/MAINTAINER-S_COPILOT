from __future__ import annotations

import re
from typing import Any


ENTITY_PATTERNS = {
    "url": r"https?://[^\s\)\]\}]+",
    "file_path": r"(?:[A-Za-z0-9_\-\.]+/)+[A-Za-z0-9_\-\.]+\.[A-Za-z0-9]+",
    "python_file": r"\b[A-Za-z_][A-Za-z0-9_]*\.py\b",
    "go_file": r"\b[A-Za-z_][A-Za-z0-9_]*\.go\b",
    "yaml_file": r"\b[A-Za-z_][A-Za-z0-9_\-]*\.ya?ml\b",
    "json_file": r"\b[A-Za-z_][A-Za-z0-9_\-]*\.json\b",
    "version": r"\bv?\d+\.\d+(?:\.\d+)?(?:[-+][A-Za-z0-9\.\-]+)?\b",
    "error_type": r"\b[A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Failure|Timeout)\b",
    "command": r"(?:^|\n)\s*(?:kubectl|docker|python|pip|npm|go|make|helm|git)\s+[^\n]+",
    "function_call": r"\b[A-Za-z_][A-Za-z0-9_]*\([^\)]{0,80}\)",
    "k8s_component": (
        r"\b(?:"
        r"kubelet|kubectl|apiserver|scheduler|controller-manager|etcd|"
        r"pod|deployment|service|ingress|configmap|secret|namespace|"
        r"kubeconfig|kube-apiserver"
        r")\b"
    ),
    "issue_ref": r"#\d+",
    "sha": r"\b[0-9a-f]{7,40}\b",
}


STOP_WORDS = {
    "title",
    "body",
    "running",
    "documentation",
    "when",
    "see",
    "for",
    "yaml",
    "json",
    "the",
    "and",
    "not",
    "with",
    "from",
    "this",
    "that",
    "gives",
    "causes",
    "apply",
    "crashes",
    "issue",
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def build_issue_text(title: str, body: str) -> str:
    return f"Title: {clean_text(title)}\n\nBody: {clean_text(body)}"


def extract_entities_from_text(text: str, max_per_type: int = 20) -> list[dict]:
    results: list[dict] = []
    global_seen: set[tuple[str, str]] = set()

    for entity_type, pattern in ENTITY_PATTERNS.items():
        matches = re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE)

        per_type_count = 0

        for match in matches:
            value = match.group(0).strip()

            if not value:
                continue

            normalized = value.lower().strip()

            if normalized in STOP_WORDS:
                continue

            key = (entity_type, normalized)

            if key in global_seen:
                continue

            global_seen.add(key)

            results.append(
                {
                    "type": entity_type,
                    "value": value,
                    "start": match.start(),
                    "end": match.end(),
                }
            )

            per_type_count += 1

            if per_type_count >= max_per_type:
                break

    return sorted(results, key=lambda item: (item["start"], item["type"]))


def extract_entities(title: str, body: str, max_per_type: int = 20) -> dict:
    text = build_issue_text(title, body)
    entities = extract_entities_from_text(text, max_per_type=max_per_type)

    return {
        "entities": entities,
        "count": len(entities),
        "method": "rule_based_code_entity_extractor",
    }