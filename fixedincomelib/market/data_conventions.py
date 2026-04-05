from abc import ABC
from enum import Enum
import pandas as pd
from fixedincomelib.date import *
from fixedincomelib.market.registries import *
from fixedincomelib.market.basics import AccrualBasis, BusinessDayConvention, HolidayConvention


class CompoundingMethod(Enum):

    SIMPLE = "simple"
    ARITHMETIC = "arithmetic"
    COMPOUND = "compound"

    @classmethod
    def from_string(cls, value: str) -> "CompoundingMethod":
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid token: {value}")

    def to_string(self) -> str:
        return self.value


### interface
class DataConvention(ABC):

    _type = ""

    def __init__(self, unique_name: str, type: str, content: dict):
        super().__init__()
        self.conv_name = unique_name.upper()
        self.conv_type = type.upper()
        self.content = content
        assert len(self.content) != 0

    @property
    def name(self):
        return self.conv_name

    @classmethod
    def type(cls):
        return cls._type

    def display(self):
        to_print = []
        for k, v in self.content.items():
            k_ = k
            if k_.endswith("_"):
                k_ = k[:-1]
            to_print.append([k_.upper(), v])
        return pd.DataFrame(to_print, columns=["Name", "Value"])


### specific examples
class DataConventionRFRFuture(DataConvention):

    _type = "RFR FUTURE"

    def __init__(self, unique_name, content):

        if len(content) != 9:
            raise ValueError(f"{unique_name}: content should have 9 fields, got {len(content)}")

        self.index_ = None
        self.accrual_basis_ = None
        self.accrual_period_ = None
        self.payment_offset_ = None
        self.payment_business_day_conv_ = None
        self.payment_holiday_conv_ = None
        self.compounding_method_ = None
        self.contractual_notional_ = None
        self.basis_point_ = None

        upper_content = {k.upper(): v for k, v in content.items()}
        for k, v in upper_content.items():
            if k.upper() == "INDEX":
                self.index_ = v
            elif k == "ACCRUAL_BASIS":
                self.accrual_basis_ = v
            elif k == "ACCRUAL_PERIOD":
                self.accrual_period_ = v
            elif k == "PAYMENT_OFFSET":
                self.payment_offset_ = v
            elif k == "PAYMENT_BUSINESS_DAY_CONVENTION":
                self.payment_business_day_convention_ = v
            elif k == "PAYMENT_HOLIDAY_CONVENTION":
                self.payment_holiday_convention_ = v
            elif k == "CONTRACTUAL_NOTIONAL":
                self.contractual_notional_ = float(v)
            elif k == "BASIS_POINT":
                self.basis_point_ = float(v)
            elif k == "COMPOUNDING_METHOD":
                self.compounding_method_ = v

        super().__init__(unique_name, DataConventionRFRFuture._type, self.__dict__.copy())

    @property
    def index(self) -> ql.QuantLib.OvernightIndex:
        return IndexRegistry().get(self.index_)

    @property
    def index_str(self) -> str:
        return self.index_

    @property
    def acc_basis(self) -> AccrualBasis:
        return AccrualBasis(self.accrual_basis_)

    @property
    def acc_period(self) -> Period:
        return Period(self.accrual_period_)

    @property
    def payment_offset(self) -> Period:
        return Period(self.payment_offset_)

    @property
    def business_day_convention(self) -> BusinessDayConvention:
        return BusinessDayConvention(self.payment_business_day_convention_)

    @property
    def holiday_convention(self) -> HolidayConvention:
        return HolidayConvention(self.payment_holiday_convention_)

    @property
    def contractual_notional(self) -> float:
        return self.contractual_notional_

    @property
    def basis_point(self) -> float:
        return self.basis_point_

    @property
    def compounding_method(self) -> CompoundingMethod:
        return self.compounding_method_


