from pathlib import Path

import lightning as pl
import torch

from ..config import settings
from ..data.dataset import DataManagerConfig, SMSDataManager
from ..models.bert import BertClassifier, BertDataset, BertTokenizerWrapper, collate_fn
from ..models.module import ModuleConfig, SMSClassificationModule


def run_inference() -> dict:
    """
    Run inference on test dataset.

    Returns:
        Dictionary with test metrics
    """
    model_path = Path(settings.MODEL_PATH)
    if not model_path.exists():
        print(f"Model not found: {model_path}")
        print("Please run training first: python -m app.train")
        return {}

    # Load data
    data_config = DataManagerConfig(
        data_dir=settings.DATA_DIR,
        train_file=settings.TRAIN_FILE,
        val_file=settings.VAL_FILE,
        test_file=settings.TEST_FILE,
    )
    manager = SMSDataManager(data_config)
    manager.load_all()

    test_texts, test_labels = manager.get_texts_and_labels("test")
    num_classes = len(manager.id2label)

    # Setup model and data
    tokenizer = BertTokenizerWrapper(
        pretrained_model=settings.PRETRAINED_MODEL,
        max_length=settings.MAX_LENGTH,
    )

    test_dataset = BertDataset(test_texts, test_labels, tokenizer=tokenizer)
    test_loader = torch.utils.data.DataLoader(
        test_dataset,
        batch_size=settings.BATCH_SIZE,
        shuffle=False,
        collate_fn=collate_fn,
    )

    model = BertClassifier(
        num_classes=num_classes,
        pretrained_model=settings.PRETRAINED_MODEL,
        dropout=settings.DROPOUT,
    )
    model.load_state_dict(torch.load(model_path, weights_only=True))

    module_config = ModuleConfig(
        num_classes=num_classes,
        learning_rate=settings.LEARNING_RATE,
    )
    module = SMSClassificationModule(model=model, config=module_config)

    trainer = pl.Trainer(
        accelerator="auto",
        devices="auto",
        logger=False,
    )

    results = trainer.test(module, dataloaders=test_loader)

    print("\n=== Test Results ===")
    for key, value in results[0].items():
        print(f"{key}: {value:.4f}")

    return results[0]
