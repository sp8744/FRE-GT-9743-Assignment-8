from typing import List, Optional, Union, Self, Any, Dict
from abc import ABC, abstractmethod
import pandas as pd
import QuantLib as ql
from fixedincomelib.market import Currency
from fixedincomelib.market.registries import (
    FundingIdentifier,
    FundingIdentifierRegistry,
    IndexRegistry,
)
from fixedincomelib.utilities.utils import Registry


class ValuationParametersBuilderRegistry(Registry):

    def __new__(cls) -> Self:
        return super().__new__(cls, "", cls.__name__)

    def register(self, key: Any, value: Any) -> None:
        super().register(key, value)
        self._map[key] = value


class ValuationParameters(ABC):

    _version = 1
    _vp_type = ""

    def __init__(self, val_param_type: str, content: List | dict) -> None:
        self.vp_type_ = val_param_type.upper()
        self.vp_dict_ = {}
        if isinstance(content, list):
            self.vp_dict_ = {each[0].upper(): each[1] for each in content}
        else:
            self.vp_dict_ = {k.upper(): v for k, v in content.items()}
        # validation
        valid_keys = self.get_valid_keys()
        for k, _ in self.vp_dict_.items():
            if k.upper() not in valid_keys:
                raise Exception(f"{k} is not a valid key.")
        for k in valid_keys:
            if k not in self.vp_dict_:
                self.vp_dict_[k.upper()] = ""

    @abstractmethod
    def get_valid_keys(self) -> set:
        pass

    def __getitem__(self, key: str):
        return self.vp_dict_[key.upper()]

    @property
    def vp_type(self) -> str:
        return self.vp_type_

    @property
    def content(self) -> Dict:
        return self.vp_dict_

    def display(self) -> pd.DataFrame:
        return pd.DataFrame(self.vp_dict_.items(), columns=["Name", "Value"])

    def serialize(self) -> dict:
        content = {}
        content["VERSION"] = self._version
        content["TYPE"] = self._vp_type
        valid_keys = self.get_valid_keys()
        for each in valid_keys:
            content[each.upper()] = self.vp_dict_[each.upper()]
        return content

    @classmethod
    def deserialize(cls, input_dict: dict) -> "ValuationParameters":
        input_dict_ = input_dict.copy()
        assert "VERSION" in input_dict_
        version = input_dict_["VERSION"]
        input_dict_.pop("VERSION")
        assert "TYPE" in input_dict_
        type = input_dict_["TYPE"]
        input_dict_.pop("TYPE")
        this_dict = cls.generate_content_based_on_version(version, input_dict_)
        return cls(this_dict)

    @classmethod
    def generate_content_based_on_version(cls, version: float, input_dict: dict):
        return {k.upper(): v for k, v in input_dict.items()}


class ValuationParametersCollection:

    _version = 1

    def __init__(self, vp_list: List[ValuationParameters]) -> None:
        self.vp_col_ = {}
        has_analytic_vp = False
        for each in vp_list:
            if each.vp_type.upper() == AnalyticValParam._vp_type.upper():
                has_analytic_vp = True
            self.vp_col_[each.vp_type.upper()] = each
        if not has_analytic_vp:
            self.vp_col_[AnalyticValParam._vp_type.upper()] = AnalyticValParam({"Analytic": ""})
        self.num_vps_ = len(self.vp_col_)

    @property
    def num_vp(self):
        return self.num_vps_

    @property
    def items(self):
        return self.vp_col_.items()

    def has_vp_type(self, vp_type: str):
        return vp_type.upper() in self.vp_col_

    def get_vp_from_build_method_collection(self, type: str) -> ValuationParameters:

        if not self.has_vp_type(type):
            raise Exception(f"Cannot find {type}.")
        return self.vp_col_[type.upper()]

    def display(self):
        content = []
        for k, v in self.vp_col_.items():
            content.append(pd.DataFrame([["TYPE", v.vp_type]], columns=["Name", "Value"]))
            content.append(v.display())
            content.append(pd.DataFrame([["", ""]], columns=["Name", "Value"]))
        return pd.concat(content[:-1])

    def serialize(self):
        content = {}
        content["VERSION"] = self._version
        content["TYPE"] = "VALUATION_PARAMETERS_COLLECTION"
        count = 0
        for _, v in self.vp_col_.items():
            content[f"VAL_PARAM_{count}"] = v.serialize()
            count += 1
        return content

    @classmethod
    def deserialize(cls, input_dict: dict):
        input_dict_ = input_dict.copy()
        assert "VERSION" in input_dict_
        version = input_dict_["VERSION"]
        input_dict_.pop("VERSION")
        assert "TYPE" in input_dict_
        type = input_dict_["TYPE"]
        input_dict_.pop("TYPE")
        vp_list = []
        for _, v in input_dict_.items():
            func = ValuationParametersBuilderRegistry().get(v["TYPE"])
            vp = func.deserialize(v)
            vp_list.append(vp)
        return cls(vp_list)