class DataConventionRFRSwap(DataConvention):

    _type = "RFR SWAP"

    def __init__(self, unique_name, content):

        if len(content) != 7:
            raise ValueError(f"{unique_name}: content should have 7 fields, got {len(content)}")

        self.index_ = None
        self.accrual_basis_ = None
        self.accrual_period_ = None
        self.payment_offset_ = None
        self.payment_business_day_convention_ = None
        self.payment_holiday_convention_ = None
        self.ois_compounding_ = None

        upper_content = {k.upper(): v for k, v in content.items()}
        for k, v in upper_content.items():
            if k.upper() == "INDEX":
                self.index_ = v
            elif k == "ACCRUAL_BASIS":
                self.accrual_basis_ = v
            elif k == "ACCRUAL_PERIOD":
                self.accrual_period_ = v
            elif k == "PAYMENT_OFFSET":
                self.payment_offset_ = v
            elif k == "PAYMENT_BUSINESS_DAY_CONVENTION":
                self.payment_business_day_convention_ = v
            elif k == "PAYMENT_HOLIDAY_CONVENTION":
                self.payment_holiday_convention_ = v
            elif k == "COMPOUNDING_METHOD":
                self.compounding_method_ = v

        super().__init__(unique_name, DataConventionRFRSwap._type, self.__dict__.copy())

    @property
    def index(self) -> ql.QuantLib.OvernightIndex:
        return IndexRegistry().get(self.index_)

    @property
    def index_str(self) -> str:
        return self.index_

    @property
    def acc_basis(self) -> AccrualBasis:
        return AccrualBasis(self.accrual_basis_)

    @property
    def acc_period(self) -> Period:
        return Period(self.accrual_period_)

    @property
    def payment_offset(self) -> Period:
        return Period(self.payment_offset_)

    @property
    def business_day_convention(self) -> BusinessDayConvention:
        return BusinessDayConvention(self.payment_business_day_convention_)

    @property
    def holiday_convention(self) -> HolidayConvention:
        return HolidayConvention(self.payment_holiday_convention_)

    @property
    def compounding_method(self) -> CompoundingMethod:
        return self.compounding_method_


class DataConventionOvernightIndexBasisSwap(DataConvention):

    _type = "OVERNIGHT INDEX BASIS SWAP"

    def __init__(self, unique_name, content):

        if len(content) != 9:
            raise ValueError(f"{unique_name}: content should have 7 fields, got {len(content)}")

        self.index_1_ = None
        self.index_2_ = None
        self.accrual_basis_ = None
        self.accrual_period_1_ = None
        self.accrual_period_2_ = None
        self.payment_offset_ = None
        self.payment_business_day_convention_ = None
        self.payment_holiday_convention_ = None
        self.ois_compounding_ = None

        upper_content = {k.upper(): v for k, v in content.items()}
        for k, v in upper_content.items():
            if k.upper() == "BASIS_OI_INDEX":
                self.index_1_ = v
            elif k.upper() == "REFERENCE_OI_INDEX":
                self.index_2_ = v
            elif k == "ACCRUAL_BASIS":
                self.accrual_basis_ = v
            elif k == "ACCRUAL_PERIOD_1":
                self.accrual_period_1_ = v
            elif k == "ACCRUAL_PERIOD_2":
                self.accrual_period_2_ = v
            elif k == "PAYMENT_OFFSET":
                self.payment_offset_ = v
            elif k == "PAYMENT_BUSINESS_DAY_CONVENTION":
                self.payment_business_day_convention_ = v
            elif k == "PAYMENT_HOLIDAY_CONVENTION":
                self.payment_holiday_convention_ = v
            elif k == "COMPOUNDING_METHOD":
                self.compounding_method_ = v

        super().__init__(unique_name, DataConventionRFRSwap._type, self.__dict__.copy())

    @property
    def index_1(self) -> ql.QuantLib.OvernightIndex:
        return IndexRegistry().get(self.index_1_)

    @property
    def index_2(self) -> ql.QuantLib.OvernightIndex:
        return IndexRegistry().get(self.index_2_)

    @property
    def index_1_str(self) -> str:
        return self.index_1_

    @property
    def index_2_str(self) -> str:
        return self.index_2_

    @property
    def acc_basis(self) -> AccrualBasis:
        return AccrualBasis(self.accrual_basis_)

    @property
    def acc_period_1(self) -> Period:
        return Period(self.accrual_period_1_)

    @property
    def acc_period_2(self) -> Period:
        return Period(self.accrual_period_2_)

    @property
    def payment_offset(self) -> Period:
        return Period(self.payment_offset_)

    @property
    def business_day_convention(self) -> BusinessDayConvention:
        return BusinessDayConvention(self.payment_business_day_convention_)

    @property
    def holiday_convention(self) -> HolidayConvention:
        return HolidayConvention(self.payment_holiday_convention_)

    @property
    def compounding_method(self) -> CompoundingMethod:
        return self.compounding_method_


