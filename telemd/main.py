#!/usr/bin/env python3
"""
Main entry point for the telemetry system.

This script runs the CAN backend with all its components.
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import main
import asyncio

if __name__ == "__main__":
    print("Starting Telemetry Data System...")
    print("=" * 40)
    asyncio.run(main()) 