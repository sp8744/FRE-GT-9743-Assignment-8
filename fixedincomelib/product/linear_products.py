from calendar import Calendar
import enum
from webbrowser import get

# from matplotlib import ticker
import pandas as pd
from typing import List, Optional, Union
from dataclasses import dataclass
import QuantLib as ql
import numpy as np
from fixedincomelib.date.utilities import add_period, frequency_from_period
from fixedincomelib.market.basics import *
from fixedincomelib.market.registries import IndexRegistry, DataConventionRegistry
from fixedincomelib.market.data_conventions import (
    CompoundingMethod,
    DataConventionBondFixed,
    DataConventionRFRFuture,
)
from fixedincomelib.market.indices import FXIndex
from fixedincomelib.market.data_conventions import CompoundingMethod, DataConventionRFRFuture
from fixedincomelib.market import (
    Currency,
    AccrualBasis,
    BusinessDayConvention,
    HolidayConvention,
    DataConventionRegistry,
    IndexRegistry,
    DataConventionRFRFuture,
)
from fixedincomelib.product.utilities import LongOrShort, PayOrReceive
from fixedincomelib.product.product_interfaces import (
    Product,
    ProductVisitor,
    ProductBuilderRegistry,
)
from fixedincomelib.date import Date, Period, TermOrTerminationDate, make_schedule, accrued
from fixedincomelib.product.product_portfolio import ProductPortfolio
from fixedincomelib.market.bond_specs import BondSpecsRegistry, BondSpecs


class ProductBulletCashflow(Product):

    _version = 1
    _product_type = "PRODUCT_BULLET_CASHFLOW"

    def __init__(
        self,
        termination_date: Date,
        currency: Currency,
        notional: float,
        long_or_short: LongOrShort,
        payment_date: Optional[Date] = None,
    ) -> None:

        super().__init__()
        self.first_date_ = termination_date
        self.long_or_short_ = long_or_short
        self.notional_ = notional
        self.currency_ = currency
        self.payment_date_ = payment_date
        if self.payment_date_ is None:
            self.payment_date_ = termination_date
        self.last_date_ = self.payment_date_

    @property
    def termination_date(self) -> Date:
        return self.last_date

    @property
    def payment_date(self) -> Date:
        return self.payment_date_

    def accept(self, visitor: ProductVisitor):
        return visitor.visit(self)

    def serialize(self) -> dict:
        content = {}
        content["VERSION"] = self._version
        content["TYPE"] = self._product_type
        content["TERMINATION_DATE"] = self.termination_date.ISO()
        content["PAYMENT_DATE"] = self.payment_date.ISO()
        content["LONG_OR_SHORT"] = self.long_or_short.to_string().upper()
        content["NOTIONAL"] = self.notional
        content["CURRENCY"] = self.currency.value_str
        return content

    @classmethod
    def deserialize(cls, input_dict) -> "ProductBulletCashflow":
        termination_date = Date(input_dict["TERMINATION_DATE"])
        payment_date = Date(input_dict["PAYMENT_DATE"])
        long_or_short = LongOrShort.from_string(input_dict["LONG_OR_SHORT"])
        notional = float(input_dict["NOTIONAL"])
        currency = Currency(input_dict["CURRENCY"])
        return cls(termination_date, currency, notional, long_or_short, payment_date)


class ProductFixedAccrued(Product):

    _version = 1
    _product_type = "PRODUCT_FIXED_ACCRUED"

    def __init__(
        self,
        effective_date: Date,
        termination_date: Date,
        currency: Currency,
        notional: float,
        accrual_basis: AccrualBasis,
        payment_date: Optional[Date] = None,
        business_day_convention: Optional[BusinessDayConvention] = BusinessDayConvention("F"),
        holiday_convention: Optional[HolidayConvention] = HolidayConvention("USGS"),
    ) -> None:

        super().__init__()
        self.effective_date_ = self.first_date_ = effective_date
        self.termination_date_ = termination_date
        self.long_or_short_ = LongOrShort.LONG if notional >= 0 else LongOrShort.SHORT
        self.notional_ = notional
        self.currency_ = currency
        self.accrual_basis_ = accrual_basis
        self.business_day_convention_ = business_day_convention
        self.holiday_convention_ = holiday_convention
        self.payment_date_ = self.termination_date_
        if payment_date is not None:
            self.payment_date_ = payment_date
        self.last_date_ = self.payment_date_
        # calc accrued
        self.accrued_ = accrued(
            self.effective_date_,
            self.termination_date_,
            self.accrual_basis_,
            self.business_day_convention_,
            self.holiday_convention_,
        )

    @property
    def effective_date(self) -> Date:
        return self.effective_date_

    @property
    def termination_date(self) -> Date:
        return self.termination_date_

    @property
    def accrual_basis(self) -> AccrualBasis:
        return self.accrual_basis_

    @property
    def payment_date(self) -> Date:
        return self.payment_date_

    @property
    def business_day_convention(self) -> BusinessDayConvention:
        return self.business_day_convention_

    @property
    def holiday_convention(self) -> HolidayConvention:
        return self.holiday_convention_

    @property
    def accrued(self) -> float:
        return self.accrued_

    def accept(self, visitor: ProductVisitor):
        return visitor.visit(self)

    def serialize(self) -> dict:
        content = {}
        content["VERSION"] = self._version
        content["TYPE"] = self._product_type
        content["EFFECTIVE_DATE"] = self.effective_date.ISO()
        content["TERMINATION_DATE"] = self.termination_date.ISO()
        content["PAYMENT_DATE"] = self.payment_date.ISO()
        content["ACCRUAL_BASIS"] = self.accrual_basis.value_str
        content["BUSINESS_DAY_CONVENTION"] = self.business_day_convention.value_str
        content["HOLIDAY_CONVENTION"] = self.holiday_convention_.value_str
        content["NOTIONAL"] = self.notional
        content["CURRENCY"] = self.currency.ccy.code()
        return content

    @classmethod
    def deserialize(cls, input_dict) -> "ProductFixedAccrued":
        effective_date = Date(input_dict["EFFECTIVE_DATE"])
        termination_date = Date(input_dict["TERMINATION_DATE"])
        payment_date = Date(input_dict["PAYMENT_DATE"])
        accrual_basis = AccrualBasis(input_dict["ACCRUAL_BASIS"])
        business_day_convention = BusinessDayConvention(input_dict["BUSINESS_DAY_CONVENTION"])
        holiday_convention = HolidayConvention(input_dict["HOLIDAY_CONVENTION"])
        notional = float(input_dict["NOTIONAL"])
        currency = Currency(input_dict["CURRENCY"])
        return cls(
            effective_date,
            termination_date,
            currency,
            notional,
            accrual_basis,
            payment_date,
            business_day_convention,
            holiday_convention,
        )


