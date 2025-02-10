
from dataclasses import dataclass

@dataclass
class RBGColor:
    red: int
    green: int
    blue: int

@dataclass
class RBGAColor:
    red: int
    green: int
    blue: int
    alpha: int