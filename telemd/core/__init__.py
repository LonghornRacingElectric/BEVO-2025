"""
Core telemetry system components.

Contains the main orchestrator and CAN field mappings.
"""

from .backend import main
from .field_mappings import CAN_MAPPING

__all__ = ['main', 'process_can_messages', 'CAN_MAPPING'] 