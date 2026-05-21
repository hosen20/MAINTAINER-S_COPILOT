from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from app.tools.classify_issue import classify_issue_tool


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TEST_PATH = PROJECT_ROOT / "data/splits/test.jsonl"
REPORT_DIR = PROJECT_ROOT / "data/reports"

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def run_eval():

    df = pd.read_json(
        TEST_PATH,
        lines=True,
    )

    y_true = []
    y_pred = []

    for row in df.itertuples():

        result = classify_issue_tool(
            title=row.title,
            body=row.body,
        )

        y_true.append(row.mapped_label)
        y_pred.append(result.label)

    metrics = {
        "accuracy": accuracy_score(
            y_true,
            y_pred,
        ),
        "macro_f1": f1_score(
            y_true,
            y_pred,
            average="macro",
        ),
        "weighted_f1": f1_score(
            y_true,
            y_pred,
            average="weighted",
        ),
    }

    report = classification_report(
        y_true,
        y_pred,
        output_dict=True,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
    ).tolist()

    with open(
        REPORT_DIR / "classification_eval.json",
        "w",
    ) as f:
        json.dump(
            {
                "metrics": metrics,
                "report": report,
                "confusion_matrix": matrix,
            },
            f,
            indent=2,
        )

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    run_eval()