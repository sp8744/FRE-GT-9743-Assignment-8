from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional
import numpy as np
from fixedincomelib.model import Model
from fixedincomelib.product import Product
from fixedincomelib.valuation.valuation_parameters import ValuationParametersCollection
from fixedincomelib.valuation.report import CashflowsReport, PVCashReport


### requests (probably will move to somewhere else)
class ValuationRequest(Enum):

    PV = "pv"
    CASH = "cash"
    PV_DETAILED = "pvdetailed"
    FIRST_ORDER_RISK = "firstorderrisk"
    CASHFLOWS_REPORT = "cashflowsreport"
    PAR_RATE_OR_SPREAD = "parrateorspread"
    PV01 = "pv01"

    @classmethod
    def from_string(cls, value: str) -> "ValuationRequest":
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid token: {value}")

    def to_string(self) -> str:
        return self.value


###
class ValuationEngineProduct(ABC):

    def __init__(
        self,
        model: Model,
        valuation_parameters_collection: ValuationParametersCollection,
        product: Product,
        request: ValuationRequest,
    ):

        self.model_ = model
        self.product_ = product
        self.valuation_parameters_collection_ = valuation_parameters_collection
        self.request_ = request
        self.value_date_ = self.model_.value_date
        self.value_ = 0.0
        self.cash_ = 0.0

    @property
    def model(self) -> Model:
        return self.model_

    @property
    def value_date(self):
        return self.value_date_

    @property
    def value(self) -> float:
        return self.value_

    @property
    def cash(self) -> float:
        return self.cash_

    @abstractmethod
    def calculate_value(self):
        return

    # this should be mandatory as well, @abstractmethod
    # TODO
    @abstractmethod
    def calculate_first_order_risk(
        self, gradient=None, scaler: float = 1.0, accumulate: bool = False
    ) -> None:
        return

    @abstractmethod
    def create_cash_flows_report(self) -> CashflowsReport:
        pass

    @abstractmethod
    def get_value_and_cash(self) -> PVCashReport:
        pass

    @classmethod
    def val_engine_type(cls) -> str:
        return cls.__name__

    # optional
    def par_rate_or_spread(self) -> float:
        raise Exception("This product does not support par rate or spread calculation.")

    # optional
    def pv01(self) -> float:
        raise Exception("This product does not support pv01 calculation.")

    # optional
    def grad_at_par(self) -> np.ndarray:
        pass


class ValuationEngineAnalytics(ABC):

    def __init__(
        self, model: Model, valuation_parameters_collection: ValuationParametersCollection
    ) -> None:
        self.model_ = model
        self.valuation_parameters_collection_ = valuation_parameters_collection
        self.value_date_ = model.value_date

    @abstractmethod
    def calculate_value(self) -> None:
        pass

    @abstractmethod
    def calculate_risk(
        self,
        gradient: List[np.ndarray],
        scaler: Optional[float] = 1.0,
        accumulate: Optional[bool] = False,
    ) -> None:
        pass

    def value(self) -> float:
        pass
