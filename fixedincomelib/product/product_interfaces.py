from abc import ABCMeta, abstractclassmethod, abstractmethod
from typing import Self, Any, List
from fixedincomelib.date import Date
from fixedincomelib.market.basics import Currency
from fixedincomelib.product.utilities import *
from fixedincomelib.utilities import *
    

class ProductBuilderRegistry(Registry):
    
    def __new__(cls) -> Self:
        return super().__new__(cls, '', cls.__name__)

    def register(self, key : Any, value : Any) -> None:
        super().register(key, value)
        self._map[key] = value

class ProductVisitor(metaclass=ABCMeta):
    pass

class Product(metaclass=ABCMeta):
    
    _version = -1
    _product_type = ''

    def __init__(self) -> None:
        self.first_date_ = None
        self.last_date_ = None
        self.notional_ = None
        self.long_or_short_ = None
        self.currency_ = None

    @abstractmethod
    def serialize(self) -> dict:
        pass

    @abstractclassmethod
    def deserialize(cls, input_dict) -> 'Product':
        pass

    @abstractmethod
    def accept(self, visitor: ProductVisitor):
        pass
    
    @property
    def product_type(self) -> str:
        return self._product_type

    @property
    def first_date(self) -> Date:
        return self.first_date_
    
    @property
    def last_date(self) -> Date:
        return self.last_date_

    @property
    def notional(self) -> float:
        return self.notional_
    
    @property
    def long_or_short(self) -> LongOrShort | List[LongOrShort]:
        return self.long_or_short_
    
    @property
    def currency(self) -> Currency | List[Currency]:
        return self.currency_