class ProductOvernightIndexCashflow(Product):

    _version = 1
    _product_type = "PRODUCT_OVERNIGHT_INDEX_CASHFLOW"

    def __init__(
        self,
        effective_date: Date,
        term_or_termination_date: TermOrTerminationDate,
        on_index: str,
        compounding_method: CompoundingMethod,
        spread: float,
        notional: float,
        payment_date: Optional[Date] = None,
    ) -> None:

        super().__init__()

        # get index
        self.on_index_str_ = on_index
        self.on_index_: ql.QuantLib.OvernightIndex = IndexRegistry().get(self.on_index_str_)
        # sort out date
        self.first_date_ = self.effective_date_ = effective_date
        self.termination_date_ = term_or_termination_date.get_date()
        if term_or_termination_date.is_term():
            calendar: ql.QuantLib.Calendar = self.on_index_.fixingCalendar()
            self.termination_date_ = Date(
                calendar.advance(
                    self.effective_date_,
                    term_or_termination_date.get_term(),
                    self.on_index.businessDayConvention(),
                )
            )  # need to find a way to get biz_day_conv from index
        self.paymentDate_ = self.termination_date_ if payment_date is None else payment_date
        self.last_date_ = self.paymentDate_
        # other attributes
        self.notional_ = notional
        self.long_or_short_ = LongOrShort.LONG if notional >= 0 else LongOrShort.SHORT
        self.compounding_method_ = compounding_method
        self.spread_ = spread
        self.currency_ = Currency(self.on_index_.currency().code())

    @property
    def on_index(self) -> ql.QuantLib.OvernightIndex:
        return self.on_index_

    @property
    def compounding_method(self) -> CompoundingMethod:
        return self.compounding_method_

    @property
    def effective_date(self) -> Date:
        return self.effective_date_

    @property
    def termination_date(self) -> Date:
        return self.termination_date_

    @property
    def spread(self) -> float:
        return self.spread_

    @property
    def payment_date(self) -> Date:
        return self.paymentDate_

    def accept(self, visitor: ProductVisitor):
        return visitor.visit(self)

    def serialize(self) -> dict:
        content = {}
        content["VERSION"] = self._version
        content["TYPE"] = self._product_type
        content["EFFECTIVE_DATE"] = self.effective_date.ISO()
        content["TERMINATION_DATE"] = self.termination_date.ISO()
        content["PAYMENT_DATE"] = self.payment_date.ISO()
        content["ON_INDEX"] = self.on_index_str_
        content["SPREAD"] = self.spread
        content["COMPOUNDING_METHOD"] = self.compounding_method.to_string().upper()
        content["NOTIONAL"] = self.notional
        return content

    @classmethod
    def deserialize(cls, input_dict) -> "ProductOvernightIndexCashflow":
        effective_date = Date(input_dict["EFFECTIVE_DATE"])
        termination_date = TermOrTerminationDate(input_dict["TERMINATION_DATE"])
        payment_date = Date(input_dict["PAYMENT_DATE"])
        on_index = input_dict["ON_INDEX"]
        spread = float(input_dict["SPREAD"])
        compounding_method = CompoundingMethod.from_string(input_dict["COMPOUNDING_METHOD"])
        notional = float(input_dict["NOTIONAL"])
        return cls(
            effective_date,
            termination_date,
            on_index,
            compounding_method,
            spread,
            notional,
            payment_date,
        )


class ProductRFRFuture(Product):

    _version = 1
    _product_type = "PRODUCT_RFR_FUTURE"

    def __init__(
        self,
        effective_date: Date,
        term_or_termination_date: TermOrTerminationDate,
        future_conv: str,
        long_or_short: LongOrShort,
        amount: float,
        strike: Optional[float] = 0.0,
    ) -> None:

        super().__init__()

        # resolve index and convention
        self.future_conv_: DataConventionRFRFuture = DataConventionRegistry().get(future_conv)
        self.on_index_: ql.QuantLib.OvernightIndex = self.future_conv.index
        # sort out dates
        self.first_date_ = self.effective_date_ = Date(effective_date)
        self.termination_date_ = term_or_termination_date.get_date()
        if term_or_termination_date.is_term():
            calendar = self.on_index_.fixingCalendar()
            self.termination_date_ = Date(
                calendar.advance(
                    self.effective_date_,
                    term_or_termination_date.get_term(),
                    self.on_index_.businessDayConvention(),
                )
            )
        self.last_date_ = self.termination_date_
        # other attributes
        self.strike_ = strike
        self.long_or_short_ = long_or_short
        self.currency_ = Currency(self.on_index_.currency().code())
        self.amount_ = amount
        self.contractual_notional_ = self.future_conv_.contractual_notional
        self.basis_point_ = self.future_conv_.basis_point
        self.notional_ = amount * self.contractual_notional_ * self.basis_point_

    @property
    def effective_date(self) -> Date:
        return self.effective_date_

    @property
    def termination_date(self) -> Date:
        return self.termination_date_

    @property
    def strike(self) -> float:
        return self.strike_

    @property
    def future_conv(self) -> DataConventionRFRFuture:
        return self.future_conv_

    @property
    def contractual_notional(self) -> float:
        return self.contractual_notional_

    @property
    def notional(self) -> float:
        return self.notional_

    @property
    def basis_point(self) -> float:
        return self.basis_point_

    @property
    def on_index(self) -> ql.QuantLib.OvernightIndex:
        return self.on_index_

    @property
    def currency(self):
        return self.currency_

    @property
    def long_or_short(self):
        return self.long_or_short_

    @property
    def amount(self) -> float:
        return self.amount_

    def accept(self, visitor: ProductVisitor):
        return visitor.visit(self)

    def serialize(self) -> dict:
        content = {}
        content["VERSION"] = self._version
        content["TYPE"] = self._product_type
        content["EFFECTIVE_DATE"] = self.effective_date.ISO()
        content["TERMINATION_DATE"] = self.termination_date.ISO()
        content["FUTURE_CONVENTION"] = self.future_conv.name
        content["LONG_OR_SHORT"] = self.long_or_short.to_string().upper()
        content["AMOUNT"] = self.amount
        content["STRIKE"] = self.strike
        return content

    @classmethod
    def deserialize(cls, input_dict) -> "ProductRFRFuture":
        effective_date = Date(input_dict["EFFECTIVE_DATE"])
        termination_date = TermOrTerminationDate(input_dict["TERMINATION_DATE"])
        future_conv = input_dict["FUTURE_CONVENTION"]
        long_or_short = LongOrShort.from_string(input_dict["LONG_OR_SHORT"])
        amount = float(input_dict["AMOUNT"])
        strike = float(input_dict["STRIKE"])
        return cls(effective_date, termination_date, future_conv, long_or_short, amount, strike)


