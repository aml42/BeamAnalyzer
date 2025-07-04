from dataclasses import dataclass
from enum import Enum


class SupportType(Enum):
    END = "end"
    INTERMEDIATE = "intermediate"


@dataclass
class Support:
    position: float
    width: float = 0 
    type: SupportType = SupportType.END
