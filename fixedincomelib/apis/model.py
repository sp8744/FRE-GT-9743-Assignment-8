import pickle
from fixedincomelib.date import *
from fixedincomelib.data import *
from fixedincomelib.model import *
from fixedincomelib.yield_curve import *
from fixedincomelib.yield_curve.model_builder import YieldCurveBuilder


def qfDisplayModelValueDate(model: Model):
    return model.value_date.ISO()


def qfDisplayModelType(model: Model):
    return model.model_type


def qfGetDataCollectionFromModel(model: Model):
    return model.data_collection


def qfGetBuildMethodCollection(model: Model):
    return model.build_method_collection


def qfCreateModel(
    value_date: str,
    model_type: str,
    data_collection: DataCollection,
    build_method_collection: BuildMethodCollection,
):

    model_type_enum = ModelType.from_string(model_type)
    if model_type_enum == ModelType.YIELD_CURVE:
        return YieldCurveBuilder.create_model_yield_curve(
            Date(value_date), data_collection, build_method_collection
        )
    else:
        raise Exception("Currently only support model type yield curve.")


def qfWriteModelObjectToFile(model: Model, path: str):
    this_dict = model.serialize()
    with open(path, "wb") as handle:
        pickle.dump(this_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return "DONE"


def qfReadModelFromFile(path: str):
    with open(path, "rb") as handle:
        this_dict = pickle.load(handle)
        assert "MODEL_TYPE" in this_dict
        func = ModelDeserializerRegistry().get(this_dict["MODEL_TYPE"])
        return func(this_dict)


def qfDiscountFactor(model: Model, index: str, expiry_date: str):

    yc_model: YieldCurve = model
    if yc_model.model_type != ModelType.YIELD_CURVE.to_string():
        yc_model = model.sub_model
    assert yc_model.model_type == ModelType.YIELD_CURVE.to_string()

    if FundingIdentifierRegistry().exists(index):
        index_obj = FundingIdentifierRegistry().get(index)
    else:
        index_obj = IndexRegistry().get(index)
    return yc_model.discount_factor(index_obj, Date(expiry_date))


# dont think this needs to be exposed, just for testing purpose
def qfDiscountFactorGradient(
    model: Model,
    index: str,
    expiry_date: str,
    gradient: List[np.ndarray],
    scaler: Optional[float] = 1.0,
    accmulate: Optional[bool] = False,
) -> np.ndarray:

    yc_model: YieldCurve = model
    if yc_model.model_type != ModelType.YIELD_CURVE.to_string():
        yc_model = model.sub_model
    assert yc_model.model_type == ModelType.YIELD_CURVE.to_string()

    index_obj = IndexRegistry().get(index)

    if len(gradient) == 0:
        yc_model.resize_gradient(gradient)

    yc_model.discount_factor_gradient_wrt_state(
        index_obj, Date(expiry_date), gradient, scaler, accmulate
    )


# display model jacobian
def qfDisplayModelJacobian(model: Model):
    return model.calculate_model_jacobian()
