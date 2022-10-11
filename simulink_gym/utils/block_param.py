from dataclasses import dataclass
from typing import Union

@dataclass
class BlockParam:
    parameter_path: str
    value: Union[int, float]
