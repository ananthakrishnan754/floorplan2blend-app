"""UNet with ResNet34 encoder."""

from __future__ import annotations

import torch.nn as nn
import segmentation_models_pytorch as smp

from .labels import NUM_CLASSES


def build_model(
    encoder_name: str = "resnet34",
    encoder_weights: str | None = "imagenet",
    num_classes: int = NUM_CLASSES,
    in_channels: int = 3,
) -> nn.Module:
    return smp.Unet(
        encoder_name=encoder_name,
        encoder_weights=encoder_weights,
        in_channels=in_channels,
        classes=num_classes,
    )
