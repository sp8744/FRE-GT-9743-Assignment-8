# import math
# from typing import Any, Dict, List, Tuple
# import numpy as np
# import pandas as pd
# from fixedincomelib.model.model import Model, ModelComponent
# from fixedincomelib.date import Date
# from fixedincomelib.utilities.numerics import Interpolator2D
# from fixedincomelib.yield_curve import YieldCurve
# from fixedincomelib.data import DataCollection, Data2D, Data1D

# class SabrModel(Model):
#     MODEL_TYPE = "IR_SABR"
#     PARAMETERS = ["NORMALVOL", "BETA", "NU", "RHO"]
#     def __init__(
#         self,
#         valueDate: str,
#         dataCollection: DataCollection,
#         buildMethodCollection: List[Dict[str, Any]],
#         ycModel: YieldCurve,
#     ):
#         for bm in buildMethodCollection:
#             tgt  = bm["TARGET"]
#             vals = bm["VALUES"]
#             prod = bm.get("PRODUCT")
#             bm["NAME"] = f"{tgt}-{vals}" + (f"-{prod}" if prod else "")

#         super().__init__(valueDate, self.MODEL_TYPE, dataCollection, buildMethodCollection)
#         self._subModel = ycModel

#     @classmethod
#     def from_curve(
#         cls,
#         valueDate: str,
#         dataCollection: DataCollection,
#         buildMethodCollection: List[Dict[str, Any]],
#         ycModel: YieldCurve
#     ) -> "SabrModel":
#         return cls(valueDate, dataCollection, buildMethodCollection, ycModel)

#     @classmethod
#     def from_data(
#         cls,
#         valueDate: str,
#         dataCollection: DataCollection,
#         buildMethodCollection: List[Dict[str, Any]],
#         ycData: DataCollection,
#         ycBuildMethods: List[Dict[str, Any]]
#     ) -> "SabrModel":
#         zero_curves = []
#         for idx_name, sub in ycData.groupby("INDEX"):
#             d1 = Data1D.createDataObject(
#                 data_type="zero_rate",
#                 data_convention=idx_name,
#                 df=sub[["AXIS1", "VALUES"]]
#             )
#             zero_curves.append(d1)
#         yc_dc = DataCollection(zero_curves)

#         yc = YieldCurve(valueDate, yc_dc, ycBuildMethods)
#         return cls(valueDate, dataCollection, buildMethodCollection, yc)

#     def newModelComponent(self, build_method: Dict[str, Any]) -> ModelComponent:
#         return SabrModelComponent(self.valueDate, self.dataCollection, build_method)

#     def get_sabr_parameters(
#         self,
#         index: str,
#         expiry: float,
#         tenor: float,
#         product_type: str | None = None
#     ) -> Tuple[float, float, float, float, float, float]:
#         suffix = f"-{product_type}".upper() if product_type else ""
#         params = []
#         for p in self.PARAMETERS:
#             key = f"{index}-{p}{suffix}".upper()
#             comp = self.components.get(key)
#             if comp is None:
#                 raise KeyError(f"No SABR component found for {key}")
#             params.append(comp.interpolate(expiry, tenor))
#         nv_key = f"{index}-NORMALVOL{suffix}".upper()
#         nv_comp = self.components[nv_key]
#         return (*params, nv_comp.shift, nv_comp.vol_decay_speed)
    
#     def jacobian(self):
#         """
#         Temporary - Returns an empty Jacobian
#         """
#         J = 0
#         return J
    
#     @property
#     def subModel(self):
#         return self._subModel
    
# class SabrModelComponent(ModelComponent):

#     def __init__(
#         self,
#         valueDate: Date,
#         dataCollection: DataCollection,
#         buildMethod: Dict[str, Any]
#     ) -> None:
        
#         super().__init__(valueDate, dataCollection, buildMethod)
#         self.shift           = float(buildMethod.get("SHIFT", 0.0))
#         self.vol_decay_speed = float(buildMethod.get("VOL_DECAY_SPEED", 0.0))
#         self.product_type    = buildMethod.get("PRODUCT")
#         self.calibrate()

#     def calibrate(self) -> None:

#         param = self.buildMethod_["VALUES"]  

#         md = self.dataCollection.get(param.lower(), self.target_)
#         assert isinstance(md, Data2D)

#         self.axis1 = np.array(md.axis1, dtype=float)  
#         self.axis2 = np.array(md.axis2, dtype=float)   
#         self.grid  = md.values                         

#         method = self.buildMethod_.get("INTERPOLATION", "LINEAR")
#         self._interp2d = Interpolator2D(
#             axis1=self.axis1,
#             axis2=self.axis2,
#             values=self.grid,
#             method=method
#         )

#     def interpolate(self, expiry: float, tenor: float) -> float:
#         return self._interp2d.interpolate(expiry, tenor)