from dataclasses import dataclass
from typing import Union


@dataclass
class BlockParam:
    """Dataclass for Simulink blocks.

    Attributes:
        parameter_path: string
            path of the parameter, e.g., '<model name>/<submodule>/<block>/<parameter>'
                Parameter names don't always correspond to the description in the
                graphical block mask. In doubt, check the documentation of the Simulink
                block for the correct name!
        value: int or float
            value of the block parameter
    """

    parameter_path: str
    value: Union[int, float]