class InterestRateStream(ProductPortfolio):

    _version = 1
    _product_type = "PRODUCT_INTEREST_RATE_STREAM"

    def __init__(
        self,
        effective_date: Date,
        termination_date: Date,
        accrual_period: Period,
        notional: float,
        currency: Currency,
        accrual_basis: AccrualBasis,
        buseinss_day_convention: BusinessDayConvention,
        holiday_convention: HolidayConvention,
        float_index: Optional[str] = None,
        fixed_rate: Optional[float] = None,
        is_on_index: Optional[bool] = True,
        # has default values
        ois_compounding: Optional[CompoundingMethod] = CompoundingMethod.COMPOUND,
        ois_spread: Optional[float] = 0.0,
        fixing_in_arrear: Optional[bool] = True,
        payment_offset: Optional[Period] = Period("0D"),
        payment_business_day_convention: Optional[BusinessDayConvention] = BusinessDayConvention(
            "F"
        ),
        payment_holiday_convention: Optional[HolidayConvention] = HolidayConvention("USGS"),
        rule: Optional[str] = "BACKWARD",
        end_of_month: Optional[bool] = False,
    ):

        if float_index is None and fixed_rate is None:
            raise Exception("Cannot have both floating index and fixed rate invalid.")

        self.float_index_ = float_index
        self.fixed_rate_ = fixed_rate

        schedule = make_schedule(
            start_date=effective_date,
            end_date=termination_date,
            accrual_period=accrual_period,
            holiday_convention=holiday_convention,
            business_day_convention=buseinss_day_convention,
            accrual_basis=accrual_basis,
            rule=rule,
            end_of_month=end_of_month,
            fix_in_arrear=fixing_in_arrear,
            payment_offset=payment_offset,
            payment_business_day_convention=payment_business_day_convention,
            payment_holiday_convention=payment_holiday_convention,
        )

        products, weights = [], []
        for _, row in schedule.iterrows():
            if float_index:
                if not is_on_index:
                    # TODO : ibor
                    raise Exception("NOT IMPLEMENTED")
                else:
                    cf = ProductOvernightIndexCashflow(
                        row.StartDate,
                        TermOrTerminationDate(row.EndDate),
                        float_index,
                        ois_compounding,
                        ois_spread,
                        notional,
                        row.PaymentDate,
                    )
            else:
                cf = ProductFixedAccrued(
                    row.StartDate,
                    row.EndDate,
                    currency,
                    notional,
                    accrual_basis,
                    row.PaymentDate,
                    buseinss_day_convention,
                    holiday_convention,
                )

            products.append(cf)
            weights.append(1.0)

        super().__init__(products, weights)

    @property
    def float_index(self) -> Optional[str]:
        return self.float_index_

    @property
    def fixed_rate(self) -> Optional[float]:
        return self.fixed_rate_

    def cashflow(self, i: int) -> Product:
        return self.element(i)

    def num_cashflows(self) -> int:
        return self.num_elements_


