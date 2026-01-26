from fastapi import APIRouter

from .schemas import (
    ErrorResponse,
    ModelsInfoResponse,
    PredictRequest,
    PredictResponse,
)
from .service import classifier_service

router = APIRouter()


@router.get(
    "/models",
    response_model=ModelsInfoResponse,
    summary="Get model info",
    description="Get information about available model and classes",
    responses={503: {"model": ErrorResponse, "description": "Model not available"}},
)
async def models_info():
    """Get information about available model and classes."""
    return classifier_service.get_models_info()


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Classify texts",
    description="Classify texts using BERT model",
    responses={
        200: {"description": "Successful prediction"},
        503: {"model": ErrorResponse, "description": "Model not available"},
    },
)
async def predict(request: PredictRequest):
    """Classify texts using BERT model."""
    return classifier_service.predict(request.texts)
