import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import LabelEncoder


@dataclass
class DataManagerConfig:
    """Configuration for SMSDataManager."""

    data_dir: Path
    text_column: str = "text"
    label_column: str = "result"
    train_file: str = "train.csv"
    val_file: str = "val.csv"
    test_file: str = "test.csv"


class SMSDataManager:
    """Manager for SMS data loading and label encoding."""

    def __init__(self, config: DataManagerConfig):
        self.config = config
        self.data_dir = Path(config.data_dir)
        self.label_encoder = LabelEncoder()
        self._data_cache: dict[str, pd.DataFrame | None] = {
            "train": None,
            "val": None,
            "test": None,
        }
        self.id2label: dict[int, str] = {}
        self.label2id: dict[str, int] = {}

    def _read_csv_file(self, filename: str) -> pd.DataFrame | None:
        """Read a CSV file and return a DataFrame."""
        file_path = self.data_dir / filename

        if file_path.exists():
            return pd.read_csv(file_path)
        return None

    def load_all(self) -> dict[str, pd.DataFrame | None]:
        """Load all data csv files and encode labels."""
        self._data_cache["train"] = self._read_csv_file(self.config.train_file)
        self._data_cache["val"] = self._read_csv_file(self.config.val_file)
        self._data_cache["test"] = self._read_csv_file(self.config.test_file)

        train_df = self._data_cache["train"]
        if train_df is None:
            raise ValueError("train.csv not found — cannot fit LabelEncoder")

        train_labels = train_df[self.config.label_column]
        encoded = self.label_encoder.fit_transform(train_labels)

        train_df["label"] = encoded
        self._data_cache["train"] = train_df

        self.id2label = dict(enumerate(self.label_encoder.classes_))
        self.label2id = {lbl: i for i, lbl in self.id2label.items()}

        for key in ["val", "test"]:
            df = self._data_cache[key]
            if df is not None:
                if self.config.label_column not in df.columns:
                    raise ValueError(f"{key}.csv must contain '{self.config.label_column}'")
                df["label"] = self.label_encoder.transform(df[self.config.label_column])
                self._data_cache[key] = df

        return self._data_cache

    def save_label_encoder(self, path: Path | str | None = None) -> Path:
        """
        Save label encoder to JSON file.

        Args:
            path: Path to save file. If None, saves to data_dir/label_encoder.json

        Returns:
            Path to saved file
        """
        path = self.data_dir / "label_encoder.json" if path is None else Path(path)

        encoder_data = {
            "id2label": {str(k): v for k, v in self.id2label.items()},
            "label2id": self.label2id,
            "classes": list(self.label_encoder.classes_),
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(encoder_data, f, ensure_ascii=False, indent=2)

        print(f"Label encoder saved to {path}")
        return path

    def get_texts_and_labels(self, split: str) -> tuple[list[str], list[int]]:
        """Get texts and labels for a specific split."""
        df = self._data_cache.get(split)
        if df is None:
            raise ValueError(f"Data for '{split}' not loaded")

        texts = df[self.config.text_column].tolist()
        labels = df["label"].tolist()
        return texts, labels
