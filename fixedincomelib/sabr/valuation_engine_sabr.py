# from typing import Any, Dict
# from fixedincomelib.sabr import SabrModel
# from fixedincomelib.analytics import SABRCalculator
# from fixedincomelib.market import IndexManager
# from fixedincomelib.valuation import (ValuationEngine, ValuationEngineRegistry)
# from fixedincomelib.product import (LongOrShort, ProductIborCapFloorlet, ProductOvernightCapFloorlet, ProductIborCapFloor, ProductOvernightCapFloor, ProductIborSwaption, ProductOvernightSwaption)
# from fixedincomelib.date.utilities import accrued
# import warnings

# class ValuationEngineIborCapFloorlet(ValuationEngine):

#     def __init__(self, model: SabrModel, valuation_parameters: Dict[str, Any], product: ProductIborCapFloorlet) -> None:
#         super().__init__(model, valuation_parameters, product)
#         self.yieldCurve   = model.subModel
#         raw = valuation_parameters.get("SABR_METHOD")
#         method_input = raw.lower() if isinstance(raw, str) else ""
#         if method_input in ("top-down", "bottom-up"):
#             warnings.warn(
#                 f"SABR_METHOD='{raw}' is not allowed for Ibor products; "
#                 "forcing standard Hagan SABR.",
#                 UserWarning
#             )
#         self.sabrCalc = SABRCalculator(model, method=None)
#         self.currencyCode = product.currency.value.code()
#         self.accrualStart = product.accrualStart
#         self.accrualEnd   = product.accrualEnd
#         self.strikeRate   = product.strike
#         self.optionType   = product.optionType
#         self.notional     = product.notional
#         self.buyOrSell    = 1.0 if product.longOrShort.value == LongOrShort.LONG else -1.

#     def calculateValue(self) -> None:
#         expiry_t = accrued(self.valueDate, self.accrualStart)
#         tenor_t  = accrued(self.accrualStart, self.accrualEnd)

#         forward_rate    = self.yieldCurve.forward(
#             self.product.index,
#             self.accrualStart,
#             self.accrualEnd,
#         )
#         discount_factor = self.yieldCurve.discountFactor(self.product.index, self.accrualEnd)

#         price = self.sabrCalc.option_price(
#             index       = self.product.index,
#             expiry      = expiry_t,
#             tenor       = tenor_t,
#             forward     = forward_rate,
#             strike      = self.strikeRate,
#             option_type = self.optionType,
#         )

#         accrual_factor = accrued(self.accrualStart, self.accrualEnd)
#         pv = self.notional * discount_factor * accrual_factor * price *  self.buyOrSell

#         self.value_ = [self.currencyCode, pv]

# ValuationEngineRegistry().insert(
#     SabrModel.MODEL_TYPE,
#     ProductIborCapFloorlet.prodType,
#     ValuationEngineIborCapFloorlet
# )

# class ValuationEngineOvernightCapFloorlet(ValuationEngine):

#     def __init__(self, model: SabrModel, valuation_parameters: Dict[str, Any], product: ProductOvernightCapFloorlet) -> None:
#         super().__init__(model, valuation_parameters, product)
#         self.yieldCurve   = model.subModel
#         raw = valuation_parameters.get("SABR_METHOD")
#         sabr_method = raw.lower() if isinstance(raw, str) else "" 
#         prod_flag   = "CAPLET"   if sabr_method=="top-down" else None
#         self.sabrCalc     = SABRCalculator(
#             model,
#             method  = valuation_parameters.get("SABR_METHOD", None),
#             product = product,
#             product_type = prod_flag 
#         )
#         self.currencyCode = product.currency.value.code()
#         self.accrualStart = product.effectiveDate
#         self.accrualEnd   = product.maturityDate
#         self.strikeRate   = product.strike
#         self.optionType   = product.optionType
#         self.notional     = product.notional
#         self.buyOrSell    = 1.0 if product.longOrShort.value == LongOrShort.LONG else -1.

#     def calculateValue(self) -> None:
#         expiry_t = accrued(self.valueDate, self.accrualStart)        
#         tenor_t  = accrued(self.accrualStart, self.accrualEnd)