class ProductRFRSwap(Product):

    _version = 1
    _product_type = "PRODUCT_RFR_SWAP"

    def __init__(
        self,
        effective_date: Date,
        term_or_termination_date: TermOrTerminationDate,
        payment_off_set: Period,
        on_index: str,
        fixed_rate: float,
        pay_or_rec: PayOrReceive,
        notional: float,
        accrual_period: Period,
        accrual_basis: AccrualBasis,
        floating_leg_accrual_period: Optional[Period] = None,
        pay_business_day_convention: Optional[BusinessDayConvention] = BusinessDayConvention("F"),
        pay_holiday_convention: Optional[HolidayConvention] = HolidayConvention("USGS"),
        spread: Optional[float] = 0.0,
        compounding_method: Optional[CompoundingMethod] = CompoundingMethod.COMPOUND,
    ) -> None:

        super().__init__()

        self.on_index_str_ = on_index
        self.on_index_: ql.QuantLib.OvernightIndex = IndexRegistry().get(self.on_index_str_)
        self.pay_business_day_convention_ = pay_business_day_convention
        self.pay_holiday_convention_ = pay_holiday_convention
        self.first_date_ = self.effective_date_ = effective_date
        self.term_or_termination_date_ = term_or_termination_date
        self.termination_date_ = self.term_or_termination_date_.get_date()
        if self.term_or_termination_date_.is_term():
            calendar = self.on_index_.fixingCalendar()
            self.termination_date_ = Date(
                calendar.advance(
                    self.effective_date_,
                    self.term_or_termination_date_.get_term(),
                    self.on_index_.businessDayConvention(),
                )
            )
        # other attributes
        self.currency_ = Currency(self.on_index_.currency().code())
        self.fixed_rate_ = fixed_rate
        self.notional_ = notional
        assert self.notional_ >= 0  # notional cannot be signed
        self.spread_ = spread
        self.pay_or_rec_ = pay_or_rec
        self.long_or_short_ = LongOrShort.LONG if notional > 0 else LongOrShort.SHORT
        self.pay_offset_ = payment_off_set
        self.accrual_basis_ = accrual_basis
        self.accrual_period_ = accrual_period
        self.floating_leg_accrual_period_ = (
            self.accrual_period_
            if floating_leg_accrual_period is None
            else floating_leg_accrual_period
        )
        self.compounding_method_ = compounding_method

        # floating leg
        self.floating_leg_ = InterestRateStream(
            effective_date=self.effective_date_,
            termination_date=self.termination_date_,
            accrual_period=self.floating_leg_accrual_period_,
            notional=self.notional_,
            currency=Currency(self.on_index_.currency().code()),
            accrual_basis=self.accrual_basis_,
            buseinss_day_convention=self.pay_business_day_convention_,  # not the best
            holiday_convention=HolidayConvention(self.on_index_.fixingCalendar().name()),
            float_index=on_index,
            ois_compounding=self.compounding_method_,
            ois_spread=spread,
            fixing_in_arrear=True,
            payment_offset=self.pay_offset_,
            payment_business_day_convention=self.pay_business_day_convention_,
            payment_holiday_convention=self.pay_holiday_convention_,
        )
        # fixed leg
        self.fixed_leg_ = InterestRateStream(
            effective_date=self.effective_date_,
            termination_date=self.termination_date_,
            accrual_period=self.accrual_period_,
            notional=self.notional_,
            currency=Currency(self.on_index_.currency().code()),
            accrual_basis=self.accrual_basis_,
            buseinss_day_convention=self.pay_business_day_convention_,
            holiday_convention=self.pay_holiday_convention_,
            fixed_rate=self.fixed_rate_,
            is_on_index=False,
            payment_offset=self.pay_offset_,
            payment_business_day_convention=self.pay_business_day_convention_,
            payment_holiday_convention=self.pay_holiday_convention_,
        )

        last_dt_fixed = self.fixed_leg_.last_date
        last_dt_floating = self.floating_leg_.last_date
        self.last_date_ = last_dt_fixed if last_dt_fixed >= last_dt_floating else last_dt_floating

    def floating_leg_cash_flow(self, i: int) -> Product:
        assert 0 <= i < self.floating_leg_.num_cashflows()
        return self.floating_leg_.element(i)

    def fixed_leg_cash_flow(self, i: int) -> Product:
        assert 0 <= i < self.fixed_leg_.num_cashflows()
        return self.fixed_leg_.element(i)

    @property
    def effective_date(self) -> Date:
        return self.effective_date_

    @property
    def termination_date(self) -> Date:
        return self.termination_date_

    @property
    def term_or_termination_date(self) -> Date:
        return self.term_or_termination_date_

    @property
    def pay_offset(self) -> Period:
        return self.pay_offset_

    @property
    def fixed_rate(self) -> float:
        return self.fixed_rate_

    @property
    def spread(self) -> float:
        return self.spread_

    @property
    def on_index(self) -> ql.QuantLib.OvernightIndex:
        return self.on_index_

    @property
    def pay_or_rec(self) -> PayOrReceive:
        return self.pay_or_rec_

    @property
    def compounding_method(self) -> CompoundingMethod:
        return self.compounding_method_

    @property
    def accrual_period(self) -> Period:
        return self.accrual_period_

    @property
    def floating_leg_accrual_period(self) -> Period:
        return self.floating_leg_accrual_period_

    @property
    def accrual_basis(self) -> AccrualBasis:
        return self.accrual_basis_

    @property
    def pay_business_day_convention(self) -> BusinessDayConvention:
        return self.pay_business_day_convention_

    @property
    def pay_holiday_convention(self) -> HolidayConvention:
        return self.pay_holiday_convention_

    @property
    def floating_leg(self) -> InterestRateStream:
        return self.floating_leg_

    @property
    def fixed_leg(self) -> InterestRateStream:
        return self.fixed_leg_

    def accept(self, visitor: ProductVisitor):
        return visitor.visit(self)

    def serialize(self) -> dict:
        content = {}
        content["VERSION"] = self._version
        content["TYPE"] = self._product_type
        content["EFFECTIVE_DATE"] = self.effective_date.ISO()
        if self.term_or_termination_date.is_term():
            content["TERM_OR_TERMINATION_DATE"] = self.term_or_termination_date.get_term().__str__()
        else:
            content["TERM_OR_TERMINATION_DATE"] = self.term_or_termination_date.get_date().ISO()
        content["PAYMENT_OFFSET"] = self.pay_offset.__str__()
        content["ON_INDEX"] = self.on_index_str_
        content["FIXED_RATE"] = self.fixed_rate
        content["PAY_OR_REC"] = self.pay_or_rec.to_string().upper()
        content["NOTIONAL"] = self.notional
        content["ACCRUAL_PERIOD"] = self.accrual_period.__str__()
        content["FLOATING_LEG_ACCRUAL_PERIOD"] = self.floating_leg_accrual_period.__str__()
        content["ACCRUAL_BASIS"] = self.accrual_basis.value_str
        content["PAY_BUSINESS_DAY_CONVENTION"] = self.pay_business_day_convention.value_str
        content["PAY_HOLIDAY_CONVENTION"] = self.pay_holiday_convention_.value_str
        content["SPREAD"] = self.spread
        content["COMPOUNDING_METHOD"] = self.compounding_method.to_string().upper()
        return content

    @classmethod
    def deserialize(cls, input_dict) -> "ProductRFRFuture":
        effective_date = Date(input_dict["EFFECTIVE_DATE"])
        term_or_termination_date = TermOrTerminationDate(input_dict["TERM_OR_TERMINATION_DATE"])
        pay_offset = Period(input_dict["PAYMENT_OFFSET"])
        on_index = input_dict["ON_INDEX"]
        fixed_rate = input_dict["FIXED_RATE"]
        pay_or_rec = PayOrReceive.from_string(input_dict["PAY_OR_REC"])
        notional = input_dict["NOTIONAL"]
        accrual_period = Period(input_dict["ACCRUAL_PERIOD"])
        floating_leg_accrual_period = Period(input_dict["FLOATING_LEG_ACCRUAL_PERIOD"])
        accrual_basis = AccrualBasis(input_dict["ACCRUAL_BASIS"])
        pay_business_day_convention = BusinessDayConvention(
            input_dict["PAY_BUSINESS_DAY_CONVENTION"]
        )
        pay_holiday_convention = HolidayConvention(input_dict["PAY_HOLIDAY_CONVENTION"])
        spread = input_dict["SPREAD"]
        compounding_method = CompoundingMethod.from_string(input_dict["COMPOUNDING_METHOD"])
        return cls(
            effective_date,
            term_or_termination_date,
            pay_offset,
            on_index,
            fixed_rate,
            pay_or_rec,
            notional,
            accrual_period,
            accrual_basis,
            floating_leg_accrual_period,
            pay_business_day_convention,
            pay_holiday_convention,
            spread,
            compounding_method,
        )


