import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

RAW = Path("data/raw/issues.jsonl")
OUT_DIR = Path("data/splits")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, default=str) + "\n")


def safe_train_val_split(train_val_df: pd.DataFrame):
    label_counts = train_val_df["mapped_label"].value_counts()

    if len(label_counts) < 2 or label_counts.min() < 2:
        print("Warning: not enough examples per class for stratified train/val split.")
        print("Using non-stratified split for now.")
        return train_test_split(
            train_val_df,
            test_size=0.2,
            random_state=42,
            shuffle=True,
        )

    return train_test_split(
        train_val_df,
        test_size=0.2,
        random_state=42,
        stratify=train_val_df["mapped_label"],
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = read_jsonl(RAW)
    df = pd.DataFrame(rows)

    if df.empty:
        raise RuntimeError("No issues found. Run scripts/fetch_issues.py first.")

    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df = df.sort_values("created_at")

    print("Full label distribution:")
    print(df["mapped_label"].value_counts())

    cutoff_index = int(len(df) * 0.8)
    train_val_df = df.iloc[:cutoff_index].copy()
    test_df = df.iloc[cutoff_index:].copy()

    train_df, val_df = safe_train_val_split(train_val_df)

    train_rows = train_df.sort_values("created_at").to_dict(orient="records")
    val_rows = val_df.sort_values("created_at").to_dict(orient="records")
    test_rows = test_df.sort_values("created_at").to_dict(orient="records")

    write_jsonl(OUT_DIR / "train.jsonl", train_rows)
    write_jsonl(OUT_DIR / "val.jsonl", val_rows)
    write_jsonl(OUT_DIR / "test.jsonl", test_rows)

    print("\nSplit sizes:")
    print(f"train: {len(train_rows)}")
    print(f"val:   {len(val_rows)}")
    print(f"test:  {len(test_rows)}")

    print("\nLabel distribution:")
    print("train")
    print(train_df["mapped_label"].value_counts())
    print("val")
    print(val_df["mapped_label"].value_counts())
    print("test")
    print(test_df["mapped_label"].value_counts())


if __name__ == "__main__":
    main()
