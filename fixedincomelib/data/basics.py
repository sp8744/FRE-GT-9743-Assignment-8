import pandas as pd
from typing import Tuple, Any, Self
from abc import ABC, abstractclassmethod, abstractmethod 
from fixedincomelib.utilities import Registry
from fixedincomelib.market import (DataConvention, DataIdentifier, DataIdentifierRegistry)


class DataObjectDeserializerRegistry(Registry):
    
    def __new__(cls) -> Self:
        return super().__new__(cls, '', cls.__name__)

    def register(self, key : Any, value : Any) -> None:
        super().register(key, value)
        self._map[key] = value


class DataObject(ABC):

    _version = -1
    _data_shape = ''

    def __init__(self, data_type: str, data_convention: DataConvention|str):
        self.data_type_ = data_type
        self.data_convention_ = data_convention
        func = DataIdentifierRegistry().get(self.data_type_)
        self.data_identifier_ = func(self.data_convention_)

    @property
    def data_shape(self) -> str:
        return self._data_shape
         
    @property
    def data_identifier(self) -> DataIdentifier:
        return self.data_identifier_
    
    @property
    def data_type(self) -> str:
        return self.data_type_

    @property
    def data_convention(self) -> DataConvention|str:
        return self.data_convention_

    @abstractmethod
    def display(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def serialize(self) -> dict:
        pass

    @abstractclassmethod
    def deserialize(cls, input_dict : dict) -> "DataObject":
        pass



