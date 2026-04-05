import numpy as np
from typing import List
from fixedincomelib.utilities import *

def qfCreate1DInterpolator(
    axis1 : np.ndarray | List,
    values : np.ndarray | List,
    interp_method : str,
    extrap_method : str):
    
    interp_method_ = InterpMethod.from_string(interp_method)
    extrap_method_ = ExtrapMethod.from_string(extrap_method)

    return InterpolatorFactory.create_1d_interpolator(
        axis1, values, interp_method_, extrap_method_
    )