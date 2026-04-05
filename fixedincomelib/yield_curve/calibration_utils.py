from scipy.optimize import root_scalar
import QuantLib as ql
from fixedincomelib.product import *
from fixedincomelib.valuation.valuation_engine import ValuationEngineProduct
from fixedincomelib.yield_curve.build_method import YieldCurveBuildMethodCommon


class YieldCurveCalibration:

    @staticmethod
    def calibrate_state_var(
        val_engine : ValuationEngineProduct, 
        component_id : ql.Index, 
        state_var_id : int, 
        solver_info : YieldCurveBuildMethodCommon,
        initial_guess : float):
        
        solver : str = solver_info['SOLVER']
        res = root_scalar(
            YieldCurveCalibration._solve_for_par, 
            bracket=(initial_guess -1., initial_guess + 1.), 
            args=(val_engine, component_id, state_var_id), 
            method=solver.lower())
        optimal_state_var = res.root        
        val_engine.model.perturb_model_parameter(component_id, state_var_id, optimal_state_var, True)        
    
    @staticmethod
    def _solve_for_par(x : float, val_engine : ValuationEngineProduct, component_id : ql.Index , state_var_id : int):
        model = val_engine.model
        model.perturb_model_parameter(component_id, state_var_id, x, True)        
        val_engine.calculate_value()
        return val_engine.value