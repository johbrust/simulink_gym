"""Simulink Gym: Gym Interface Wrapper for Simulink Models"""

__version__ = '0.5.0'

# Path of the simulink block library defining the interface blocks:
from pathlib import Path
SIMULINK_BLOCK_LIB_PATH = Path(__file__).parent.parent.absolute().joinpath('simulink_block_lib')

from gym import logger
from gym import spaces
from .environment import SimulinkEnv
from .observations import Observation, Observations
from .utils import BlockParam