class DataConventionRFRSwaption(DataConvention):

    _type = "RFR SWAPTION"

    def __init__(self, unique_name, content):

        if len(content) != 4:
            raise ValueError(f"{unique_name}: content should have 4 fields, got {len(content)}")

        self.index_ = None
        self.payment_offset_ = None
        self.payment_business_day_convention_ = None
        self.payment_holiday_convention_ = None

        upper_content = {k.upper(): v for k, v in content.items()}
        for k, v in upper_content.items():
            if k.upper() == "INDEX":
                self.index_ = v
            elif k == "PAYMENT_OFFSET":
                self.payment_offset_ = v
            elif k == "PAYMENT_BUSINESS_DAY_CONVENTION":
                self.payment_business_day_convention_ = v
            elif k == "PAYMENT_HOLIDAY_CONVENTION":
                self.payment_holiday_convention_ = v

        super().__init__(unique_name, DataConventionRFRSwaption._type, self.__dict__.copy())

    @property
    def index(self) -> ql.QuantLib.OvernightIndex:
        return IndexRegistry().get(self.index_)

    @property
    def index_str(self) -> str:
        return self.index_

    @property
    def payment_offset(self) -> Period:
        return Period(self.payment_offset_)

    @property
    def business_day_convention(self) -> BusinessDayConvention:
        return BusinessDayConvention(self.payment_business_day_convention_)

    @property
    def holiday_convention(self) -> HolidayConvention:
        return HolidayConvention(self.payment_holiday_convention_)


class DataConventionRFRCapFloor(DataConvention):

    _type = "RFR CAPFLOOR"

    def __init__(self, unique_name, content):

        if len(content) != 4:
            raise ValueError(f"{unique_name}: content should have 4 fields, got {len(content)}")

        self.index_ = None
        self.payment_offset_ = None
        self.payment_business_day_convention_ = None
        self.payment_holiday_convention_ = None

        upper_content = {k.upper(): v for k, v in content.items()}
        for k, v in upper_content.items():
            if k.upper() == "INDEX":
                self.index_ = v
            elif k == "PAYMENT_OFFSET":
                self.payment_offset_ = v
            elif k == "PAYMENT_BUSINESS_DAY_CONVENTION":
                self.payment_business_day_convention_ = v
            elif k == "PAYMENT_HOLIDAY_CONVENTION":
                self.payment_holiday_convention_ = v

        super().__init__(unique_name, DataConventionRFRSwaption._type, self.__dict__.copy())

    @property
    def index(self) -> ql.QuantLib.OvernightIndex:
        return IndexRegistry().get(self.index_)

    @property
    def index_str(self) -> str:
        return self.index_

    @property
    def payment_offset(self) -> Period:
        return Period(self.payment_offset_)

    @property
    def business_day_convention(self) -> BusinessDayConvention:
        return BusinessDayConvention(self.payment_business_day_convention_)

    @property
    def holiday_convention(self) -> HolidayConvention:
        return HolidayConvention(self.payment_holiday_convention_)


class DataConventionJump(DataConvention):

    _type = "JUMP"

    def __init__(self, unique_name, content):

        if len(content) != 2:
            raise ValueError(f"{unique_name}: content should have 2 fields, got {len(content)}")

        self.index_ = None
        self.jupm_size_ = 1e4

        upper_content = {k.upper(): v for k, v in content.items()}
        for k, v in upper_content.items():
            if k.upper() == "INDEX":
                self.index_ = v
            elif k == "JUMP_SIZE":
                self.jupm_size_ = v

        super().__init__(unique_name, DataConventionJump._type, self.__dict__.copy())

    @property
    def index(self) -> ql.Index:
        return IndexRegistry().get(self.index_)

    @property
    def jump_size(self):
        return self.jupm_size_


class DataConventionIFR(DataConvention):

    _type = "INSTANTANEOUS FORWARD RATE"

    def __init__(self, unique_name, content):

        if len(content) != 3:
            raise ValueError(f"{unique_name}: content should have 3 fields, got {len(content)}")

        self.index_ = None

        upper_content = {k.upper(): v for k, v in content.items()}
        for k, v in upper_content.items():
            if k.upper() == "INDEX":
                self.index_ = v
            elif k == "BUSINESS_DAY_CONVENTION":
                self.business_day_convention_ = v
            elif k == "HOLIDAY_CONVENTION":
                self.holiday_convention_ = v

        super().__init__(unique_name, DataConventionIFR._type, self.__dict__.copy())

    @property
    def index(self) -> ql.Index:
        return IndexRegistry().get(self.index_)

    @property
    def business_day_convention(self) -> BusinessDayConvention:
        return BusinessDayConvention(self.business_day_convention_)

    @property
    def holiday_convention(self) -> HolidayConvention:
        return HolidayConvention(self.holiday_convention_)


