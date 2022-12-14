"""Simulink Gym: Gym Interface Wrapper for Simulink Models"""

__version__ = "0.6.1"

# Path of the simulink block library defining the interface blocks:
from pathlib import Path

SIMULINK_BLOCK_LIB_PATH = (
    Path(__file__).parent.parent.absolute().joinpath("simulink_block_lib")
)

from gym import logger  # noqa: E402
from gym import spaces  # noqa: E402
from .environment import SimulinkEnv  # noqa: E402
from .observations import Observation, Observations  # noqa: E402

__all__ = [
    logger,
    spaces,
    SimulinkEnv,
    Observation,
    Observations,
    SIMULINK_BLOCK_LIB_PATH,
]
