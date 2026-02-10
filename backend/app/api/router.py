import os
import httpx
from fastapi import APIRouter, HTTPException, status, Request
from . import schemas

CLASSIFIER_URL = os.getenv("CLASSIFIER_URL")

router = APIRouter()


@router.post(
    "/predict",
    summary="Classify texts",
    description="Classify texts using BERT model",
    response_model=schemas.PredictionResponse,
)
async def predict(request: schemas.PredictRequest, req: Request):
    """Predict classes for input texts."""
    client = req.app.state.http_client
    try:
        response = await client.post(
            f"{CLASSIFIER_URL}/predict",
            json=request.model_dump(),
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Classifier error: {e.response.text}",
        )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Classifier unavailable: {e}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {e}",
        )

    return response.json()


@router.get(
    "/models",
    response_model=schemas.ModelsInfoResponse,
    summary="Get model info",
    description="Get information about available model and classes",
)
async def models_info(req: Request):
    """Get information about available model and classes."""
    client = req.app.state.http_client

    try:
        response = await client.get(f"{CLASSIFIER_URL}/models")
        response.raise_for_status()

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Classifier error: {e.response.text}",
        )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Classifier unavailable: {e}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {e}",
        )
    return response.json()