class DataConventionZeroSpread(DataConvention):

    _type = "ZERO SPREAD"

    def __init__(self, unique_name, content):

        if len(content) != 3:
            raise ValueError(f"{unique_name}: content should have 3 fields, got {len(content)}")

        self.index_ = None

        upper_content = {k.upper(): v for k, v in content.items()}
        for k, v in upper_content.items():
            if k.upper() == "INDEX":
                self.index_ = v
            elif k == "BUSINESS_DAY_CONVENTION":
                self.business_day_convention_ = v
            elif k == "HOLIDAY_CONVENTION":
                self.holiday_convention_ = v

        super().__init__(unique_name, DataConventionZeroSpread._type, self.__dict__.copy())

    @property
    def index(self) -> ql.Index:
        return IndexRegistry().get(self.index_)

    @property
    def index_str(self) -> str:
        return self.index_

    @property
    def business_day_convention(self) -> BusinessDayConvention:
        return BusinessDayConvention(self.business_day_convention_)

    @property
    def holiday_convention(self) -> HolidayConvention:
        return HolidayConvention(self.holiday_convention_)


class DataConventionBondFixed(DataConvention):

    _type = "BOND FIXED"

    def __init__(self, unique_name, content):

        self.bond_issuer_ = None
        self.currency_ = None
        self.bond_type_ = None
        self.bond_coupon_type_ = None
        self.principal_ = None
        self.settlement_offset_ = None
        self.coupon_accrual_period_ = None
        self.coupon_accrual_convention_ = None
        self.roll_convention_ = None
        self.payment_business_day_convention_ = None
        self.payment_holiday_convention_ = None

        upper_content = {k.upper(): v for k, v in content.items()}

        for k, v in upper_content.items():
            
            if k == "BOND_ISSUER":
                self.bond_issuer_ = v
            elif k == "CURRENCY":
                self.currency_ = v
            elif k == "BOND_TYPE":
                self.bond_type_ = v
            elif k == "BOND_COUPON_TYPE":
                self.bond_coupon_type_ = v
            elif k == "PRINCIPAL":
                self.principal_ = float(v)
            elif k == "SETTLEMENT_OFFSET":
                self.settlement_offset_ = v
            elif k == "COUPON_ACCRUAL_PERIOD":
                self.coupon_accrual_period_ = v
            elif k == "COUPON_ACCRUAL_CONVENTION":
                self.coupon_accrual_convention_ = v
            elif k == "ROLL_CONVENTION":
                self.roll_convention_ = v
            elif k == "PAYMENT_BUSINESS_DAY_CONVENTION":
                self.payment_business_day_convention_ = v
            elif k == "PAYMENT_HOLIDAY_CONVENTION":
                self.payment_holiday_convention_ = v

        super().__init__(unique_name, DataConventionBondFixed._type, self.__dict__.copy())

    @property
    def bond_issuer(self) -> str:
        return self.bond_issuer_

    @property
    def bond_type(self) -> str:
        return self.bond_type_

    @property
    def bond_coupon_type(self) -> str:
        return self.bond_coupon_type_

    @property
    def principal(self) -> float:
        return self.principal_

    @property
    def roll_convention(self) -> str:
        return self.roll_convention_

    @property
    def yield_calculation_dates(self) -> str:
        return self.yield_calculation_dates_

    @property
    def yield_first_period_calculation_type(self) -> str:
        return self.yield_first_period_calculation_type_

    @property
    def yield_last_period_calculation_type(self) -> str:
        return self.yield_last_period_calculation_type_

    @property
    def yield_regular_period_calculation_type(self) -> str:
        return self.yield_regular_period_calculation_type_

    @property
    def accrued_first_period_convention(self) -> str:
        return self.accrued_first_period_convention_

    @property
    def accrued_last_period_convention(self) -> str:
        return self.accrued_last_period_convention_

    @property
    def accrued_regular_period_convention(self) -> str:
        return self.accrued_regular_period_convention_

    @property
    def accrued_rounding_precision(self) -> int:
        return self.accrued_rounding_precision_

    @property
    def accrued_rounding_units(self) -> int:
        return self.accrued_rounding_units_

    @property
    def accrued_rounding_convention(self) -> str:
        return self.accrued_rounding_convention_

    @property
    def price_rounding_precision(self) -> int:
        return self.price_rounding_precision_

    @property
    def price_rounding_units(self) -> int:
        return self.price_rounding_units_

    @property
    def price_rounding_convention(self) -> str:
        return self.price_rounding_convention_

    @property
    def yield_rounding_precision(self) -> int:
        return self.yield_rounding_precision_

    @property
    def yield_rounding_units(self) -> int:
        return self.yield_rounding_units_

    @property
    def yield_rounding_convention(self) -> str:
        return self.yield_rounding_convention_

    @property
    def currency(self) -> Currency:
        return Currency(self.currency_)

    @property
    def settlement_offset(self) -> Period:
        return self.settlement_offset_

    @property
    def coupon_accrual_period(self) -> Period:
        return Period(self.coupon_accrual_period_)

    @property
    def yield_compound_period(self) -> Period:
        return Period(self.yield_compound_period_)

    @property
    def coupon_accrual_convention(self) -> AccrualBasis:
        return AccrualBasis(self.coupon_accrual_convention_)

    @property
    def yield_first_period_accrual_convention(self) -> AccrualBasis:
        return AccrualBasis(self.yield_first_period_accrual_convention_)

    @property
    def yield_last_period_accrual_convention(self) -> AccrualBasis:
        return AccrualBasis(self.yield_last_period_accrual_convention_)

    @property
    def yield_regular_period_accrual_convention(self) -> AccrualBasis:
        return AccrualBasis(self.yield_regular_period_accrual_convention_)

    @property
    def settlement_business_day_convention(self) -> BusinessDayConvention:
        return BusinessDayConvention(self.settlement_business_day_convention_)

    @property
    def accrual_business_day_convention(self) -> BusinessDayConvention:
        return BusinessDayConvention(self.accrual_business_day_convention_)

    @property
    def payment_business_day_convention(self) -> BusinessDayConvention:
        return BusinessDayConvention(self.payment_business_day_convention_)

    @property
    def settlement_holiday_convention(self) -> HolidayConvention:
        return HolidayConvention(self.settlement_holiday_convention_)

    @property
    def payment_holiday_convention(self) -> HolidayConvention:
        return HolidayConvention(self.payment_holiday_convention_)

    @property
    def accrued_first_period_accrual_convention(self) -> AccrualBasis:
        return AccrualBasis(self.accrued_first_period_accrual_convention_)

    @property
    def accrued_last_period_accrual_convention(self) -> AccrualBasis:
        return AccrualBasis(self.accrued_last_period_accrual_convention_)

    @property
    def accrued_regular_period_accrual_convention(self) -> AccrualBasis:
        return AccrualBasis(self.accrued_regular_period_accrual_convention_)

    @property
    def ex_interest_period(self) -> Period:
        return Period(self.ex_interest_period_)

    @property
    def end_of_month(self) -> bool:
        return self.roll_convention_ == "EOM"


