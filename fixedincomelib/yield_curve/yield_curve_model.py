import numpy as np
from typing import List
from scipy.linalg import block_diag

from fixedincomelib.valuation.valuation_engine_registry import ValuationEngineProductRegistry

from ..date import *
from ..data import *
from ..market import *
from ..model import *
from ..product import *
from ..utilities import *
from ..valuation import *
from ..yield_curve.build_method import (
    YieldCurveIndexBuildMethod,
    YieldCurveFundingBuildMethod,
)

# from ..valuation.valuation_engine import ValuationRequest


class YieldCurve(Model):

    _version = 1
    _model_type = ModelType.YIELD_CURVE

    def __init__(
        self,
        value_date: Date,
        data_collection: DataCollection,
        build_method_collection: BuildMethodCollection,
    ) -> None:
        super().__init__(value_date, self._model_type, data_collection, build_method_collection)

    def fx_rate(
        self,
        index: ql.Index,
        expiry_date: Date,
        funding_identifier: Optional[FundingIdentifier] = None,
    ):
        this_component: YieldCurveModelComponent = self.retrieve_model_component(index)
        return this_component.fx_rate(expiry_date, funding_identifier)

    def fx_rate_gradient_wrt_state(
        self,
        index: ql.Index,
        expiry_date: Date,
        gradient_vector: List[np.ndarray],
        funding_identifier: Optional[FundingIdentifier] = None,
        scaler: Optional[float] = 1.0,
        accumulate: Optional[bool] = False,
    ):

        this_component: YieldCurveModelComponent = self.retrieve_model_component(index)
        component_index = self.component_indices[index.name()]
        this_gradient = gradient_vector[component_index]
        this_component.fx_rate_gradient_wrt_state(
            expiry_date, this_gradient, funding_identifier, scaler, accumulate
        )

    ### old world: df : component => exp(-\int_0^t r(s) ds)
    ### new world : df (sofr-1b-flat-over sofr-1b) => exp(-\int_0^t s(u)du) * df(index)

    def discount_factor(
        self, index: ql.Index, expiry_date: Date, underlying_funding: Optional[ql.Index] = None
    ):
        df = 1.0
        if type(index) == FundingIdentifier and index.reference_index is not None:
            ref_component: YieldCurveModelComponent = self.retrieve_model_component(
                index.reference_index
            )
            df = ref_component.discount_factor(expiry_date)
        this_component: YieldCurveModelComponent = self.retrieve_model_component(index)
        return df * this_component.discount_factor(expiry_date)

    def discount_factor_gradient_wrt_state(
        self,
        index: ql.Index,
        expiry_date: Date,
        gradient_vector: List[np.ndarray],
        scaler: Optional[float] = 1.0,
        accumulate: Optional[bool] = False,
    ):

        # df = df(tar) * df(ref)
        # if index is funding and it has reference:
        #   - ddf/ddf(index) = df(ref) * grad df(tar)
        #   - ddf/ddf(ref) = df(tar) * grad df(ref)
        # otherwise,
        #   df = df(tar)
        #   - ddf/ddf(tar) = grad df(Tar)

        if type(index) == FundingIdentifier and index.reference_index is not None:
            ref_component: YieldCurveModelComponent = self.retrieve_model_component(
                index.reference_index
            )
            ref_component_index = self.component_indices[index.reference_index.name()]
            this_ref_gradient = gradient_vector[ref_component_index]
            df_ref = ref_component.discount_factor(expiry_date)
            this_component: YieldCurveModelComponent = self.retrieve_model_component(index)
            component_index = self.component_indices[index.name()]
            this_gradient = gradient_vector[component_index]
            df_tar = this_component.discount_factor(expiry_date)
            # - ddf/ddf(index) = df(ref) * grad df(tar)
            this_component.discount_factor_gradient_wrt_state(
                expiry_date, this_gradient, df_ref * scaler, accumulate
            )
            # - ddf/ddf(ref) = df(tar) * grad df(ref)
            ref_component.discount_factor_gradient_wrt_state(
                expiry_date, this_ref_gradient, df_tar * scaler, accumulate
            )
        else:
            # just df(tar)
            this_component: YieldCurveModelComponent = self.retrieve_model_component(index)
            component_index = self.component_indices[index.name()]
            this_gradient = gradient_vector[component_index]
            this_component.discount_factor_gradient_wrt_state(
                expiry_date, this_gradient, scaler, accumulate
            )

    def serialize(self) -> dict:
        content = {}
        content["VERSION"] = YieldCurve._version
        content["MODEL_TYPE"] = YieldCurve._model_type.to_string()
        content["VALUE_DATE"] = self.value_date.ISO()
        content["BUILD_METHOD_COLLECTION"] = self.build_method_collection.serialize()
        content["DATA_COLLECTION"] = self.data_collection.serialize()
        return content

    @classmethod
    def deserialize(cls, input_dict: dict) -> "YieldCurve":
        input_dict_ = input_dict.copy()
        assert "VERSION" in input_dict_
        version = input_dict_["VERSION"]
        assert "MODEL_TYPE" in input_dict_
        model_type = input_dict_["MODEL_TYPE"]
        assert "VALUE_DATE" in input_dict_
        value_date = Date(input_dict_["VALUE_DATE"])
        bmc = BuildMethodCollection.deserialize(input_dict_["BUILD_METHOD_COLLECTION"])
        dc = DataCollection.deserialize(input_dict_["DATA_COLLECTION"])
        # find modelbuilder
        func = ModelBuilderRegistry().get(model_type)
        return func(value_date, dc, bmc)

    def calculate_model_jacobian(self):
        if self.is_jacobian_calculated_:
            return
        # WARNING: WE DO NOT ALLOW A MIXTURE OF CALIBRATION INSTRUMENTS AND STATE DATA FOR NOW
        only_state_data = False
        jacobian_pre = [None] * self.num_components
        for target_name, yc_component in self.components_.items():
            index = self.component_indices[target_name]
            calib_prod = yc_component.calibration_product
            calib_funding = yc_component.calibration_funding
            if len(calib_prod) == 0:
                # no calibration, just using state data
                # jacobian is identity
                jacobian_pre[index] = np.diag(np.ones(yc_component.num_state_data))
                only_state_data = True
                continue
            # calculate calibration instrument gradient
            grads = []
            for _, (prod, funding) in enumerate(zip(calib_prod, calib_funding)):
                fi_vp = FundingIndexParameter({"Funding Index": funding})
                vpc = ValuationParametersCollection([fi_vp])
                engine = ValuationEngineProductRegistry.new_valuation_engine(
                    self, prod, vpc, ValuationRequest.PV_DETAILED
                )
                engine.calculate_value()
                grads.append(np.concatenate(engine.grad_at_par()))
            jacobian_pre[index] = grads  # np.concatenate(grads, axis=0)

        self.model_jacobian_ = (
            block_diag(*jacobian_pre) if only_state_data else np.concatenate(jacobian_pre, axis=0)
        )
        self.is_jacobian_calculated_ = True

    def risk_postprocess(self, grad: np.ndarray):
        frame = [None] * self.num_components
        for target_name, yc_component in self.components_.items():
            index = self.component_indices[target_name]
            frame[index] = yc_component.market_data
        frame = np.concatenate(frame, axis=0)
        return np.concatenate([frame, grad.reshape(len(frame), 1)], axis=1)


