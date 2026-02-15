"""
Hardware interface components.

Contains CAN bus interface and data generation modules.
"""

from .interface import CANInterface
from .simulator import CANGenerator

__all__ = ['CANInterface', 'CANGenerator'] 