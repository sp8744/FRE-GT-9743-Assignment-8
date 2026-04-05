import pickle
from typing import List
from fixedincomelib.valuation import *
from fixedincomelib.valuation.valuation_engine import ValuationRequest
from fixedincomelib.yield_curve import *


def qfCreateValuationParameters(vp_type: str, content: dict):
    func = ValuationParametersBuilderRegistry().get(vp_type)
    return func(content)


def qfWriteValuationParameterToFile(vp: ValuationParameters, path: str):
    this_dict = vp.serialize()
    with open(path, "wb") as handle:
        pickle.dump(this_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return "DONE"


def qfReadValuationParameterFromFile(path: str):
    with open(path, "rb") as handle:
        this_dict = pickle.load(handle)
        this_type = this_dict["TYPE"]
        this_key = f"{this_type}_DES"
        func = ValuationParametersBuilderRegistry().get(this_key)
        return func(this_dict)


def qfCreateValuationParametersCollection(vp_list: List[ValuationParameters]):
    return ValuationParametersCollection(vp_list)


def qfWriteValuationParametersCollectionToFile(vpc: ValuationParametersCollection, path: str):
    this_dict = vpc.serialize()
    with open(path, "wb") as handle:
        pickle.dump(this_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return "DONE"


def qfReadValuationParametersCollectionFromFile(path: str):
    with open(path, "rb") as handle:
        this_dict = pickle.load(handle)
        return ValuationParametersCollection.deserialize(this_dict)


def qfValueIndexForward(
    model: Model,
    valuation_parameters_collection: ValuationParametersCollection,
    index: str,
    effective_date: str,
    term_or_termination_date: str,
    compounding_method: Optional[str] = "COMPOUND",
):

    this_index = IndexRegistry().get(index)
    engine = ValuationEngineAnalyticIndexRegistry.new_valuation_engine_analytic_index(
        model,
        valuation_parameters_collection,
        this_index,
        Date(effective_date),
        TermOrTerminationDate(term_or_termination_date),
        CompoundingMethod.from_string(compounding_method),
    )

    engine.calculate_value()
    this_v = engine.value()

    return this_v


### test purpose
def qfValueIndexForwardGradient(
    model: Model,
    valuation_parameters_collection: ValuationParametersCollection,
    index: str,
    effective_date: str,
    term_or_termination_date: str,
    gradient: List[np.ndarray],
    compounding_method: Optional[str] = "COMPOUND",
):

    this_index = IndexRegistry().get(index)
    engine = ValuationEngineAnalyticIndexRegistry.new_valuation_engine_analytic_index(
        model,
        valuation_parameters_collection,
        this_index,
        Date(effective_date),
        TermOrTerminationDate(term_or_termination_date),
        CompoundingMethod.from_string(compounding_method),
    )

    engine.calculate_value()
    engine.calculate_risk(gradient)


### valuation engine product


def qfCreateValueReport(
    model: Model,
    product: Product,
    valuation_parameters_collection: ValuationParametersCollection,
    request: str,
):

    this_report = create_value_report(
        model, product, valuation_parameters_collection, ValuationRequest.from_string(request)
    )

    return this_report