#         forward_rate    = self.yieldCurve.forward(
#             self.product.index,
#             self.accrualStart,
#             self.accrualEnd,
#         )
#         discount_factor = self.yieldCurve.discountFactor(self.product.index, self.accrualEnd)

#         price = self.sabrCalc.option_price(
#             index       = self.product.index,
#             expiry      = expiry_t,
#             tenor       = tenor_t,
#             forward     = forward_rate,
#             strike      = self.strikeRate,
#             option_type = self.optionType,
#         )

#         accrual_factor = accrued(self.accrualStart, self.accrualEnd)
#         pv = self.notional * discount_factor * accrual_factor * price *  self.buyOrSell

#         self.value_ = [self.currencyCode, pv]

# ValuationEngineRegistry().insert(
#     SabrModel.MODEL_TYPE,
#     ProductOvernightCapFloorlet.prodType,
#     ValuationEngineOvernightCapFloorlet
# )

# class ValuationEngineIborCapFloor(ValuationEngine):

#     def __init__(
#         self,
#         model: SabrModel,
#         valuation_parameters: Dict[str, Any],
#         product: ProductIborCapFloor,
#     ) -> None:
#         super().__init__(model, valuation_parameters, product)
#         self.currencyCode = product.currency.value.code()
#         self.caplets      = product.capStream
#         self.engines = [ValuationEngineIborCapFloorlet(model, valuation_parameters, caplet) for caplet in self.caplets.products]

#     def calculateValue(self) -> None:
#         total_pv = 0.0
#         for engine in self.engines:
#             engine.calculateValue()
#             _, pv = engine.value_
#             total_pv += pv
#         self.value_ = [self.currencyCode, total_pv]

# ValuationEngineRegistry().insert(
#     SabrModel.MODEL_TYPE,
#     ProductIborCapFloor.prodType,
#     ValuationEngineIborCapFloor
# )

# class ValuationEngineOvernightCapFloor(ValuationEngine):

#     def __init__(
#         self,
#         model: SabrModel,
#         valuation_parameters: Dict[str, Any],
#         product: ProductOvernightCapFloor,
#     ) -> None:
#         super().__init__(model, valuation_parameters, product)
#         self.currencyCode = product.currency.value.code()
#         self.caplets      = product.capStream
#         self.engines = [ ValuationEngineOvernightCapFloorlet(model, valuation_parameters, caplet) for caplet in self.caplets.products]

#     def calculateValue(self) -> None:
#         total_pv = 0.0
#         for engine in self.engines:
#             engine.calculateValue()
#             _, pv = engine.value_
#             total_pv += pv
#         self.value_ = [self.currencyCode, total_pv]

# ValuationEngineRegistry().insert(
#     SabrModel.MODEL_TYPE,
#     ProductOvernightCapFloor.prodType,
#     ValuationEngineOvernightCapFloor
# )

# class ValuationEngineIborSwaption(ValuationEngine):

#     def __init__(
#         self,
#         model: SabrModel,
#         valuation_parameters: Dict[str, Any],
#         product: ProductIborSwaption,
#     ) -> None:
#         super().__init__(model, valuation_parameters, product)
#         self.yieldCurve   = model.subModel
#         raw = valuation_parameters.get("SABR_METHOD")
#         method_input = raw.lower() if isinstance(raw, str) else ""
#         if method_input in ("top-down", "bottom-up"):
#             warnings.warn(
#                 f"SABR_METHOD='{raw}' is not allowed for Ibor products; "
#                 "forcing standard Hagan SABR.",
#                 UserWarning
#             )
#         self.sabrCalc = SABRCalculator(model, method=None)
#         self.swap          = product.swap
#         self.expiry        = product.expiryDate
#         self.notional      = product.notional
#         self.buyOrSell     = 1.0 if product.longOrShort.value == LongOrShort.LONG else -1.
#         self.currencyCode  = self.swap.currency.value.code()
#         self.strikeRate    = self.swap.fixedRate
#         self.optionType = product.optionType
#         self.optionFlag = 'CAP'   if self.optionType == 'PAYER' else 'FLOOR'

