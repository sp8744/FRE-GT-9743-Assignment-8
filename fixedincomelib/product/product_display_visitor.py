from __future__ import annotations
from atexit import register
from typing import Any, Dict, List, Tuple
import pandas as pd
from functools import singledispatchmethod
from fixedincomelib.product.product_interfaces import Product, ProductVisitor
from fixedincomelib.product.product_portfolio import ProductPortfolio
from fixedincomelib.product.linear_products import (
    ProductBulletCashflow,
    ProductFixedAccrued,
    ProductOvernightIndexBasisSwap,
    ProductFxForward,
    ProductOvernightIndexBasisSwap,
    ProductOvernightIndexCashflow,
    ProductRFRFuture,
    ProductRFRSwap,
    ProductBond,
    ProductZeroSpread,
)


class ProductDisplayVisitor(ProductVisitor):

    def __init__(self) -> None:
        super().__init__()
        self.nvps_ = []

    @singledispatchmethod
    def visit(self, product: Product):
        raise NotImplementedError(f"No visitor for {Product._product_type}")

    def display(self) -> pd.DataFrame:
        return pd.DataFrame(self.nvps_, columns=["Name", "Value"])

    def _common_items(self, product: Product):
        self.nvps_ = [
            ["Product Type", product.product_type],
            ["Notional", product.notional],
            ["Currency", product.currency.value_str],
            ["Long Or Short", product.long_or_short.to_string().upper()],
        ]

    @visit.register
    def _(self, product: ProductBulletCashflow):
        self._common_items(product)
        self.nvps_.append(["Termination Date", product.termination_date.ISO()])
        self.nvps_.append(["Payment Date", product.payment_date.ISO()])

    @visit.register
    def _(self, product: ProductFixedAccrued):
        self._common_items(product)
        self.nvps_.append(["Effective Date", product.effective_date.ISO()])
        self.nvps_.append(["Termination Date", product.termination_date.ISO()])
        self.nvps_.append(["Accrual Basis", product.accrual_basis.value_str])
        self.nvps_.append(["Payment Date", product.payment_date.ISO()])
        self.nvps_.append(["Business Day Convention", product.business_day_convention.value_str])
        self.nvps_.append(["Holiday Convention", product.holiday_convention.value_str])

    @visit.register
    def _(self, product: ProductOvernightIndexCashflow):
        self._common_items(product)
        self.nvps_.append(["Effective Date", product.effective_date.ISO()])
        self.nvps_.append(["Termination Date", product.termination_date.ISO()])
        self.nvps_.append(["ON Index", product.on_index.name()])
        self.nvps_.append(["Compounding Method", product.compounding_method.to_string().upper()])
        self.nvps_.append(["Spread", product.spread])
        self.nvps_.append(["Payment Date", product.payment_date.ISO()])

    @visit.register
    def _(self, product: ProductRFRFuture):
        self._common_items(product)
        self.nvps_.append(["Effective Date", product.effective_date.ISO()])
        self.nvps_.append(["Termination Date", product.termination_date.ISO()])
        self.nvps_.append(["Future Convention", product.future_conv.name])
        self.nvps_.append(["Amount", product.amount])
        self.nvps_.append(["Strike", product.strike])

    @visit.register
    def _(self, product: ProductRFRSwap):
        self._common_items(product)
        self.nvps_.append(["Effective Date", product.effective_date.ISO()])
        self.nvps_.append(["Termination Date", product.termination_date.ISO()])
        self.nvps_.append(["Payment Offset", product.pay_offset.__str__()])
        self.nvps_.append(["ON Index", product.on_index.name()])
        self.nvps_.append(["Fixed Rate", product.fixed_rate])
        self.nvps_.append(["Pay Or Receive", product.pay_or_rec.to_string().upper()])
        self.nvps_.append(["Accrual Period", product.accrual_period.__str__()])
        self.nvps_.append(["Accrual Basis", product.accrual_basis.value_str])
        self.nvps_.append(
            ["Floating Leg Accrual Period", product.floating_leg_accrual_period.__str__()]
        )
        self.nvps_.append(
            ["Business Day Convention", product.pay_business_day_convention.value_str]
        )
        self.nvps_.append(["Holiday Convention", product.pay_holiday_convention.value_str])
        self.nvps_.append(["Compounding Method", product.compounding_method.to_string()])

    @visit.register
    def _(self, product: ProductOvernightIndexBasisSwap):
        self._common_items(product)
        self.nvps_.append(["Effective Date", product.effective_date.ISO()])
        self.nvps_.append(["Termination Date", product.termination_date.ISO()])
        self.nvps_.append(["Payment Offset", product.pay_offset.__str__()])
        self.nvps_.append(["ON Index 1", product.on_index_1.name()])
        self.nvps_.append(["ON Index 2", product.on_index_2.name()])
        self.nvps_.append(["Spread Over Leg 1", product.spread])
        self.nvps_.append(["Pay Or Receive Leg 1", product.pay_or_rec.to_string().upper()])
        self.nvps_.append(["Accrual Period Leg 1", product.accrual_period_leg_1.__str__()])
        self.nvps_.append(["Accrual Period Leg 2", product.accrual_period_leg_2.__str__()])
        self.nvps_.append(["Accrual Basis", product.accrual_basis.value_str])
        self.nvps_.append(
            ["Business Day Convention", product.pay_business_day_convention.value_str]
        )
        self.nvps_.append(["Holiday Convention", product.pay_holiday_convention.value_str])
        self.nvps_.append(["Compounding Method", product.compounding_method.to_string()])

    @visit.register
    def _(self, product: ProductZeroSpread):
        self._common_items(product)
        self.nvps_.append(["Termination Date", product.termination_date.ISO()])
        self.nvps_.append(["Index", product.index.name()])
        self.nvps_.append(["Zero Rate", product.zero_rate])

    @visit.register
    def _(self, product: ProductPortfolio):
        self.nvps_.append(["Product Type", product.product_type])
        for i in range(product.num_elemnts):
            self.nvps_.append([f"Product {i} Type", product.element(i).product_type])
            self.nvps_.append([f"Product {i} Weight", product.weight(i)])

    @visit.register
    def _(self, product: ProductFxForward):
        self._common_items(product)
        self.nvps_.append(["Termination Date", product.termination_date.ISO()])
        self.nvps_.append(["Index", product.fx_pair.name()])
        self.nvps_.append(["PayOrRec", product.pay_or_rec.to_string().upper()])
        self.nvps_.append(["Strike", product.strike])
        self.nvps_.append(
            ["Payment Business Day Convention", product.pay_business_day_convention.value_str]
        )
        self.nvps_.append(["Payment Holiday Convention", product.pay_holidays.value_str])
        self.nvps_.append(["Payment Offset", product.pay_offset.__str__()])

    @visit.register
    def _(self, product: ProductBond):
        # bond-level info
        self.nvps_.append(["Product Type", product.product_type])
        self.nvps_.append(["ISIN", product.isin])
        self.nvps_.append(["Bond Convention", product.bond_convention])
        self.nvps_.append(["Issue Date", product.bond_specs.issue_date_.ISO()])
        self.nvps_.append(["First Accrual Date", product.bond_specs.first_accrual_date_.ISO()])
        self.nvps_.append(["First Coupon Date", product.bond_specs.first_coupon_date_.ISO()])
        self.nvps_.append(["Maturity Date", product.maturity_date.ISO()])
        self.nvps_.append(["Coupon Rate", product.coupon_rate])
        self.nvps_.append(["Redemption Percentage", product.bond_specs.redemption_percentage_])
        self.nvps_.append(["Trade Date", product.trade_date.ISO()])
        self.nvps_.append(["Settlement Date", product.settlement_date.ISO()])
        self.nvps_.append(["Buy/Sell", product.buy_sell.to_string().upper()])
        # cashflow breakdown
        self.nvps_.append(["Num Cashflows", product.num_cashflows()])
        for i in range(product.num_cashflows()):
            self.nvps_.append([f"Cashflow {i} Type", product.cashflow(i).product_type])
            self.nvps_.append([f"Cashflow {i} Weight", product.weight(i)])