class YieldCurveModelComponent(ModelComponent):

    def __init__(
        self,
        value_date: Date,
        component_identifier: ql.Index,
        state_data: np.ndarray,
        build_method: YieldCurveIndexBuildMethod | YieldCurveFundingBuildMethod,
        calibration_product: Optional[List[Product]] = [],
        calibration_funding: Optional[List[Product]] = [],
        market_data: Optional[List] = [],
    ) -> None:

        super().__init__(
            value_date,
            component_identifier,
            state_data,
            build_method,
            calibration_product,
            calibration_funding,
            market_data,
        )
        assert len(state_data) == 2
        self.num_state_data_ = len(state_data[0])
        self.interpolator_ = InterpolatorFactory.create_1d_interpolator(
            state_data[0],
            state_data[1],
            self.build_method.interpolation_method,
            self.build_method.extrapolation_method,
        )

    def perturb_model_parameter(
        self, parameter_id: int, perturb_size: float, override_parameter: Optional[bool] = False
    ):
        super().perturb_model_parameter(parameter_id, perturb_size, override_parameter)
        self.interpolator_ = InterpolatorFactory.create_1d_interpolator(
            self.state_data[0],
            self.state_data[1],
            self.build_method.interpolation_method,
            self.build_method.extrapolation_method,
        )

    def fx_rate(self, expiry_date: Date, funding_identifier: FundingIdentifier):
        # TODO: i am only going to fetch spot for now
        #       i think we shall also provide fx forward rate here too @wanling
        time_to_expiry = accrued(self.value_date, expiry_date)
        fx_spot = self.state_data_interpolator.interpolate(time_to_expiry)
        return fx_spot

    def fx_rate_gradient_wrt_state(
        self,
        expiry_date: Date,
        gradient_vector: np.ndarray,
        funding_identifier: FundingIdentifier,
        scaler: Optional[float] = 1.0,
        accumulate: Optional[bool] = False,
    ):

        # TODO: similarly, we shall extend this for forward fx risk as well
        time_to_expiry = accrued(self.value_date, expiry_date)
        grad = self.state_data_interpolator.gradient_wrt_ordinate(time_to_expiry)
        grad *= scaler
        if accumulate:
            assert len(gradient_vector) == len(grad)
            for i in range(len(gradient_vector)):
                gradient_vector[i] += grad[i]
        else:
            gradient_vector[:] = grad

    def discount_factor(self, expiry_date: Date):
        time_to_expiry = accrued(self.value_date, expiry_date)
        exponent = self.state_data_interpolator.integrate(0.0, time_to_expiry)
        return np.exp(-exponent)

    def discount_factor_gradient_wrt_state(
        self,
        expiry_date: Date,
        gradient_vector: np.ndarray,
        scaler: Optional[float] = 1.0,
        accumulate: Optional[bool] = False,
    ):

        time_to_expiry = accrued(self.value_date, expiry_date)
        exponent = self.state_data_interpolator.integrate(0.0, time_to_expiry)

        # df risk w.r.t state variables
        d_df_d_exponent = -np.exp(-exponent)
        grad = self.state_data_interpolator.gradient_of_integrated_value_wrt_ordinate(
            0, time_to_expiry
        )
        grad *= d_df_d_exponent * scaler

        # finalize
        if accumulate:
            assert len(gradient_vector) == len(grad)
            for i in range(len(gradient_vector)):
                gradient_vector[i] += grad[i]
        else:
            gradient_vector[:] = grad

    @property
    def state_data_interpolator(self) -> Interpolator1D:
        return self.interpolator_

    @property
    def num_state_data(self) -> int:
        return self.num_state_data_


### registry
ModelDeserializerRegistry().register(YieldCurve._model_type.to_string(), YieldCurve.deserialize)