class ProductOvernightIndexBasisSwap(Product):

    _version = 1
    _product_type = "PRODUCT_OVERNIGHT_INDEX_BASIS_SWAP"

    def __init__(
        self,
        effective_date: Date,
        term_or_termination_date: TermOrTerminationDate,
        payment_off_set: Period,
        on_index_1: str,
        on_index_2: str,
        spread_over_leg_1: float,
        pay_or_rec_leg_1: PayOrReceive,
        notional: float,
        accrual_period_1: Period,
        accrual_basis: AccrualBasis,
        accrual_period_2: Optional[Period] = None,
        pay_business_day_convention: Optional[BusinessDayConvention] = BusinessDayConvention("F"),
        pay_holiday_convention: Optional[HolidayConvention] = HolidayConvention("USGS"),
        compounding_method: Optional[CompoundingMethod] = CompoundingMethod.COMPOUND,
    ) -> None:

        super().__init__()

        self.on_index_str_1_ = on_index_1
        self.on_index_str_2_ = on_index_2
        self.on_index_1_: ql.QuantLib.OvernightIndex = IndexRegistry().get(self.on_index_str_1_)
        self.on_index_2_: ql.QuantLib.OvernightIndex = IndexRegistry().get(self.on_index_str_2_)
        self.pay_business_day_convention_ = pay_business_day_convention
        self.pay_holiday_convention_ = pay_holiday_convention
        self.first_date_ = self.effective_date_ = effective_date
        self.term_or_termination_date_ = term_or_termination_date
        self.termination_date_ = self.term_or_termination_date_.get_date()
        if self.term_or_termination_date_.is_term():
            # we shall assert business day convention is the same between two legs
            calendar: ql.Calendar = self.on_index_1_.fixingCalendar()
            self.termination_date_ = Date(
                calendar.advance(
                    self.effective_date_,
                    self.term_or_termination_date_.get_term(),
                    self.on_index_1_.businessDayConvention(),
                )
            )

        # other attributes
        self.currency_ = Currency(self.on_index_1_.currency().code())
        self.spread_ = spread_over_leg_1
        self.notional_ = notional
        assert self.notional_ >= 0  # notional cannot be signed
        self.pay_or_rec_ = pay_or_rec_leg_1
        self.long_or_short_ = LongOrShort.LONG if notional > 0 else LongOrShort.SHORT
        self.pay_offset_ = payment_off_set
        self.accrual_basis_ = accrual_basis
        self.accrual_period_1_ = accrual_period_1
        self.accrual_period_2_ = accrual_period_1 if accrual_period_2 is None else accrual_period_2
        self.compounding_method_ = compounding_method

        # floating leg 1
        self.floating_leg_1_basis_ = None
        self.floating_leg_1_wo_basis_ = None
        self.floating_leg_1_ = InterestRateStream(
            effective_date=self.effective_date_,
            termination_date=self.termination_date_,
            accrual_period=self.accrual_period_1_,
            notional=self.notional_,
            currency=self.currency_,
            accrual_basis=self.accrual_basis_,
            buseinss_day_convention=self.pay_business_day_convention_,  # not the best
            holiday_convention=HolidayConvention(self.on_index_1_.fixingCalendar().name()),
            float_index=self.on_index_str_1_,
            ois_compounding=self.compounding_method_,
            ois_spread=self.spread_,
            fixing_in_arrear=True,
            payment_offset=self.pay_offset_,
            payment_business_day_convention=self.pay_business_day_convention_,
            payment_holiday_convention=self.pay_holiday_convention_,
        )

        # floating leg 2
        self.floating_leg_2_ = InterestRateStream(
            effective_date=self.effective_date_,
            termination_date=self.termination_date_,
            accrual_period=self.accrual_period_2_,
            notional=self.notional_,
            currency=self.currency_,
            accrual_basis=self.accrual_basis_,
            buseinss_day_convention=self.pay_business_day_convention_,  # not the best
            holiday_convention=HolidayConvention(self.on_index_2_.fixingCalendar().name()),
            float_index=self.on_index_str_2_,
            ois_compounding=self.compounding_method_,
            ois_spread=0.0,
            fixing_in_arrear=True,
            payment_offset=self.pay_offset_,
            payment_business_day_convention=self.pay_business_day_convention_,
            payment_holiday_convention=self.pay_holiday_convention_,
        )

        last_dt_floating_1 = self.floating_leg_1_.last_date
        last_dt_floating_2 = self.floating_leg_2_.last_date
        self.last_date_ = (
            last_dt_floating_2 if last_dt_floating_2 >= last_dt_floating_1 else last_dt_floating_1
        )

    def floating_leg_1_cash_flow(self, i: int) -> Product:
        assert 0 <= i < self.floating_leg_1_.num_cashflows()
        return self.floating_leg_1_.element(i)

    def floating_leg_2_cash_flow(self, i: int) -> Product:
        assert 0 <= i < self.floating_leg_2_.num_cashflows()
        return self.floating_leg_2_.element(i)

    @property
    def effective_date(self) -> Date:
        return self.effective_date_

    @property
    def termination_date(self) -> Date:
        return self.termination_date_

    @property
    def term_or_termination_date(self) -> Date:
        return self.term_or_termination_date_

    @property
    def pay_offset(self) -> Period:
        return self.pay_offset_

    @property
    def spread(self) -> float:
        return self.spread_

    @property
    def on_index_1(self) -> ql.QuantLib.OvernightIndex:
        return self.on_index_1_

    @property
    def on_index_2(self) -> ql.QuantLib.OvernightIndex:
        return self.on_index_2_

    @property
    def pay_or_rec(self) -> PayOrReceive:
        return self.pay_or_rec_

    @property
    def compounding_method(self) -> CompoundingMethod:
        return self.compounding_method_

    @property
    def accrual_period_leg_1(self) -> Period:
        return self.accrual_period_1_

    @property
    def accrual_period_leg_2(self) -> Period:
        return self.accrual_period_2_

    @property
    def accrual_basis(self) -> AccrualBasis:
        return self.accrual_basis_

    @property
    def pay_business_day_convention(self) -> BusinessDayConvention:
        return self.pay_business_day_convention_

    @property
    def pay_holiday_convention(self) -> HolidayConvention:
        return self.pay_holiday_convention_

    @property
    def floating_leg_1(self) -> InterestRateStream:
        return self.floating_leg_1_

    @property
    def floating_leg_2(self) -> InterestRateStream:
        return self.floating_leg_2_

    @property
    def floating_leg_1_basis(self) -> InterestRateStream:
        if self.floating_leg_1_basis_ is None:
            self.floating_leg_1_basis_ = InterestRateStream(
                effective_date=self.effective_date_,
                termination_date=self.termination_date_,
                accrual_period=self.accrual_period_1_,
                notional=self.notional_,
                currency=self.currency_,
                accrual_basis=self.accrual_basis_,
                buseinss_day_convention=self.pay_business_day_convention_,
                holiday_convention=HolidayConvention(self.on_index_1_.fixingCalendar().name()),
                fixed_rate=self.spread_,
                is_on_index=False,
                payment_offset=self.pay_offset_,
                payment_business_day_convention=self.pay_business_day_convention_,
                payment_holiday_convention=self.pay_holiday_convention_,
            )
        return self.floating_leg_1_basis_

    @property
    def floating_leg_1_wo_basis(self) -> InterestRateStream:
        if self.floating_leg_1_wo_basis_ is None:
            self.floating_leg_1_wo_basis_ = InterestRateStream(
                effective_date=self.effective_date_,
                termination_date=self.termination_date_,
                accrual_period=self.accrual_period_1_,
                notional=self.notional_,
                currency=self.currency_,
                accrual_basis=self.accrual_basis_,
                buseinss_day_convention=self.pay_business_day_convention_,  # not the best
                holiday_convention=HolidayConvention(self.on_index_1_.fixingCalendar().name()),
                float_index=self.on_index_str_1_,
                ois_compounding=self.compounding_method_,
                ois_spread=0.0,
                fixing_in_arrear=True,
                payment_offset=self.pay_offset_,
                payment_business_day_convention=self.pay_business_day_convention_,
                payment_holiday_convention=self.pay_holiday_convention_,
            )
        return self.floating_leg_1_wo_basis_

    def accept(self, visitor: ProductVisitor):
        return visitor.visit(self)

    def serialize(self) -> dict:
        content = {}
        content["VERSION"] = self._version
        content["TYPE"] = self._product_type
        content["EFFECTIVE_DATE"] = self.effective_date.ISO()
        if self.term_or_termination_date.is_term():
            content["TERM_OR_TERMINATION_DATE"] = self.term_or_termination_date.get_term().__str__()
        else:
            content["TERM_OR_TERMINATION_DATE"] = self.term_or_termination_date.get_date().ISO()
        content["PAYMENT_OFFSET"] = self.pay_offset.__str__()
        content["ON_INDEX_LEG_1"] = self.on_index_str_1_
        content["ON_INDEX_LEG_2"] = self.on_index_str_2_
        content["SPARED_OVER_LEG_1"] = self.spread
        content["PAY_OR_REC_LEG_1"] = self.pay_or_rec.to_string().upper()
        content["NOTIONAL"] = self.notional
        content["ACCRUAL_PERIOD_1"] = self.accrual_period_leg_1.__str__()
        content["ACCRUAL_PERIOD_2"] = self.accrual_period_leg_2.__str__()
        content["ACCRUAL_BASIS"] = self.accrual_basis.value_str
        content["PAY_BUSINESS_DAY_CONVENTION"] = self.pay_business_day_convention.value_str
        content["PAY_HOLIDAY_CONVENTION"] = self.pay_holiday_convention_.value_str
        content["COMPOUNDING_METHOD"] = self.compounding_method.to_string().upper()
        return content

    @classmethod
    def deserialize(cls, input_dict) -> "ProductRFRFuture":
        effective_date = Date(input_dict["EFFECTIVE_DATE"])
        term_or_termination_date = TermOrTerminationDate(input_dict["TERM_OR_TERMINATION_DATE"])
        pay_offset = Period(input_dict["PAYMENT_OFFSET"])
        on_index_1 = input_dict["ON_INDEX_LEG_1"]
        on_index_2 = input_dict["ON_INDEX_LEG_2"]
        spread_over_leg_1 = input_dict["SPREAD_OVER_LEG_1"]
        pay_or_rec_leg_1 = PayOrReceive.from_string(input_dict["PAY_OR_REC_LEG_1"])
        notional = input_dict["NOTIONAL"]
        leg_1_accrual_period = Period(input_dict["ACCRUAL_PERIOD_1"])
        leg_2_accrual_period = Period(input_dict["ACCRUAL_PERIOD_2"])
        accrual_basis = AccrualBasis(input_dict["ACCRUAL_BASIS"])
        pay_business_day_convention = BusinessDayConvention(
            input_dict["PAY_BUSINESS_DAY_CONVENTION"]
        )
        pay_holiday_convention = HolidayConvention(input_dict["PAY_HOLIDAY_CONVENTION"])
        compounding_method = CompoundingMethod.from_string(input_dict["COMPOUNDING_METHOD"])

        return cls(
            effective_date,
            term_or_termination_date,
            pay_offset,
            on_index_1,
            on_index_2,
            spread_over_leg_1,
            pay_or_rec_leg_1,
            notional,
            leg_1_accrual_period,
            accrual_basis,
            leg_2_accrual_period,
            pay_business_day_convention,
            pay_holiday_convention,
            compounding_method,
        )