class DataConventionFxPair(DataConvention):

    _type = "FX PAIR"

    def __init__(self, unique_name, content):

        if len(content) != 1:
            raise ValueError(f"{unique_name}: content should have 3 fields, got {len(content)}")

        self.index_ = None

        upper_content = {k.upper(): v for k, v in content.items()}
        for k, v in upper_content.items():
            if k.upper() == "INDEX":
                self.index_ = v

        super().__init__(unique_name, DataConventionZeroSpread._type, self.__dict__.copy())

    @property
    def index(self) -> ql.Index:
        return IndexRegistry().get(self.index_)

    @property
    def index_str(self) -> str:
        return self.index_


### registry
DataConventionRegFunction().register(DataConventionRFRFuture._type, DataConventionRFRFuture)
DataConventionRegFunction().register(DataConventionRFRSwap._type, DataConventionRFRSwap)
DataConventionRegFunction().register(
    DataConventionOvernightIndexBasisSwap._type, DataConventionOvernightIndexBasisSwap
)
DataConventionRegFunction().register(DataConventionRFRSwaption._type, DataConventionRFRSwaption)
DataConventionRegFunction().register(DataConventionRFRCapFloor._type, DataConventionRFRCapFloor)
DataConventionRegFunction().register(DataConventionJump._type, DataConventionJump)
DataConventionRegFunction().register(DataConventionIFR._type, DataConventionIFR)
DataConventionRegFunction().register(DataConventionZeroSpread._type, DataConventionZeroSpread)

# Bond
DataConventionRegFunction().register(DataConventionBondFixed._type, DataConventionBondFixed)
DataConventionRegFunction().register(DataConventionFxPair._type, DataConventionFxPair)
