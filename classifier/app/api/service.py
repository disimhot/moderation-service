from fastapi import HTTPException, status

from ..predict.predictor import LabelEncoderNotFoundError, ModelNotFoundError, Predictor
from .schemas import (
    ClassInfo,
    HealthResponse,
    ModelStatus,
    ModelsInfoResponse,
    PredictionItem,
    PredictResponse,
)


class ClassifierService:
    """Service for managing BERT classification model."""

    def __init__(self):
        self.predictor: Predictor | None = None
        self.error: str | None = None

    def load(self) -> None:
        """Load model on startup."""
        try:
            self.predictor = Predictor()
            self.predictor.load()
            self.error = None
            print("BERT model loaded successfully")

        except (ModelNotFoundError, LabelEncoderNotFoundError) as e:
            self.predictor = None
            self.error = str(e)
            print(f"Model not available: {e}")

        except Exception as e:
            self.predictor = None
            self.error = f"Unexpected error: {e}"
            print(f"Model failed to load: {e}")

    def _get_predictor(self) -> Predictor:
        """Get predictor or raise HTTPException if not available."""
        if self.predictor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=self.error or "Model not available",
            )
        return self.predictor

    def predict(self, texts: list[str]) -> PredictResponse:
        """Classify texts using BERT model."""
        predictor = self._get_predictor()

        try:
            results = predictor.predict(texts)

            predictions = [
                PredictionItem(
                    text=r["text"],
                    label=r["label"],
                    label_id=r["label_id"],
                    confidence=r["confidence"],
                )
                for r in results
            ]

            return PredictResponse(predictions=predictions)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Prediction failed: {e}",
            ) from e

    def get_health_status(self) -> HealthResponse:
        """Get health status with model info."""
        if self.predictor is not None:
            model_status = ModelStatus(
                available=True,
                path=self.predictor.get_model_path(),
                error=None,
            )
        else:
            model_status = ModelStatus(
                available=False,
                path="unknown",
                error=self.error,
            )

        return HealthResponse(status="healthy", model=model_status)

    def get_models_info(self) -> ModelsInfoResponse:
        """Get information about model and classes."""
        predictor = self._get_predictor()

        classes = [
            ClassInfo(id=id_, name=name) for id_, name in sorted(predictor.id2label.items())
        ]

        return ModelsInfoResponse(
            model_available=True,
            num_classes=len(predictor.id2label),
            classes=classes,
        )

classifier_service = ClassifierService()
