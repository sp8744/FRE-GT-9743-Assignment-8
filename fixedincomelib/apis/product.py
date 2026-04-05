import pickle
from typing import List, Optional
from fixedincomelib.date import *
from fixedincomelib.market import *
from fixedincomelib.product import *


def qfDisplayProduct(product: Product):
    visitor = ProductDisplayVisitor()
    product.accept(visitor)
    return visitor.display()


def qdDisplaySpecs(specs: BondSpecs):
    return pd.DataFrame(specs.info.items(), columns=["Name", "Value"])


def qfWriteProductToFile(product: Product, path: str):
    this_dict = product.serialize()
    with open(path, "wb") as handle:
        pickle.dump(this_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return "DONE"


def qfReadProductFromFile(path: str):
    with open(path, "rb") as handle:
        this_dict = pickle.load(handle)
        prod_type = this_dict["TYPE"]
        func = ProductBuilderRegistry().get(f"{prod_type}_DES")
        return func(this_dict)


def qfCreateProductFromDataConvention(
    value_date: str, data_convention: str, axis1: str, values: float, **kwargs
):
    conv_obj = DataConventionRegistry().get(data_convention)
    return ProductFactory.create_product_from_data_convention(
        Date(value_date), axis1, conv_obj, values, **kwargs
    )


def qfCreateProductBulletCashflow(
    termination_date: str,
    currency: str,
    notional: float,
    long_or_short: str,
    payment_date: Optional[str] = "",
):

    pay_date = None
    if payment_date != "":
        pay_date = Date(payment_date)

    return ProductBulletCashflow(
        Date(termination_date),
        Currency(currency),
        notional,
        LongOrShort.from_string(long_or_short),
        pay_date,
    )


def qfCreateProducFixedAccrued(
    effective_date: str,
    termination_date: str,
    currency: str,
    notional: float,
    accrual_basis: str,
    payment_date: Optional[str] = "",
    business_day_convention: Optional[str] = "",
    holiday_convention: Optional[str] = "",
):

    pay_date = None
    if payment_date != "":
        pay_date = Date(payment_date)

    business_day_convention_obj = BusinessDayConvention("F")
    if business_day_convention != "":
        business_day_convention_obj = BusinessDayConvention(business_day_convention)

    holiday_day_convention_obj = HolidayConvention("USGS")
    if holiday_convention != "":
        holiday_day_convention_obj = HolidayConvention(holiday_convention)

    return ProductFixedAccrued(
        Date(effective_date),
        Date(termination_date),
        Currency(currency),
        notional,
        AccrualBasis(accrual_basis),
        pay_date,
        business_day_convention_obj,
        holiday_day_convention_obj,
    )


def qfCreateProductOvernightIndexCashflow(
    effective_date: str,
    term_or_terminatino_date: str,
    overnight_index: str,
    notional: float,
    compounding_method: Optional[str] = "compound",
    spread: Optional[float] = 0.0,
    payment_date: Optional[str] = "",
):

    pay_date = None
    if payment_date != "":
        pay_date = Date(payment_date)

    return ProductOvernightIndexCashflow(
        Date(effective_date),
        TermOrTerminationDate(term_or_terminatino_date),
        overnight_index,
        CompoundingMethod.from_string(compounding_method),
        spread,
        notional,
        pay_date,
    )


def qfCreateProductRFRFuture(
    effective_date: str,
    term_or_termination_date: str,
    future_convention: str,
    long_or_short: str,
    amount: float,
    strike: Optional[float] = 0.0,
):

    return ProductRFRFuture(
        Date(effective_date),
        TermOrTerminationDate(term_or_termination_date),
        future_convention,
        LongOrShort.from_string(long_or_short),
        amount,
        strike,
    )


def qfCreateProductRFRSwap(
    effective_date: str,
    term_or_termination_date: str,
    payment_off_set: str,
    on_index: str,
    fixed_rate: float,
    pay_or_rec: str,
    notional: float,
    accrual_period: str,
    accrual_basis: str,
    floating_leg_accrual_period: Optional[str] = "",
    pay_business_day_convention: Optional[str] = "F",
    pay_holiday_convention: Optional[str] = "USGS",
    spread: Optional[float] = 0.0,
    compounding_method: Optional[str] = "compound",
):

    if floating_leg_accrual_period == "":
        floating_leg_accrual_period = accrual_period

    return ProductRFRSwap(
        Date(effective_date),
        TermOrTerminationDate(term_or_termination_date),
        Period(payment_off_set),
        on_index,
        fixed_rate,
        PayOrReceive(pay_or_rec),
        notional,
        Period(accrual_period),
        AccrualBasis(accrual_basis),
        Period(floating_leg_accrual_period),
        BusinessDayConvention(pay_business_day_convention),
        HolidayConvention(pay_holiday_convention),
        spread,
        CompoundingMethod.from_string(compounding_method),
    )


def qfCreateProductOvernightIndexBasisSwap(
    effective_date: str,
    term_or_termination_date: str,
    payment_off_set: str,
    on_index_leg_1: str,
    on_index_leg_2: str,
    spread_over_leg_1: float,
    pay_or_rec_leg_1: str,
    notional: float,
    accrual_period_1: str,
    accrual_period_2: str,
    accrual_basis: str,
    pay_business_day_convention: Optional[str] = "F",
    pay_holiday_convention: Optional[str] = "USGS",
    compounding_method: Optional[str] = "compound",
):

    return ProductOvernightIndexBasisSwap(
        effective_date=Date(effective_date),
        term_or_termination_date=TermOrTerminationDate(term_or_termination_date),
        payment_off_set=Period(payment_off_set),
        on_index_1=on_index_leg_1,
        on_index_2=on_index_leg_2,
        spread_over_leg_1=spread_over_leg_1,
        pay_or_rec_leg_1=PayOrReceive(pay_or_rec_leg_1),
        notional=notional,
        accrual_period_1=Period(accrual_period_1),
        accrual_period_2=Period(accrual_period_2),
        accrual_basis=AccrualBasis(accrual_basis),
        pay_business_day_convention=BusinessDayConvention(pay_business_day_convention),
        pay_holiday_convention=HolidayConvention(pay_holiday_convention),
        compounding_method=CompoundingMethod.from_string(compounding_method),
    )


def qfCreateBondSpecs(key: str, parameters: dict) -> BondSpecs:

    # check if exists
    # if not, register(), and get()

    # otherwise, get()
    if not BondSpecsRegistry().exists(key):
        BondSpecsRegistry().register(key, parameters)

    return BondSpecsRegistry().get(key)


def qfCreateProductBond(name: str, trade_date: str, buy_sell: str, trade: float) -> ProductBond:

    bond_specs = BondSpecsRegistry().get(name)
    return ProductBond(
        name=name,
        bond_specs=bond_specs,
        trade_date=Date(trade_date),
        buy_sell=buy_sell,
        traded_price=trade,
    )


def qfCreatePortfolio(
    products: List[Product], weights: Optional[List[float]] = None
) -> ProductPortfolio:
    return ProductPortfolio(products, weights)


def qfCreateProductFXForward(
    termination_date: str,
    fx_pair: str,
    pay_or_rec: str,
    settlement_ccy: str,
    foreign_notional: float,
    strike: float,
    business_day_convention: Optional[str] = "",
    holiday_convention: Optional[str] = "",
    pay_offset: Optional[str] = "0D",
):

    business_day_convention_obj = BusinessDayConvention("F")
    if business_day_convention != "":
        business_day_convention_obj = BusinessDayConvention(business_day_convention)

    holiday_day_convention_obj = HolidayConvention("USGS")
    if holiday_convention != "":
        holiday_day_convention_obj = HolidayConvention(holiday_convention)

    return ProductFxForward(
        Date(termination_date),
        fx_pair,
        PayOrReceive(pay_or_rec),
        Currency(settlement_ccy),
        foreign_notional,
        strike,
        business_day_convention_obj,
        holiday_day_convention_obj,
        Period(pay_offset),
    )
