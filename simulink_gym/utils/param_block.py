from dataclasses import dataclass
from typing import Union

@dataclass
class ParamBlock:
    path: str
    parameter: str
    value: Union[int, float]
