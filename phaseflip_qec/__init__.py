"""
PhaseFlip QEC - Million-Fold Quantum Error Suppression

Created by OaGI Research
Copyright (c) 2025 OaGI Research
Licensed under Commercial License - Available for Purchase
"""

__version__ = "1.0.0"
__author__ = "OaGI Research"
__license__ = "Commercial - Available for Purchase"

from .encoders import (
    PhaseFlipEncoder,
    Distance3Encoder,
    Distance5Encoder,
    Distance7Encoder,
    AdaptiveEncoder,
)
from .decoders import SyndromeDecoder, MLDecoder
from .integration import PhaseFlipTranspilerPass

__all__ = [
    "PhaseFlipEncoder",
    "Distance3Encoder",
    "Distance5Encoder",
    "Distance7Encoder",
    "AdaptiveEncoder",
    "SyndromeDecoder",
    "MLDecoder",
    "PhaseFlipTranspilerPass",
]