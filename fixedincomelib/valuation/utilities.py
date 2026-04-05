from typing import Any
import numpy as np
from fixedincomelib.model import *
from fixedincomelib.product import *
from fixedincomelib.valuation.report import PVCashReport, RiskReprt
from fixedincomelib.valuation.valuation_engine_registry import *
from fixedincomelib.valuation.valuation_parameters import ValuationParametersCollection


def create_value_report(
    model : Model, 
    product : Product,
    valuation_parameters_collection: ValuationParametersCollection,
    request : ValuationRequest) -> Any:

    engine = ValuationEngineProductRegistry.new_valuation_engine(
        model, 
        product,
        valuation_parameters_collection, 
        request)

    engine.calculate_value()    
    if request in [ValuationRequest.PV_DETAILED, ValuationRequest.PV, ValuationRequest.CASH]:
        v : PVCashReport = engine.get_value_and_cash()
        if request == ValuationRequest.PV_DETAILED:
            return v
        else:
            return v.pv if request == ValuationRequest.PV else v.cash
    elif request == ValuationRequest.FIRST_ORDER_RISK:
        return risk_calculation(engine)
    elif request == ValuationRequest.CASHFLOWS_REPORT:
        return engine.create_cash_flows_report()
    elif request == ValuationRequest.PAR_RATE_OR_SPREAD:
        return engine.par_rate_or_spread()
    elif request == ValuationRequest.PV01:
        return engine.pv01()
    else:
        raise Exception(f'Request is not currently supported.')


def risk_calculation(engine : ValuationEngineProduct):
    gradient = []
    engine.calculate_first_order_risk(gradient, 1., False)
    # dV/dX^M = dV/dX^I \cdot J^{-1}, where J is the model jacobian dX^M/dX^I 
    # step 1: flatten gradient
    gradient_flat = np.concatenate(gradient, axis=0) # dim : 1 x len(X^I)
    # step 2: get model (lazy) jacobian
    engine.model.calculate_model_jacobian()
    # step 3: inverse model jacobian (what is this algorithm ?)
    jacobian_inv = np.linalg.inv(engine.model.model_jacobian)
    # step 4: final risk
    risk = np.dot(gradient_flat, jacobian_inv)
    # step 5: make a nice report
    risk_report = RiskReprt(engine.model.risk_postprocess(risk))
    return risk_report

