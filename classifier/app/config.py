from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file="./.env", env_file_encoding="utf-8", extra="ignore")

    # App settings
    PROJECT_NAME: str = "BERT Classification API"
    PROJECT_VERSION: str = "0.1.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8090
    ENVIRONMENT: Literal["dev", "test", "prod"] = "dev"

    # Data settings
    DATA_DIR: Path = Field(default=Path("data"))
    TRAIN_FILE: str = "train.csv"
    VAL_FILE: str = "val.csv"
    TEST_FILE: str = "test.csv"

    # ML settings
    MODEL_PATH: Path = Field(default=Path("weights/bert.pt"))
    LABEL_ENCODER_PATH: Path = Field(default=Path("data/label_encoder.json"))
    PRETRAINED_MODEL: str = "deepvk/RuModernBERT-small"
    # PRETRAINED_MODEL: str = "cointegrated/rubert-tiny"
    MAX_LENGTH: int = 256
    DROPOUT: float = 0.1

    # Training settings
    BATCH_SIZE: int = 32
    MAX_EPOCHS: int = 10
    LEARNING_RATE: float = 2e-5
    SEED: int = 42

    # Logging settings
    MLFLOW_TRACKING_URI: str = "mlruns"
    MLFLOW_EXPERIMENT_NAME: str = "sms-classification"


settings = Settings()
