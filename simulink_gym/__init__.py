# ruff: noqa: E402
"""Simulink Gym: Gym Interface Wrapper for Simulink Models."""

__version__ = "1.0.0"

# Path of the simulink block library defining the interface blocks:
from pathlib import Path

SIMULINK_BLOCK_LIB_PATH = (
    Path(__file__).parent.parent.absolute().joinpath("simulink_block_lib")
)

import sys

from gymnasium import spaces
from loguru import logger

from .environment import SimulinkEnv
from .observations import Observation, Observations

# Set logging level to INFO:
logger.remove()
logger.add(sys.stderr, level="INFO")

__all__ = [
    logger,
    spaces,
    SimulinkEnv,
    Observation,
    Observations,
    SIMULINK_BLOCK_LIB_PATH,
]
