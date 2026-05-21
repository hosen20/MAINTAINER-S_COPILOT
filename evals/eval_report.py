from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data/reports/classification_eval.json"
OUTPUT = ROOT / "EVALS.md"


def build():

    data = json.loads(INPUT.read_text())

    metrics = data["metrics"]

    content = f"""
# Evaluation

Accuracy:
{metrics["accuracy"]:.4f}

Macro F1:
{metrics["macro_f1"]:.4f}

Weighted F1:
{metrics["weighted_f1"]:.4f}
"""

    OUTPUT.write_text(content)

    print("Generated", OUTPUT)


if __name__ == "__main__":
    build()