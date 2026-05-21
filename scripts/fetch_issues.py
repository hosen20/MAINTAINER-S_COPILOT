import json
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

REPO = os.getenv("GITHUB_REPO", "pandas-dev/pandas")
TOKEN = os.getenv("GITHUB_TOKEN")
OUT = Path("data/raw/issues.jsonl")

MAX_PAGES = int(os.getenv("GITHUB_MAX_PAGES", "20"))

LABEL_MAPPING = {
    # bug
    "bug": "bug",
    "bug report": "bug",
    "type: bug": "bug",
    "type:bug": "bug",
    "kind/bug": "bug",
    "kind: bug": "bug",
    "defect": "bug",
    "regression": "bug",
    "crash": "bug",

    # feature
    "enhancement": "feature",
    "feature": "feature",
    "feature request": "feature",
    "type: feature": "feature",
    "type:feature": "feature",
    "kind/feature": "feature",
    "kind: feature": "feature",
    "new feature": "feature",
    "request": "feature",

    # docs
    "docs": "docs",
    "doc": "docs",
    "documentation": "docs",
    "type: documentation": "docs",
    "type: docs": "docs",
    "kind/docs": "docs",
    "kind: docs": "docs",

    # question
    "question": "question",
    "usage question": "question",
    "support": "question",
    "help wanted": "question",
    "usage": "question",
    "how-to": "question",
    "how to": "question",
}


def map_label(labels: list[str]) -> str | None:
    lowered = [label.lower().strip() for label in labels]

    for label in lowered:
        if label in LABEL_MAPPING:
            return LABEL_MAPPING[label]

    for label in lowered:
        if "bug" in label or "regression" in label or "crash" in label:
            return "bug"

        if "doc" in label:
            return "docs"

        if "enhancement" in label or "feature" in label or "request" in label:
            return "feature"

        if "question" in label or "support" in label or "usage" in label or "how to" in label:
            return "question"

    return None


def fetch_page(client: httpx.Client, page: int) -> list[dict[str, Any]]:
    url = f"https://api.github.com/repos/{REPO}/issues"
    response = client.get(
        url,
        params={
            "state": "closed",
            "per_page": 100,
            "page": page,
            "sort": "created",
            "direction": "asc",
        },
    )
    response.raise_for_status()
    return list(response.json())


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "maintainers-copilot-dataset-builder",
    }

    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    kept = 0
    scanned = 0
    skipped_pull_requests = 0
    skipped_unmapped = 0
    seen_labels: dict[str, int] = {}
    mapped_counts: dict[str, int] = {}

    with httpx.Client(
        headers=headers,
        timeout=30,
        follow_redirects=True,
    ) as client, OUT.open("w", encoding="utf-8") as f:
        for page in tqdm(range(1, MAX_PAGES + 1), desc=f"Fetching {REPO} issues"):
            items = fetch_page(client, page)

            if not items:
                break

            for item in items:
                scanned += 1

                if "pull_request" in item:
                    skipped_pull_requests += 1
                    continue

                labels = [label["name"] for label in item.get("labels", [])]

                for label in labels:
                    key = label.lower().strip()
                    seen_labels[key] = seen_labels.get(key, 0) + 1

                mapped = map_label(labels)

                if mapped is None:
                    skipped_unmapped += 1
                    continue

                mapped_counts[mapped] = mapped_counts.get(mapped, 0) + 1

                row = {
                    "external_id": item["id"],
                    "repo": REPO,
                    "number": item["number"],
                    "title": item["title"],
                    "body": item.get("body") or "",
                    "state": item["state"],
                    "labels": labels,
                    "mapped_label": mapped,
                    "created_at": item["created_at"],
                    "closed_at": item.get("closed_at"),
                    "url": item["html_url"],
                }

                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                kept += 1

    print("\nDone.")
    print(f"Repo: {REPO}")
    print(f"Scanned total GitHub items: {scanned}")
    print(f"Skipped pull requests: {skipped_pull_requests}")
    print(f"Skipped unmapped issues: {skipped_unmapped}")
    print(f"Kept labeled issues: {kept}")
    print(f"Wrote: {OUT}")

    print("\nMapped label counts:")
    for label, count in sorted(mapped_counts.items()):
        print(f"  {label}: {count}")

    print("\nTop seen raw GitHub labels:")
    for label, count in sorted(seen_labels.items(), key=lambda x: x[1], reverse=True)[:30]:
        print(f"  {label}: {count}")


if __name__ == "__main__":
    main()