class ProductBond(ProductPortfolio):

    _version = 1
    _product_type = "PRODUCT_BOND"

    def __init__(
        self,
        name: str,
        bond_specs: BondSpecs,
        trade_date: Date,
        buy_sell: str,
        traded_price: Optional[float] = 0.0,
        clean: Optional[bool] = True,
    ):

        self.name_ = name
        self.bond_specs_ = bond_specs

        self.buy_sell_ = LongOrShort.from_string(buy_sell)
        self.sign_ = 1.0 if self.buy_sell_ == LongOrShort.LONG else -1.0

        self.traded_price_ = traded_price  # input is yield
        self.trade_date_ = trade_date

        self.conv_ = bond_specs.bond_conv_

        # calculate settlement date based on offset
        settlement_offset = ""
        if self.conv_.settlement_offset.endswith("B"):
            # business day offset
            settlement_offset = Period(f"{int(self.conv_.settlement_offset[:-1])}D")
        else:
            settlement_offset = Period(self.conv_.settlement_offset)

        self.settlement_date_ = add_period(
            self.trade_date_,
            settlement_offset,
            self.conv_.payment_business_day_convention,
            self.conv_.payment_holiday_convention,
        )

        schedule = make_schedule(
            start_date=bond_specs.first_accrual_date_,
            end_date=bond_specs.maturity_date_,
            accrual_period=self.conv_.coupon_accrual_period,
            holiday_convention=self.conv_.payment_holiday_convention,
            business_day_convention=self.conv_.payment_business_day_convention,
            accrual_basis=self.conv_.coupon_accrual_convention,
            rule="BACKWARD",
            end_of_month=self.conv_.end_of_month,
            fix_in_arrear=False,
            payment_offset=Period("0D"),
            payment_business_day_convention=self.conv_.payment_business_day_convention,
            payment_holiday_convention=self.conv_.payment_holiday_convention,
        )

        self.coupon_rates_, self.period_lengths_ = [], []
        products, weights, coupons_cf = [], [], []
        self.ai_t_ = 0.0
        self.current_coupon_rate_ = 0.0

        # coupon cashflows
        for _, row in schedule.iterrows():
            if row.EndDate <= self.settlement_date_:
                continue

            cf = ProductFixedAccrued(
                row.StartDate,
                row.EndDate,
                self.conv_.currency,
                bond_specs.coupon_rate_
                * self.sign_,
                self.conv_.coupon_accrual_convention,
                row.PaymentDate,
                self.conv_.payment_business_day_convention,
                self.conv_.payment_holiday_convention,
            )

            products.append(cf)
            coupons_cf.append(cf)
            weights.append(1.0)

            self.coupon_rates_.append(abs(cf.notional))
            if cf.effective_date <= self.settlement_date_ <= cf.termination_date:
                # only keep the remaining length
                remaining_length = accrued(
                    self.settlement_date_,
                    cf.termination_date,
                    self.conv_.coupon_accrual_convention,
                    self.conv_.payment_business_day_convention,
                    self.conv_.payment_holiday_convention,
                )
                self.period_lengths_.append(remaining_length)
                # save the accrued period length for the current coupon
                self.ai_t_ = accrued(
                    cf.effective_date,
                    self.settlement_date_,
                    self.conv_.coupon_accrual_convention,
                    self.conv_.payment_business_day_convention,
                    self.conv_.payment_holiday_convention,
                )
                self.current_coupon_rate_ = abs(cf.notional)
            else:
                self.period_lengths_.append(cf.accrued)

        self.coupons_cf_ = coupons_cf

        principal = ProductBulletCashflow(
            termination_date=bond_specs.maturity_date_,
            currency=self.conv_.currency,
            notional=bond_specs.redemption_percentage_,
            long_or_short=self.buy_sell_,
            payment_date=schedule.iloc[-1].PaymentDate,
        )

        self.principal_ = principal
        products.append(principal)
        weights.append(1.0)

        super().__init__(products, weights)
        self.currency_ = self.conv_.currency
        self.last_date_ = self.bond_specs_.maturity_date_
        self.first_date_ = self.settlement_date_
        self.face_value_ = self.conv_.principal

    @property
    def bond_specs(self) -> BondSpecs:
        return self.bond_specs_

    @property
    def conv(self) -> DataConventionBondFixed:
        return self.conv_

    @property
    def face_value(self) -> float:
        return self.face_value_

    @property
    def isin(self) -> str:
        return self.bond_specs.__getitem__(BondSpecs.ISIN)

    @property
    def bond_convention(self) -> DataConventionBondFixed:
        return self.bond_specs_.__getitem__(BondSpecs.BOND_CONVENTION)

    @property
    def settlement_date(self) -> Date:
        return self.settlement_date_

    @property
    def trade_date(self) -> Date:
        return self.trade_date_

    @property
    def buy_sell(self) -> LongOrShort:
        return self.buy_sell_

    @property
    def coupon_rate(self) -> float:
        return self.bond_specs_.coupon_rate_

    @property
    def maturity_date(self) -> Date:
        return self.bond_specs_.maturity_date_

    def cashflow(self, i: int) -> Product:
        return self.element(i)

    @property
    def coupon_rates(self) -> List[float]:
        return self.coupon_rates_

    @property
    def period_lengths(self) -> List[float]:
        return self.period_lengths_

    @property
    def current_coupon_rate(self) -> float:
        return self.current_coupon_rate_

    @property
    def ai_t(self) -> float:
        return self.ai_t_

    @property
    def principal(self) -> Product:
        return self.principal_

    @property
    def coupons_cf(self) -> List[Product]:
        return self.coupons_cf_

    @property
    def traded_price(self) -> float:
        return self.traded_price_

    def num_coupons_cf(self) -> int:
        return len(self.coupons_cf_)

    def num_cashflows(self) -> int:
        return self.num_elements_

    def accept(self, visitor):
        return visitor.visit(self)

    def serialize(self) -> dict:
        content = super().serialize()
        content["VERSION"] = self._version
        content["TYPE"] = self._product_type
        content["BOND_SPECS"] = self.bond_specs_.serialize()
        content["SETTLEMENT_DATE"] = self.settlement_date_.ISO()
        content["BUY_SELL"] = self.buy_sell_.to_string().upper()
        return content

    @classmethod
    def deserialize(cls, input_dict: dict) -> "ProductBond":
        input_dict_ = input_dict.copy()
        assert (
            input_dict_["TYPE"] == cls._product_type
        ), f"Expected {cls._product_type}, got {input_dict_['TYPE']}"
        input_dict_.pop("TYPE")
        assert (
            input_dict_["VERSION"] == cls._version
        ), f"Expected version {cls._version}, got {input_dict_['VERSION']}"
        input_dict_.pop("VERSION")

        bond_specs = BondSpecs.deserialize(input_dict_.pop("BOND_SPECS"))
        settlement_date = Date(input_dict_.pop("SETTLEMENT_DATE"))
        buy_sell = input_dict_.pop("BUY_SELL")
        weights = input_dict_.pop("WEIGHTS")

        # rebuild cashflows
        cashflows = []
        for _, v in input_dict_.items():
            func = ProductBuilderRegistry().get(v["TYPE"])
            cashflows.append(func(v))

        instance = cls.__new__(cls)
        instance.bond_specs_ = bond_specs
        instance.settlement_date_ = settlement_date
        instance.buy_sell_ = LongOrShort.from_string(buy_sell)
        ProductPortfolio.__init__(instance, cashflows, weights)
        return instance


