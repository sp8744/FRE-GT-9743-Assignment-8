from fixedincomelib.market.basics import Currency
from fixedincomelib.model.model import Model
from fixedincomelib.product.product_portfolio import ProductPortfolio
from fixedincomelib.valuation.report import CashflowsReport, PVCashReport
from fixedincomelib.valuation.valuation_engine_registry import ValuationEngineProductRegistry
from fixedincomelib.valuation.valuation_parameters import (
    AnalyticValParam,
    ValuationParametersCollection,
)
from fixedincomelib.valuation.valuation_engine import ValuationEngineProduct, ValuationRequest
from fixedincomelib.model.model import ModelType


class ValuationEngineProductPortfolio(ValuationEngineProduct):

    def __init__(
        self,
        model: Model,
        valuation_parameters_collection: ValuationParametersCollection,
        product: ProductPortfolio,
        request: ValuationRequest,
    ):
        super().__init__(model, valuation_parameters_collection, product, request)
        from typing import List

        self.engines_: List[ValuationEngineProduct] = []
        self.weights = []
        self.currencies = []
        for prod, weight in product.elements_:
            self.weights.append(weight)
            self.currencies.append(prod.currency)
            self.engines_.append(
                ValuationEngineProductRegistry().new_valuation_engine(
                    model, prod, valuation_parameters_collection, request
                )
            )

    @classmethod
    def val_engine_type(cls) -> str:
        return cls.__name__

    def calculate_value(self):

        self.value_ = 0.0
        self.cash_ = 0.0

        self.aggregated_value_ = {}
        self.aggregated_cash_ = {}
        for i, engine in enumerate(self.engines_):
            engine.calculate_value()
            this_ccy: Currency = self.currencies[i]
            if this_ccy in self.aggregated_value_:
                self.aggregated_value_[this_ccy] += self.weights[i] * engine.value
                self.aggregated_cash_[this_ccy] += self.weights[i] * engine.cash
            else:
                self.aggregated_value_[this_ccy] = self.weights[i] * engine.value
                self.aggregated_cash_[this_ccy] = self.weights[i] * engine.cash

    def calculate_first_order_risk(
        self, gradient=None, scaler: float = 1.0, accumulate: bool = False
    ) -> None:

        local_grad = []
        self.model_.resize_gradient(local_grad)

        for i, engine in enumerate(self.engines_):
            engine.calculate_first_order_risk(local_grad, scaler * self.weights[i], True)

        self.model_.resize_gradient(gradient)
        if accumulate:
            for i in range(len(gradient)):
                gradient[i] += local_grad[i]
        else:
            gradient[:] = local_grad

    def get_value_and_cash(self) -> PVCashReport:
        report = PVCashReport(self.currencies)
        for ccy, value in self.aggregated_value_.items():
            report.set_pv(ccy, value)
            report.set_cash(ccy, self.aggregated_cash_[ccy])
        return report

    def create_cash_flows_report(self) -> CashflowsReport:
        ## TODO:
        return


ValuationEngineProductRegistry().register(
    (
        ModelType.YIELD_CURVE.value,
        ProductPortfolio._product_type,
        AnalyticValParam._vp_type,
    ),
    ValuationEngineProductPortfolio,
)
