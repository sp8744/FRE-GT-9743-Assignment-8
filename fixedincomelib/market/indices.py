from abc import ABC
from enum import Enum
import pandas as pd
from fixedincomelib.date import *
from fixedincomelib.market.registries import *
from fixedincomelib.market.basics import BusinessDayConvention, HolidayConvention

### OTHER INDICES

class Index(ql.Index):

    _type = ''

    def __init__(self, unique_name : str, type : str, content : dict):
        self.index_name_ = unique_name.upper()
        self.index_type_ = type.upper()
        self.content_ = content
        assert len(self.content_) != 0
    
    def name(self):
        return self.index_name_
    
    @classmethod
    def type(cls):
        return cls._type
    
    def display(self):
        to_print = []
        for k, v in self.content_.items():
            k_ = k
            if k_.endswith('_'):
                k_ = k[:-1]
            to_print.append([k_.upper(), v])
        return pd.DataFrame(to_print, columns=['Name', 'Value'])

### specific examples
class FXIndex(Index):

    _type = 'FX INDEX'

    def __init__(self, unique_name, content):
    
        if len(content) != 9:
            raise ValueError(f"{unique_name}: content should have 9 fields, got {len(content)}")

        self.base_ccy_ = None
        self.base_business_day_conv_ = None
        self.base_holidays_ = None
        self.base_fixing_offset_ = None
        self.quoted_ccy_ = None
        self.quoted_business_day_conv_ = None
        self.quoted_holidays_ = None
        self.quoted_fixing_offset_ = None
        self.premium_ccy_ = None
        
        upper_content = {k.upper(): v for k,v in content.items()}
        for k, v in upper_content.items():
            if k == 'BASE CURRENCY':
                self.base_ccy_ = v
            elif k == 'BASE BUSINESSDAY CONVENTION':
                self.base_business_day_conv_ = v
            elif k == 'BASE HOLIDAYS':
                self.base_holidays_ = v
            elif k == 'BASE FIXING OFFSET':
                self.base_fixing_offset_ = v
            elif k == 'QUOTED CURRENCY':
                self.quoted_ccy_ = v
            elif k == 'QUOTED BUSINESSDAY CONVENTION':
                self.quoted_business_day_conv_ = v
            elif k == 'QUOTED HOLIDAYS':
                self.quoted_holidays_ = v
            elif k == 'QUOTED FIXING OFFSET':
                self.quoted_fixing_offset_ = v
            elif k == 'PREMIUM CURRENCY':
                self.premium_ccy_ = v

        super().__init__(unique_name, FXIndex._type, self.__dict__.copy())

    @property
    def base_ccy(self) -> Currency:
        return Currency(self.base_ccy_)
    
    @property
    def base_business_day_conv(self) -> BusinessDayConvention:
        return BusinessDayConvention(self.base_business_day_conv_)
    
    @property
    def base_holidays(self) -> HolidayConvention:
        return HolidayConvention(self.base_holidays_)

    @property
    def base_fixing_offset(self) -> Period:
        return Period(self.base_fixing_offset_)
    
    @property
    def quoted_ccy(self) -> Currency:
        return Currency(self.quoted_ccy_)
    
    @property
    def quoted_business_day_conv(self) -> BusinessDayConvention:
        return BusinessDayConvention(self.quoted_business_day_conv_)
    
    @property
    def quoted_holidays(self) -> HolidayConvention:
        return HolidayConvention(self.quoted_holidays_)

    @property
    def quoted_fixing_offset(self) -> Period:
        return Period(self.quoted_fixing_offset_)
    
    @property
    def premium_ccy(self) -> Currency:
        return Currency(self.premium_ccy_)

    def currency(self) -> Currency:
        return self.base_ccy

### registry
IndexRegFunction().register(FXIndex._type, FXIndex)