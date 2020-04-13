
from typing import Union, Dict, Tuple

RawMatch = Tuple[int, Tuple, Union[Dict, None]]
Memo = Dict[int, Dict[int, RawMatch]]
