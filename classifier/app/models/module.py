from dataclasses import dataclass

import lightning as pl
import torch
import torchmetrics
from torch import nn

from .loss import FocalLoss


@dataclass
class ModuleConfig:
    """Configuration for SMSClassificationModule."""

    num_classes: int = 13
    learning_rate: float = 2e-5
    loss_type: str = "cross_entropy"
    focal_gamma: float = 2.0
    scheduler_eta_min: float = 1e-7
    class_weights: torch.Tensor | None = None


class SMSClassificationModule(pl.LightningModule):
    """
    Lightning module for multi-class SMS classification.

    Args:
        model: Neural network model (BERT)
        config: Module configuration
    """

    def __init__(self, model: nn.Module, config: ModuleConfig):
        super().__init__()
        self.save_hyperparameters(ignore=["model", "criterion"])

        self.model = model
        self.num_classes = config.num_classes
        self.learning_rate = config.learning_rate
        self.scheduler_eta_min = config.scheduler_eta_min

        # Loss
        self.criterion = self._create_loss(
            config.loss_type, config.class_weights, config.focal_gamma
        )

        # Validation metrics
        self.val_f1_weighted = torchmetrics.F1Score(
            task="multiclass", num_classes=config.num_classes, average="weighted"
        )
        self.val_f1_macro = torchmetrics.F1Score(
            task="multiclass", num_classes=config.num_classes, average="macro"
        )
        self.val_accuracy = torchmetrics.Accuracy(task="multiclass", num_classes=config.num_classes)

        # Test metrics
        self.test_f1_weighted = torchmetrics.F1Score(
            task="multiclass", num_classes=config.num_classes, average="weighted"
        )
        self.test_f1_macro = torchmetrics.F1Score(
            task="multiclass", num_classes=config.num_classes, average="macro"
        )
        self.test_accuracy = torchmetrics.Accuracy(
            task="multiclass", num_classes=config.num_classes
        )

    def _create_loss(self, loss_type, class_weights, focal_gamma):
        if loss_type == "cross_entropy":
            return nn.CrossEntropyLoss(weight=class_weights)
        if loss_type == "focal":
            return FocalLoss(alpha=class_weights, gamma=focal_gamma)
        raise ValueError(f"Unknown loss type: {loss_type}")

    def forward(self, inputs) -> torch.Tensor:
        """Forward pass through the model."""
        return self.model(inputs)

    def training_step(self, batch) -> torch.Tensor:
        inputs, targets = batch
        logits = self.forward(inputs)
        loss = self.criterion(logits, targets)

        self.log("train_loss", loss, prog_bar=True, logger=True, on_step=True, on_epoch=True)
        return loss

    def validation_step(self, batch):
        inputs, targets = batch
        logits = self.forward(inputs)
        loss = self.criterion(logits, targets)

        preds = torch.argmax(logits, dim=1)

        self.log("val_loss", loss, prog_bar=True, logger=True, on_step=False, on_epoch=True)

        self.val_accuracy(preds, targets)
        self.val_f1_weighted(preds, targets)
        self.val_f1_macro(preds, targets)

        self.log("val_accuracy", self.val_accuracy, prog_bar=True, on_epoch=True)
        self.log("val_f1_weighted", self.val_f1_weighted, prog_bar=True, on_epoch=True)
        self.log("val_f1_macro", self.val_f1_macro, on_epoch=True)

    def test_step(self, batch):
        inputs, targets = batch
        logits = self.forward(inputs)
        loss = self.criterion(logits, targets)

        preds = torch.argmax(logits, dim=1)

        self.log("test_loss", loss, prog_bar=True, on_epoch=True)

        self.test_accuracy(preds, targets)
        self.test_f1_weighted(preds, targets)
        self.test_f1_macro(preds, targets)

        self.log("test_accuracy", self.test_accuracy, prog_bar=True, on_epoch=True)
        self.log("test_f1_weighted", self.test_f1_weighted, prog_bar=True, on_epoch=True)
        self.log("test_f1_macro", self.test_f1_macro, on_epoch=True)

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.learning_rate)

        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=self.trainer.estimated_stepping_batches,
            eta_min=self.scheduler_eta_min,
        )

        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "interval": "step",
            },
        }
