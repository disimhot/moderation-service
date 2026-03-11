from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from ..config import settings


class ModelNotFoundError(Exception):
    """Raised when model weights file is not found."""


class LabelEncoderNotFoundError(Exception):
    """Raised when label encoder file is not found."""


class Predictor:
    """
    Predictor for SMS classification using BERT.

    Loads model from HuggingFace Hub.
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.id2label: dict[int, str] = {}
        self.label2id: dict[str, int] = {}
        self._hf_paths: dict[str, str] = {}

    def load(self) -> None:
        """Load model and label encoder from HuggingFace."""
        self._ensure_weights()
        self._load_label_encoder()
        self._load_model()

    def _resolve_file(self, filename: str) -> Path | None:
        """Find file in HF cache paths."""
        if filename in self._hf_paths:
            return Path(self._hf_paths[filename])
        return None

    def _ensure_weights(self) -> None:
        """Download model files from HuggingFace into cache."""
        required_files = ["model.safetensors", "config.json", "id2label.pt"]

        for filename in required_files:
            print(f"  Resolving {filename}...")
            self._hf_paths[filename] = hf_hub_download(
                repo_id=settings.HF_REPO_ID,
                filename=filename,
                token=settings.HF_TOKEN,
            )

        print("All model files ready (from cache or downloaded).")

    def _load_label_encoder(self) -> None:
        """Load label encoder from id2label.pt."""
        id2label_path = self._resolve_file("id2label.pt")

        if id2label_path is not None:
            id2label = torch.load(id2label_path, weights_only=False, map_location="cpu")
            self.id2label = {int(k): v for k, v in id2label.items()}
            self.label2id = {v: k for k, v in self.id2label.items()}
            print(f"Label encoder loaded from {id2label_path} ({len(self.id2label)} classes)")
            return

        raise LabelEncoderNotFoundError("Label encoder not found. Expected id2label.pt in HF repo.")

    def _load_model(self) -> None:
        """Load model from HuggingFace cache directory."""
        config_path = self._resolve_file("config.json")
        model_dir = str(config_path.parent)

        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_dir,
            id2label=self.id2label,
            label2id=self.label2id,
            local_files_only=True,
        )
        self.model.to(self.device)
        self.model.eval()

        self.tokenizer = AutoTokenizer.from_pretrained(settings.PRETRAINED_MODEL)

        print("Model loaded in HuggingFace format.")

    @torch.no_grad()
    def predict(self, texts: list[str]) -> list[dict]:
        """Predict classes for input texts."""
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=settings.MAX_LENGTH,
            return_tensors="pt",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        outputs = self.model(**inputs)
        logits = outputs.logits

        probs = torch.softmax(logits, dim=1)
        confidences, pred_ids = torch.max(probs, dim=1)

        results = []
        for i, text in enumerate(texts):
            pred_id = pred_ids[i].item()

            probabilities = {
                self.id2label[j]: round(probs[i, j].item(), 4) for j in range(len(self.id2label))
            }

            results.append(
                {
                    "text": text,
                    "label": self.id2label[pred_id],
                    "label_id": pred_id,
                    "confidence": round(confidences[i].item(), 4),
                    "probabilities": probabilities,
                }
            )

        return results

    def get_model_path(self) -> str:
        """Return path to model weights."""
        return str(self._resolve_file("model.safetensors") or "unknown")
