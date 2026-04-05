from typing import List, Optional, Tuple
from fixedincomelib.product.product_interfaces import Product, ProductBuilderRegistry


class ProductPortfolio(Product):

    _version = 1
    _product_type = "PRODUCT_PORTFOLIO"

    def __init__(self, products: List[Product], weights: Optional[List[float]] = None):

        super().__init__()
        self.num_elements_ = len(products)
        assert self.num_elements_ != 0
        if weights is None:
            weights = [1.0] * self.num_elements_
        assert len(weights) == len(products)
        self.elements_: List[Tuple[Product, float]] = list(zip(products, weights))

        # scan portfolio
        ccys = set()
        self.long_or_short_ = []
        self.notional_ = 0.0
        self.first_date_ = products[0].first_date
        self.last_date_ = products[0].last_date
        for product, weight in self.elements_:
            if product.first_date <= self.first_date:
                self.first_date_ = product.first_date
            if product.last_date >= self.last_date:
                self.last_date_ = product.last_date
            ccys.add(product.currency)
            self.long_or_short_.append(product.long_or_short)
            self.notional_ += product.notional * weight
        self.currency_ = list(ccys)

    @property
    def num_elemnts(self):
        return self.num_elements_

    def element(self, i: int) -> Product:
        assert 0 <= i < self.num_elemnts
        return self.elements_[i][0]

    def weight(self, i: int) -> float:
        assert 0 <= i < self.num_elemnts
        return self.elements_[i][1]

    def accept(self, visitor):
        return visitor.visit(self)

    def serialize(self) -> dict:
        content = {}
        content["VERSION"] = self._version
        content["TYPE"] = self._product_type
        count = 0
        weights = []
        for element, weight in self.elements_:
            content[f"PRODUCT_{count}"] = element.serialize()
            weights.append(weight)
            count += 1
        content["WEIGHTS"] = weights
        return content

    @classmethod
    def deserialize(cls, input_dict) -> "Product":
        input_dict_ = input_dict.copy()
        assert "VERSION" in input_dict_
        version = input_dict_["VERSION"]
        input_dict_.pop("VERSION")
        assert "TYPE" in input_dict_
        type = input_dict_["TYPE"]
        input_dict_.pop("TYPE")
        assert "WEIGHTS" in input_dict_
        weights = input_dict_["WEIGHTS"]
        input_dict_.pop("WEIGHTS")
        prod_list = []
        for k, v in input_dict_.items():
            func = ProductBuilderRegistry().get(v["TYPE"])
            prod = func(v)
            prod_list.append(prod)
        return cls(prod_list, weights)
