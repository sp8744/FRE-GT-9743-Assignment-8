from os import name
from re import U
from fixedincomelib.date import Date
from fixedincomelib.market import (
    DataConventionRegistry,
)
from fixedincomelib.market.data_conventions import (
    DataConventionBondFixed,
)
from fixedincomelib.utilities import Registry
from typing import Self, Any
import pandas as pd
import pickle
import json


class BondSpecsRegistry(Registry):

    def __new__(cls) -> Self:
        return super().__new__(cls, "bond_specs", "BondSpecs")

    def register(self, key: str, value: Any) -> None:
        super().register(key, value)
        self._map[key] = BondSpecs.create_bond_spec(key, value)

class BondSpecs:
    """
    Bond Specs
    """

    NAME = "NAME"
    ISIN = "ISIN"
    BOND_CONVENTION = "BOND_CONVENTION"
    ISSUE_DATE = "ISSUE_DATE"
    FIRST_ACCRUAL_DATE = "FIRST_ACCRUAL_DATE"
    FIRST_COUPON_DATE = "FIRST_COUPON_DATE"
    MATURITY_DATE = "MATURITY_DATE"
    COUPON_RATE = "COUPON_RATE"
    REDEMPTION_PERCENTAGE = "REDEMPTION_PERCENTAGE"

    def __init__(
        self,
        name: str,
        isin: str,
        bond_conv: str,
        issue_date: Date,
        first_accrual_date: Date,
        first_coupon_date: Date,
        maturity_date: Date,
        coupon_rate: float,
        redemption_percentage: float,
    ):
        self.name_ = name
        self.isin_ = isin
        self.bond_conv_: DataConventionBondFixed = DataConventionRegistry().get(bond_conv)
        self.issue_date_ = issue_date
        self.first_accrual_date_ = first_accrual_date
        self.first_coupon_date_ = first_coupon_date
        self.maturity_date_ = maturity_date
        self.coupon_rate_ = coupon_rate
        self.redemption_percentage_ = redemption_percentage

        self.info = {
            BondSpecs.NAME: self.name_,
            BondSpecs.ISIN: self.isin_,
            BondSpecs.BOND_CONVENTION: self.bond_conv_.name,
            BondSpecs.ISSUE_DATE: self.issue_date_.ISO(),
            BondSpecs.FIRST_ACCRUAL_DATE: self.first_accrual_date_.ISO(),
            BondSpecs.FIRST_COUPON_DATE: self.first_coupon_date_.ISO(),
            BondSpecs.MATURITY_DATE: self.maturity_date_.ISO(),
            BondSpecs.COUPON_RATE: self.coupon_rate_,
            BondSpecs.REDEMPTION_PERCENTAGE: self.redemption_percentage_,
        }

    @classmethod
    def create_bond_spec(cls, key: str, parameters: dict):

        return cls(
            name=key,
            isin=parameters[BondSpecs.ISIN],
            bond_conv=parameters[BondSpecs.BOND_CONVENTION],
            issue_date=Date(parameters[BondSpecs.ISSUE_DATE]),
            first_accrual_date=Date(parameters[BondSpecs.FIRST_ACCRUAL_DATE]),
            first_coupon_date=Date(parameters[BondSpecs.FIRST_COUPON_DATE]),
            maturity_date=Date(parameters[BondSpecs.MATURITY_DATE]),
            coupon_rate=float(parameters[BondSpecs.COUPON_RATE]),
            redemption_percentage=float(parameters[BondSpecs.REDEMPTION_PERCENTAGE]),
        )

    def __getitem__(self, key):
        return self.info[key]

    @property
    def name(self):
        return self.name_

    def display(self):
        return pd.DataFrame(self.info.items(), columns=["Field", "Value"])

    def serialize(self, path):
        # only support json and pickle
        assert path.endswith(".json") or path.endswith(
            ".pkl"
        ), "Only .json and .pkl formats are supported for serialization."
        if path.endswith(".json"):
            with open(path, "w") as handle:
                json.dump(self.info, handle, indent=4)
        else:
            with open(path, "wb") as handle:
                pickle.dump(self.info, handle, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def deserialize(cls, input_path: str) -> "BondSpecs":
        if input_path.endswith(".json"):
            with open(input_path, "r") as handle:
                input_dict = json.load(handle)
        elif input_path.endswith(".pkl"):
            with open(input_path, "rb") as handle:
                input_dict = pickle.load(handle)
        else:
            raise ValueError(f"Unsupported file format: {input_path}")

        return cls(
            name=input_dict["NAME"],
            isin=input_dict["ISIN"],
            bond_conv=input_dict["BOND_CONVENTION"],
            issue_date=Date(input_dict["ISSUE_DATE"]),
            first_accrual_date=Date(input_dict["FIRST_ACCRUAL_DATE"]),
            first_coupon_date=Date(input_dict["FIRST_COUPON_DATE"]),
            maturity_date=Date(input_dict["MATURITY_DATE"]),
            coupon_rate=float(input_dict["COUPON_RATE"]),
            redemption_percentage=float(input_dict["REDEMPTION_PERCENTAGE"]),
        )
