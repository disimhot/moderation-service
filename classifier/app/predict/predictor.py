import json
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file
from transformers import AutoConfig, AutoModelForSequenceClassification

from ..config import settings
from ..models.bert import BertClassifier, BertTokenizerWrapper


class ModelNotFoundError(Exception):
    """Raised when model weights file is not found."""


class LabelEncoderNotFoundError(Exception):
    """Raised when label encoder file is not found."""


class Predictor:
    """
    Predictor for SMS classification using BERT.

    Loads model weights from local files or HuggingFace Hub.
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: BertClassifier | None = None
        self.tokenizer: BertTokenizerWrapper | None = None
        self.id2label: dict[int, str] = {}
        self.label2id: dict[str, int] = {}
        self._hf_paths: dict[str, str] = {}

    def load(self) -> None:
        """Load model and label encoder (local first, then HuggingFace)."""
        self._ensure_weights()
        self._load_label_encoder()
        self._load_model()

    def _resolve_file(self, filename: str) -> Path | None:
        """Find file: first in HF cache paths, then in local weights dir."""
        if filename in self._hf_paths:
            return Path(self._hf_paths[filename])

        local_path = Path(settings.WEIGHTS_DIR) / filename
        if local_path.exists():
            return local_path

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
        """Load label encoder from id2label.pt or label_encoder.json."""
        id2label_path = self._resolve_file("id2label.pt")

        if id2label_path is not None:
            id2label = torch.load(id2label_path, weights_only=False, map_location="cpu")
            self.id2label = {int(k): v for k, v in id2label.items()}
            self.label2id = {v: k for k, v in self.id2label.items()}
            print(f"Label encoder loaded from {id2label_path} ({len(self.id2label)} classes)")
            return

        # Fallback: label_encoder.json
        encoder_path = Path(settings.LABEL_ENCODER_PATH)

        if encoder_path.exists():
            with encoder_path.open(encoding="utf-8") as f:
                data = json.load(f)
            self.id2label = {int(k): v for k, v in data["id2label"].items()}
            self.label2id = data["label2id"]
            print(f"Label encoder loaded from {encoder_path} ({len(self.id2label)} classes)")
            return

        raise LabelEncoderNotFoundError(
            "Label encoder not found. Expected id2label.pt in weights/ "
            "or label_encoder.json in data/."
        )

    def _load_model(self) -> None:
        """Load BERT model weights from safetensors or pt format."""
        safetensors_path = self._resolve_file("model.safetensors")
        pt_path = Path(settings.MODEL_PATH)

        if safetensors_path is not None:
            state_dict = load_file(str(safetensors_path), device=str(self.device))
            print(f"Loaded weights from {safetensors_path}")
        elif pt_path.exists():
            state_dict = torch.load(pt_path, weights_only=True, map_location=self.device)
            print(f"Loaded weights from {pt_path}")
        else:
            raise ModelNotFoundError("Model not found. Check HF_REPO_ID and HF_TOKEN settings.")

        num_classes = len(self.id2label)

        # Detect model structure from state_dict keys
        # HuggingFace format: keys start with "model." (e.g. "model.encoder.layers...")
        # Custom format: keys start with "bert." or "classifier." (e.g. "bert.encoder...")
        is_hf_format = any(k.startswith("model.") for k in state_dict)

        # Initialize tokenizer
        self.tokenizer = BertTokenizerWrapper(
            pretrained_model=settings.PRETRAINED_MODEL,
            max_length=settings.MAX_LENGTH,
        )

        if is_hf_format:
            # HuggingFace ModernBertForSequenceClassification format
            config_path = self._resolve_file("config.json")
            model_dir = str(config_path.parent) if config_path else settings.PRETRAINED_MODEL

            config = AutoConfig.from_pretrained(
                model_dir,
                num_labels=num_classes,
                id2label=self.id2label,
                label2id=self.label2id,
            )

            self.model = AutoModelForSequenceClassification.from_config(config)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            self._predict_fn = self._predict_hf
            print("Model loaded in HuggingFace format.")

            print("Model loaded in HuggingFace format.")
        else:
            # Custom BertClassifier format
            self.model = BertClassifier(
                num_classes=num_classes,
                pretrained_model=settings.PRETRAINED_MODEL,
                dropout=settings.DROPOUT,
            )
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            self._predict_fn = self._predict_custom
            print("Model loaded in custom format.")

    @torch.no_grad()
    def predict(self, texts: list[str]) -> list[dict]:
        """
        Predict classes for input texts.

        Args:
            texts: List of texts to classify

        Returns:
            List of prediction dictionaries
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        return self._predict_fn(texts)

    def _predict_custom(self, texts: list[str]) -> list[dict]:
        """Predict using custom BertClassifier."""
        inputs = self.tokenizer(texts)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        logits = self.model(inputs)
        return self._format_results(texts, logits)

    def _predict_hf(self, texts: list[str]) -> list[dict]:
        """Predict using HuggingFace model."""
        inputs = self.tokenizer(texts)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        outputs = self.model(**inputs)
        logits = outputs.logits
        return self._format_results(texts, logits)

    def _format_results(self, texts: list[str], logits: torch.Tensor) -> list[dict]:
        """Format prediction results."""
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
        safetensors_path = self._resolve_file("model.safetensors")
        if safetensors_path is not None:
            return str(safetensors_path)
        return str(settings.MODEL_PATH)