class ProductFxForward(Product):

    _version = 1
    _product_type = "PRODUCT_FX_FORWARD"

    def __init__(
        self,
        termination_date: Date,
        fx_pair: str,
        pay_or_receive: PayOrReceive,
        settlement_currency: Currency,
        foreign_notional: float,
        strike: Optional[float] = 0.0,
        payment_business_day_convention: Optional[BusinessDayConvention] = BusinessDayConvention(
            "F"
        ),
        payment_holidays: Optional[HolidayConvention] = HolidayConvention("USGS"),
        payment_offset: Optional[Period] = Period("0D"),
    ) -> None:

        super().__init__()

        # resolve index and convention
        self.fx_pair_: FXIndex = IndexRegistry().get(fx_pair)
        self.pay_business_day_convention_ = payment_business_day_convention
        self.pay_holidays_ = payment_holidays
        # sort out dates
        self.termination_date_ = self.first_date_ = termination_date
        self.pay_offset_ = payment_offset
        self.pay_date_ = add_period(
            self.termination_date_,
            payment_offset,
            self.pay_business_day_convention_,
            self.pay_holidays_,
        )
        self.last_date_ = self.pay_date_
        # other attributes
        self.strike_ = strike
        self.pay_or_rec_ = pay_or_receive
        self.long_or_short_ = LongOrShort.LONG
        self.currency_ = self.settlement_currency_ = settlement_currency
        self.notional_ = self.foreign_notional_ = foreign_notional

    @property
    def termination_date(self) -> Date:
        return self.termination_date_

    @property
    def strike(self) -> float:
        return self.strike_

    @property
    def fx_pair(self) -> FXIndex:
        return self.fx_pair_

    @property
    def notional(self) -> float:
        return self.foreign_notional_

    @property
    def currency(self):
        return self.settlement_currency_

    @property
    def long_or_short(self):
        return self.long_or_short_

    @property
    def pay_or_rec(self):
        return self.pay_or_rec_

    @property
    def pay_business_day_convention(self):
        return self.pay_business_day_convention_

    @property
    def pay_holidays(self):
        return self.pay_holidays_

    @property
    def pay_offset(self) -> Period:
        return self.pay_offset_

    def accept(self, visitor: ProductVisitor):
        return visitor.visit(self)

    def serialize(self) -> dict:
        content = {}
        content["VERSION"] = self._version
        content["TYPE"] = self._product_type
        content["TERMINATION_DATE"] = self.termination_date.ISO()
        content["FX_INDEX"] = self.fx_pair.name()
        content["PAY_OR_REC"] = self.pay_or_rec.to_string().upper()
        content["SETTLEMENT_CURRENCY"] = self.currency.ccy.code()
        content["FOREIGN_NOTIONAL"] = self.foreign_notional_
        content["STRIKE"] = self.strike
        content["PAY_BUSINESS_DAY_CONVENTION"] = self.pay_business_day_convention.value_str
        content["PAY_HOLIDAYS"] = self.pay_holidays.value_str
        content["PAY OFFSET"] = self.pay_offset.__str__()
        return content

    @classmethod
    def deserialize(cls, input_dict) -> "ProductFxForward":
        termination_date = Date(input_dict["TERMINATION_DATE"])
        fx_index = input_dict["FX_INDEX"]
        pay_or_rec = PayOrReceive.from_string(input_dict["PAY_OR_REC"])
        currency = Currency(input_dict["SETTLEMENT_CURRENCY"])
        foreign_notional = input_dict["FOREIGN_NOTIONAL"]
        strike = float(input_dict["STRIKE"])
        pay_business_day_convention = BusinessDayConvention(
            input_dict["PAY_BUSINESS_DAY_CONVENTION"]
        )
        pay_holiday_convention = HolidayConvention(input_dict["PAY_HOLIDAYS"])
        pay_offset = Period(input_dict["PAY OFFSET"])

        return cls(
            termination_date,
            fx_index,
            pay_or_rec,
            currency,
            foreign_notional,
            strike,
            pay_business_day_convention,
            pay_holiday_convention,
            pay_offset,
        )