#     def calculateValue(self) -> None:
#         t_exp = accrued(self.valueDate, self.expiry)
#         t_ten = accrued(self.swap.firstDate, self.swap.lastDate)

#         ir_vp = {"FUNDING INDEX": self.swap.index}
#         ir_engine = ValuationEngineRegistry().new_valuation_engine(self.yieldCurve, ir_vp, self.swap)
#         ir_engine.calculateValue()
#         forward_swap_rate = ir_engine.parRate()
#         swap_annuity      = ir_engine.annuity()

#         price = self.sabrCalc.option_price(
#             index       = self.swap.index,
#             expiry      = t_exp,
#             tenor       = t_ten,
#             forward     = forward_swap_rate,
#             strike      = self.strikeRate,
#             option_type = self.optionFlag,
#         )

#         pv = self.notional * swap_annuity * price *  self.buyOrSell
#         self.value_ = [self.currencyCode, pv]

# ValuationEngineRegistry().insert(
#     SabrModel.MODEL_TYPE,
#     ProductIborSwaption.prodType,
#     ValuationEngineIborSwaption
# )

# class ValuationEngineOvernightSwaption(ValuationEngine):

#     def __init__(self, model: SabrModel, valuation_parameters: Dict[str, Any], product: ProductOvernightSwaption) -> None:
#         super().__init__(model, valuation_parameters, product)
#         self.yieldCurve   = model.subModel
#         raw = valuation_parameters.get("SABR_METHOD")
#         method_input = raw.lower() if isinstance(raw, str) else ""
#         if method_input in ("top-down", "bottom-up"):
#             warnings.warn(
#                 f"SABR_METHOD='{raw}' is not allowed for Overnight Swaptions; "
#                 "forcing standard Hagan SABR.",
#                 UserWarning
#             )
#         self.sabrCalc = SABRCalculator(model, method=None)
#         self.swap          = product.swap
#         self.expiry        = product.expiryDate
#         self.notional      = product.notional
#         self.buyOrSell     = 1.0 if product.longOrShort.value == LongOrShort.LONG else -1.
#         self.currencyCode  = self.swap.currency.value.code()
#         self.strikeRate    = self.swap.fixedRate
#         self.optionType = product.optionType
#         self.optionFlag = 'CAP'   if self.optionType == 'PAYER' else 'FLOOR'

#     def calculateValue(self) -> None:
#         t_exp = accrued(self.valueDate, self.expiry)
#         t_ten = accrued(self.swap.firstDate, self.swap.lastDate)

#         ir_vp = {"FUNDING INDEX": self.swap.index}
#         ir_engine = ValuationEngineRegistry().new_valuation_engine(self.yieldCurve, ir_vp, self.swap)
#         ir_engine.calculateValue()
#         forward_swap_rate = ir_engine.parRate()
#         swap_annuity      = ir_engine.annuity()

#         price = self.sabrCalc.option_price(
#             index       = self.swap.index,
#             expiry      = t_exp,
#             tenor       = t_ten,
#             forward     = forward_swap_rate,
#             strike      = self.strikeRate,
#             option_type = self.optionFlag,
#         )

#         pv = self.notional * swap_annuity * price * self.buyOrSell
#         self.value_ = [self.currencyCode, pv]

# ValuationEngineRegistry().insert(
#     SabrModel.MODEL_TYPE,
#     ProductOvernightSwaption.prodType,
#     ValuationEngineOvernightSwaption
# )


# _SABR_ENGINE_MAP = {
#     ProductIborCapFloorlet.prodType:       ValuationEngineIborCapFloorlet,
#     ProductOvernightCapFloorlet.prodType:  ValuationEngineOvernightCapFloorlet,
#     ProductIborCapFloor.prodType:          ValuationEngineIborCapFloor,
#     ProductOvernightCapFloor.prodType:     ValuationEngineOvernightCapFloor,
#     ProductIborSwaption.prodType:          ValuationEngineIborSwaption,
#     ProductOvernightSwaption.prodType:     ValuationEngineOvernightSwaption,
# }

# for prod_type, eng_cls in _SABR_ENGINE_MAP.items():
#     ValuationEngineRegistry().insert(
#         SabrModel.MODEL_TYPE,
#         prod_type,
#         eng_cls
#     )