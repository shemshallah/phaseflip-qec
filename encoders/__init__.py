"""
PhaseFlip QEC Encoders

Provides quantum error correction encoders for phase-flip errors
at multiple code distances (3, 5, 7) with adaptive selection.
"""

from .distance_3 import Distance3Encoder
from .distance_5 import Distance5Encoder
from .distance_7 import Distance7Encoder
from .adaptive import AdaptiveEncoder

# Base class for all encoders
PhaseFlipEncoder = Distance3Encoder

__all__ = [
    "PhaseFlipEncoder",
    "Distance3Encoder",
    "Distance5Encoder",
    "Distance7Encoder",
    "AdaptiveEncoder",
]