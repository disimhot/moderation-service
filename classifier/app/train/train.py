from pathlib import Path

import lightning as pl
import torch

from ..config import settings
from ..data.dataset import DataManagerConfig, SMSDataManager
from ..models.bert import BertClassifier, BertDataset, BertTokenizerWrapper, collate_fn
from ..models.loss import compute_class_weights
from ..models.module import ModuleConfig, SMSClassificationModule


def run_training() -> None:
    """Train SMS classification model."""
    pl.seed_everything(settings.SEED)

    # Load data
    data_config = DataManagerConfig(
        data_dir=settings.DATA_DIR,
        train_file=settings.TRAIN_FILE,
        val_file=settings.VAL_FILE,
        test_file=settings.TEST_FILE,
    )
    manager = SMSDataManager(data_config)
    manager.load_all()
    manager.save_label_encoder(settings.LABEL_ENCODER_PATH)

    num_classes = len(manager.id2label)
    print(f"Number of classes: {num_classes}")
    print(f"Classes: {manager.id2label}")

    train_texts, train_labels = manager.get_texts_and_labels("train")
    val_texts, val_labels = manager.get_texts_and_labels("val")

    # Compute class weights
    class_weights = compute_class_weights(train_labels, num_classes)

    # Setup tokenizer and datasets
    tokenizer = BertTokenizerWrapper(
        pretrained_model=settings.PRETRAINED_MODEL,
        max_length=settings.MAX_LENGTH,
    )

    train_dataset = BertDataset(train_texts, train_labels, tokenizer=tokenizer)
    val_dataset = BertDataset(val_texts, val_labels, tokenizer=tokenizer)

    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=settings.BATCH_SIZE,
        shuffle=True,
        collate_fn=collate_fn,
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset,
        batch_size=settings.BATCH_SIZE,
        shuffle=False,
        collate_fn=collate_fn,
    )

    # Setup model
    model = BertClassifier(
        num_classes=num_classes,
        pretrained_model=settings.PRETRAINED_MODEL,
        dropout=settings.DROPOUT,
    )

    module_config = ModuleConfig(
        num_classes=num_classes,
        learning_rate=settings.LEARNING_RATE,
        class_weights=class_weights,
    )
    module = SMSClassificationModule(model=model, config=module_config)

    # Loggers
    mlflow_logger = pl.pytorch.loggers.MLFlowLogger(
        experiment_name=settings.MLFLOW_EXPERIMENT_NAME,
        tracking_uri=settings.MLFLOW_TRACKING_URI,
    )

    # Callbacks
    callbacks = [
        pl.pytorch.callbacks.LearningRateMonitor(logging_interval="step"),
        pl.pytorch.callbacks.RichModelSummary(max_depth=2),
        pl.pytorch.callbacks.ModelCheckpoint(
            dirpath="checkpoints",
            filename="best-{epoch:02d}-{val_f1_weighted:.3f}",
            monitor="val_f1_weighted",
            mode="max",
            save_top_k=1,
        ),
        pl.pytorch.callbacks.EarlyStopping(
            monitor="val_f1_weighted",
            mode="max",
            patience=3,
            min_delta=0.001,
        ),
    ]

    # Trainer
    trainer = pl.Trainer(
        max_epochs=settings.MAX_EPOCHS,
        accelerator="auto",
        devices="auto",
        logger=mlflow_logger,
        callbacks=callbacks,
    )

    # Train
    trainer.fit(module, train_dataloaders=train_loader, val_dataloaders=val_loader)

    # Save model
    output_path = Path(settings.MODEL_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(module.model.state_dict(), output_path)
    print(f"\nModel saved to {output_path}")


if __name__ == "__main__":
    run_training()
