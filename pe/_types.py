
from typing import Union, List, Dict, Tuple

RawMatch = Tuple[int, List, Union[Dict, None]]
Memo = Dict[int, Dict[int, RawMatch]]