### some helper products


class ProductZeroSpread(Product):

    _version = 1
    _product_type = "PRODUCT_ZERO_SPREAD"

    def __init__(
        self,
        termination_date: Date,
        index: str,
        zero_rate: float,
        notional: float,
        long_or_short: LongOrShort,
    ) -> None:

        super().__init__()
        # get index
        self.index_str_ = index
        self.index_ = IndexRegistry().get(index)
        self.zero_rate_ = zero_rate
        self.currency_ = Currency(self.index_.currency().code())
        self.first_date_ = self.last_date_ = termination_date
        self.long_or_short_ = long_or_short
        self.notional_ = notional

    @property
    def termination_date(self) -> Date:
        return self.last_date

    @property
    def index(self) -> ql.Index:
        return self.index_

    @property
    def zero_rate(self) -> float:
        return self.zero_rate_

    def accept(self, visitor: ProductVisitor):
        return visitor.visit(self)

    def serialize(self) -> dict:
        content = {}
        content["VERSION"] = self._version
        content["TYPE"] = self._product_type
        content["TERMINATION_DATE"] = self.termination_date.ISO()
        content["INDEX"] = self.index_str_
        content["ZERO_RATE"] = self.zero_rate
        content["NOTIONAL"] = self.notional
        content["LONG_OR_SHORT"] = self.long_or_short.to_string().upper()
        return content

    @classmethod
    def deserialize(cls, input_dict) -> "ProductZeroSpread":
        termination_date = Date(input_dict["TERMINATION_DATE"])
        index = input_dict["INDEX"]
        zero_rate = input_dict["ZERO_RATE"]
        notional = float(input_dict["NOTIONAL"])
        long_or_short = LongOrShort.from_string(input_dict["LONG_OR_SHORT"])
        return cls(termination_date, index, zero_rate, notional, long_or_short)


### register
ProductBuilderRegistry().register(ProductBulletCashflow._product_type, ProductBulletCashflow)
ProductBuilderRegistry().register(ProductFixedAccrued._product_type, ProductFixedAccrued)
ProductBuilderRegistry().register(
    ProductOvernightIndexCashflow._product_type, ProductOvernightIndexCashflow
)
ProductBuilderRegistry().register(ProductRFRFuture._product_type, ProductRFRFuture)
ProductBuilderRegistry().register(ProductRFRSwap._product_type, ProductRFRSwap)
ProductBuilderRegistry().register(
    ProductOvernightIndexBasisSwap._product_type, ProductOvernightIndexBasisSwap
)
ProductBuilderRegistry().register(InterestRateStream._product_type, InterestRateStream)
ProductBuilderRegistry().register(ProductZeroSpread._product_type, ProductZeroSpread)
ProductBuilderRegistry().register(ProductBond._product_type, ProductBond)
ProductBuilderRegistry().register(ProductFxForward._product_type, ProductFxForward)

# support de-serilization
ProductBuilderRegistry().register(
    f"{ProductBulletCashflow._product_type}_DES", ProductBulletCashflow.deserialize
)
ProductBuilderRegistry().register(
    f"{ProductFixedAccrued._product_type}_DES", ProductFixedAccrued.deserialize
)
ProductBuilderRegistry().register(
    f"{ProductOvernightIndexCashflow._product_type}_DES", ProductOvernightIndexCashflow.deserialize
)
ProductBuilderRegistry().register(
    f"{ProductRFRFuture._product_type}_DES", ProductRFRFuture.deserialize
)
ProductBuilderRegistry().register(f"{ProductRFRSwap._product_type}_DES", ProductRFRSwap.deserialize)
ProductBuilderRegistry().register(
    f"{ProductOvernightIndexBasisSwap._product_type}_DES",
    ProductOvernightIndexBasisSwap.deserialize,
)
ProductBuilderRegistry().register(
    f"{ProductZeroSpread._product_type}_DES", ProductZeroSpread.deserialize
)

ProductBuilderRegistry().register(
    f"{ProductFxForward._product_type}_DES", ProductFxForward.deserialize
)