##### derived vp classes


class AnalyticValParam(ValuationParameters):

    _version = 1
    _vp_type = "ANALYTIC PARAMETER"

    def __init__(self, content: Union[List, dict]):
        super().__init__("ANALYTIC PARAMETER", content)

    def get_valid_keys(self) -> set:
        return {"ANALYTIC"}


class FundingIndexParameter(ValuationParameters):

    _version = 1
    _vp_type = "FUNDING INDEX PARAMETER"

    def __init__(self, content: Union[List, dict]):
        super().__init__("FUNDING INDEX PARAMETER", content)
        funding_identifier = self.vp_dict_["FUNDING INDEX"]
        self.funding_index_ = None
        self.funding_identifiers_map_ = {}
        if funding_identifier == "":
            assert self.vp_dict_["CURRENCIES"] != "" and self.vp_dict_["FUNDING INDICES"] != ""
            these_ccys = self.vp_dict_["CURRENCIES"].split(";")
            these_fundingidentifiers = self.vp_dict_["FUNDING INDICES"].split(";")
            assert len(these_ccys) == len(these_fundingidentifiers)
            for ccy, fi in zip(these_ccys, these_fundingidentifiers):
                self.funding_identifiers_map_[Currency(ccy)] = FundingIdentifierRegistry().get(fi)
        else:
            self.funding_identifier_ = FundingIdentifierRegistry().get(funding_identifier)  # check

        ### underlying funding
        self.underlying_funding_identifiers_map_ = {}
        collateral_identifier = self.vp_dict_["UNDERLYING FUNDING INDEX"]
        if collateral_identifier != "":
            assert (
                self.vp_dict_["CURRENCIES"] != ""
                and self.vp_dict_["UNDERLYING FUNDING INDEX"] != ""
            )
            these_ccys = self.vp_dict_["CURRENCIES"].split(";")
            these_fundingidentifiers = self.vp_dict_["UNDERLYING FUNDING INDEX"].split(";")
            assert len(these_ccys) == len(these_fundingidentifiers)
            for ccy, fi in zip(these_ccys, these_fundingidentifiers):
                self.underlying_funding_identifiers_map_[Currency(ccy)] = (
                    FundingIdentifierRegistry().get(fi)
                )

    def get_valid_keys(self) -> set:
        return {"FUNDING INDEX", "CURRENCIES", "FUNDING INDICES", "UNDERLYING FUNDING INDEX"}

    def get_funding_index(self, currency: Optional[Currency] = None) -> FundingIdentifier:
        if currency and currency in self.funding_identifiers_map_:
            return self.funding_identifiers_map_[currency]
        else:
            return self.funding_identifier_

    def get_underlying_funding_by_ccy(self, currency: Currency) -> FundingIdentifier:
        if currency and currency in self.underlying_funding_identifiers_map_:
            return self.underlying_funding_identifiers_map_[currency]
        else:
            return None


### register
ValuationParametersBuilderRegistry().register(AnalyticValParam._vp_type, AnalyticValParam)
ValuationParametersBuilderRegistry().register(FundingIndexParameter._vp_type, FundingIndexParameter)
ValuationParametersBuilderRegistry().register(
    f"{AnalyticValParam._vp_type}_DES", AnalyticValParam.deserialize
)
ValuationParametersBuilderRegistry().register(
    f"{FundingIndexParameter._vp_type}_DES", FundingIndexParameter.deserialize
)
