from typing import List, Dict, Optional
import numpy as np
import pandas as pd 
from fixedincomelib.market import *

### PV AND CASH REPORT

class PVCashReport:

    def __init__(self, currencies : Currency|List[Currency]) -> None:
        self.currencies_ = list(dict.fromkeys([currencies] if not isinstance(currencies, List) else currencies))
        # self.currencies_ = [currencies] if not isinstance(currencies, List) else currencies
        self.num_currencies_ = len(self.currencies_)
        self.pv_ = {each : 0.  for each in self.currencies_}
        self.cash_ = {each : 0.  for each in self.currencies_}
    
    def set_pv(self, currency : Currency, value : float):
        assert currency in self.currencies
        self.pv_[currency] = value

    def set_cash(self, currency : Currency, value : float):
        assert currency in self.currencies
        self.cash_[currency] = value

    def display(self) -> pd.DataFrame:
        content = []
        for currency in self.currencies_:
            this_pv = self.pv_[currency]
            this_cash = self.cash_[currency]
            content += \
                [
                    [currency.ccy.code(), 'PV', this_pv - this_cash],
                    [currency.ccy.code(), 'CASH', this_cash]
                ]
            
        return pd.DataFrame(content, columns=['Currency', 'Type', 'Value'])

    @property
    def currencies(self) -> List[Currency]:
        return self.currencies_
    
    @property
    def num_currencies(self) -> int:
        return self.num_currencies_
    
    @property
    def pv(self) -> Dict:
        return [[currency.ccy.code(), self.pv_[currency]]for currency in self.currencies_]
    
    @property
    def cash(self) -> Dict:
        return [[currency.ccy.code(), self.cash_[currency]]for currency in self.currencies_]
    
### Risk Report

class RiskReportColumns(Enum):
    
    DATA_TYPE = 'DATA_TYPE'
    DATA_CONVENTION = 'DATA_CONVENTION'
    AXIS1 = 'AXIS1'
    AXIS2 = 'AXIS2'
    DATA_VALUES = 'MARKET_QUOTE'
    UNIT = 'UNIT'
    VALUES = 'VALUES'

    @classmethod
    def from_string(cls, value: str) -> 'RiskReportColumns':
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        try:
            return cls(value.upper())
        except ValueError:
            raise ValueError(f"Invalid token: {value}")

    def to_string(self) -> str:
        return self.value

class RiskReprt:

    def __init__(self, content : np.ndarray) -> None:
        self.content_ = content
        self.schema_ = [ \
            RiskReportColumns.DATA_TYPE.to_string(),
            RiskReportColumns.DATA_CONVENTION.to_string(),
            RiskReportColumns.AXIS1.to_string(),
            RiskReportColumns.AXIS2.to_string(),
            RiskReportColumns.DATA_VALUES.to_string(),
            RiskReportColumns.UNIT.to_string(),
            RiskReportColumns.VALUES.to_string()
        ]

    def display(self):
        df = pd.DataFrame(self.content_, columns=self.schema_)
        df[RiskReportColumns.VALUES.to_string()] = df.apply(lambda x: \
            float(x[RiskReportColumns.VALUES.to_string()]) * float(x[RiskReportColumns.UNIT.to_string()]), axis=1)
        return df
    
    @property
    def content(self) -> List:
        return self.content_

    @property
    def schema(self) -> List:
        return self.schema_

### CASHFLOWS REPORT

class CFReportColumns(Enum):
    
    PRODUCT_TYPE = 'PRODUCT_TYPE'
    VALUATION_ENGINE_TYPE = 'VALUATION_ENGINE_TYPE'
    LEG_ID = 'LEG_ID'
    CASHFLOW_ID = 'CASHFLOW_ID'
    FIXING_DATE = 'FIXING_DATE'
    START_DATE = 'START_DATE'
    END_DATE = 'END_DATE'
    ACCRUED = 'ACCRUED'
    PAY_DATE = 'PAY_DATE'
    INDEX_OR_FIXED = 'INDEX_OR_FIXED'
    INDEX_VALUE = 'INDEX_VALUE'
    NOTIONAL = 'NOTIONAL'
    PAY_OR_RECEIVE = 'PAY_OR_RECEIVE' # pay : -1 , receive : 1
    FORECASTED_AMOUNT = 'FORECASTED_AMOUNT'
    PV = 'PV'
    DF = 'DISCOUNG FACTOR'

    @classmethod
    def from_string(cls, value: str) -> 'CFReportColumns':
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        try:
            return cls(value.upper())
        except ValueError:
            raise ValueError(f"Invalid token: {value}")

    def to_string(self) -> str:
        return self.value


class CashflowsReport:

    def __init__(self) -> None:
        self.leg_id_tracker_ = {}
        self.content_ = []
        self.schema_ = [ \
            CFReportColumns.PRODUCT_TYPE.to_string(),
            CFReportColumns.VALUATION_ENGINE_TYPE.to_string(),
            CFReportColumns.LEG_ID.to_string(),
            CFReportColumns.CASHFLOW_ID.to_string(),
            CFReportColumns.PAY_OR_RECEIVE.to_string(),
            CFReportColumns.NOTIONAL.to_string(),
            CFReportColumns.PAY_DATE.to_string(),
            CFReportColumns.FORECASTED_AMOUNT.to_string(),
            CFReportColumns.PV.to_string(),
            CFReportColumns.DF.to_string()
            ]
        
    def add_row(self,
                leg_id : int,
                prod_type : str,
                val_engine_type : str,
                notional : float,
                pay_or_rec : float,
                pay_date : Date,
                forecasted_amount : float,
                pv : float,
                df : float,
                fixing_date : Optional[Date]=None,
                start_date : Optional[Date]=None,
                end_date :  Optional[Date]=None,
                accrued : Optional[float]=None,
                index_or_fixed : Optional[float|str]=None,
                index_value : Optional[float]=None) -> None:

        this_row = []
        
        # sort out index
        cur_cf_id = self.leg_id_tracker_.setdefault(leg_id, 0)

        # mandatory field
        this_row = [
            prod_type,
            val_engine_type,
            leg_id,
            cur_cf_id,
            pay_or_rec,
            notional,
            pay_date,
            forecasted_amount,
            pv,
            df]

        # process optional field
        optional_pairs = [
            (CFReportColumns.FIXING_DATE.to_string(), fixing_date),
            (CFReportColumns.START_DATE.to_string(), start_date),
            (CFReportColumns.END_DATE.to_string(), end_date),
            (CFReportColumns.ACCRUED.to_string(), accrued),
            (CFReportColumns.INDEX_OR_FIXED.to_string(), index_or_fixed),
            (CFReportColumns.INDEX_VALUE.to_string(), index_value),
        ]

        # process optional field
        if len(self.content_) == 0:
            for col, val in optional_pairs:
                if val is not None:
                    self.schema_.append(col)
                    this_row.append(val)
        else:
            schema_set = set(self.schema_)
            for col, val in optional_pairs:
                if col in schema_set:
                    this_row.append(val)
        
        # consistency validation
        if len(self.content_) != 0:
            assert len(self.content_[0]) == len(this_row)

        # finalized
        self.content_.append(this_row)
        self.leg_id_tracker_[leg_id] += 1

    def display(self):
        return pd.DataFrame(self.content_, columns=self.schema_)
    
    @property
    def content(self) -> List:
        return self.content_

    @property
    def schema(self) -> List:
        return self.schema_