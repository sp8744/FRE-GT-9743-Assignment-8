from enum import Enum
from abc import ABCMeta, abstractmethod

class LongOrShort(Enum):
    
    LONG = 'long'
    SHORT = 'short'

    @classmethod
    def from_string(cls, value: str) -> 'LongOrShort':
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid token: {value}")

    def to_string(self) -> str:
        return self.value

class PayOrReceive(Enum):
    
    PAY = 'pay'
    RECEIVE = 'receive'

    @classmethod
    def from_string(cls, value: str) -> 'PayOrReceive':
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid token: {value}")

    def to_string(self) -> str:
        return self.value

