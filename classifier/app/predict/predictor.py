import json
from pathlib import Path

import torch

from ..config import settings
from ..models.bert import BertClassifier, BertTokenizerWrapper


class ModelNotFoundError(Exception):
    """Raised when model weights file is not found."""


class LabelEncoderNotFoundError(Exception):
    """Raised when label encoder file is not found."""


class Predictor:
    """
    Predictor for SMS classification using BERT.

    Loads model weights and provides prediction interface.
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: BertClassifier | None = None
        self.tokenizer: BertTokenizerWrapper | None = None
        self.id2label: dict[int, str] = {}
        self.label2id: dict[str, int] = {}

    def load(self) -> None:
        """Load model and label encoder."""
        self._load_label_encoder()
        self._load_model()

    def _load_label_encoder(self) -> None:
        """Load label encoder from JSON file."""
        encoder_path = Path(settings.LABEL_ENCODER_PATH)

        if not encoder_path.exists():
            raise LabelEncoderNotFoundError(
                f"Label encoder not found: {encoder_path}. "
                "Please run training first to generate label_encoder.json"
            )

        with encoder_path.open(encoding="utf-8") as f:
            data = json.load(f)

        self.id2label = {int(k): v for k, v in data["id2label"].items()}
        self.label2id = data["label2id"]

    def _load_model(self) -> None:
        """Load BERT model weights."""
        model_path = Path(settings.MODEL_PATH)

        if not model_path.exists():
            raise ModelNotFoundError(
                f"Model not found: {model_path}. Please train the model first."
            )

        # Load state dict to determine num_classes
        state_dict = torch.load(model_path, weights_only=True, map_location=self.device)
        num_classes = state_dict["classifier.1.weight"].shape[0]

        # Validate num_classes matches label encoder
        if num_classes != len(self.id2label):
            raise RuntimeError(
                f"Mismatch: model has {num_classes} classes, "
                f"but label_encoder has {len(self.id2label)}."
            )

        # Initialize tokenizer
        self.tokenizer = BertTokenizerWrapper(
            pretrained_model=settings.PRETRAINED_MODEL,
            max_length=settings.MAX_LENGTH,
        )

        # Initialize and load model
        self.model = BertClassifier(
            num_classes=num_classes,
            pretrained_model=settings.PRETRAINED_MODEL,
            dropout=settings.DROPOUT,
        )
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

    @torch.no_grad()
    def predict(self, texts: list[str]) -> list[dict]:
        """
        Predict classes for input texts.

        Args:
            texts: List of texts to classify

        Returns:
            List of prediction dictionaries with keys:
                - text: Original input text
                - label: Predicted class label
                - label_id: Predicted class ID
                - confidence: Prediction confidence
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Tokenize
        inputs = self.tokenizer(texts)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Predict
        logits = self.model(inputs)
        probs = torch.softmax(logits, dim=1)
        confidences, pred_ids = torch.max(probs, dim=1)

        # Format results
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
        return str(settings.MODEL_PATH)
