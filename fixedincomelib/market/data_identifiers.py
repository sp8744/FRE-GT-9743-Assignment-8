from typing import Tuple
from abc import ABC, abstractmethod
from fixedincomelib.market.data_conventions import *
from fixedincomelib.market.data_conventions import DataConvention


class DataIdentifier(ABC):

    _data_type = ''

    def __init__(self, data_convention : DataConvention|str) -> None:
        self.data_convention_ = data_convention
        self.data_identifier_ = (self._data_type, data_convention if isinstance(data_convention, str) else data_convention.name)
    
    @property
    def data_type(self) -> str:
        return self._data_type
    
    @property
    def data_convention(self) -> DataConvention|str:
        return self.data_convention_
    
    @property
    def data_identifier(self) -> Tuple[str, str]:
        return self.data_identifier_

    def to_string(self):
        name =  self.data_convention if isinstance(self.data_convention, str) else self.data_convention.name
        return f'{self.data_type}:{name}'
    
    @abstractmethod
    def unit(self):
        pass

class DataIdentifierOvernightIndexFuture(DataIdentifier):

    _data_type = 'Overnight Index Future'

    def __init__(self, data_convention: DataConventionRFRFuture) -> None:
        super().__init__(data_convention)

    def unit(self):
        return -0.01

class DataIdentifierOvernightIndexSwap(DataIdentifier):

    _data_type = 'Overnight Index Swap'

    def __init__(self, data_convention: DataConventionRFRSwap) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.0001

class DataIdentifierOvernightIndexBasisSwap(DataIdentifier):

    _data_type = 'Overnight Index Basis Swap'

    def __init__(self, data_convention: DataConventionOvernightIndexBasisSwap) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.0001

class DataIdentifierJump(DataIdentifier):

    _data_type = 'Jump'

    def __init__(self, data_convention: DataConventionJump) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.0001

class DataIdentifierIFR(DataIdentifier):

    _data_type = 'Instantaneous Forward Rate'

    def __init__(self, data_convention: DataConventionIFR) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.0001

class DataIdentifierZeroSpread(DataIdentifier):

    _data_type = 'Spread Zero Rate'

    def __init__(self, data_convention: DataConventionZeroSpread) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.0001

class DataIdentifierSwaptionNormalVolatility(DataIdentifier):

    _data_type = 'Swaption Normal Volatility'

    def __init__(self, data_convention: DataConventionRFRSwaption) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.0001
    
class DataIdentifierSwaptionSABRBeta(DataIdentifier):

    _data_type = 'Swaption SABR Beta'

    def __init__(self, data_convention: DataConventionRFRSwaption) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.01
    
class DataIdentifierSwaptionSABRNu(DataIdentifier):

    _data_type = 'Swaption SABR Nu'

    def __init__(self, data_convention: DataConventionRFRSwaption) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.01
    
class DataIdentifierSwaptionSABRRho(DataIdentifier):

    _data_type = 'Swaption SABR Rho'

    def __init__(self, data_convention: DataConventionRFRSwaption) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.01

class DataIdentifierCapFloorNormalVolatility(DataIdentifier):

    _data_type = 'CapFloor Normal Volatility'

    def __init__(self, data_convention: DataConventionRFRCapFloor) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.0001
    
class DataIdentifierCapFloorSABRBeta(DataIdentifier):

    _data_type = 'CapFloor SABR Beta'

    def __init__(self, data_convention: DataConventionRFRCapFloor) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.01
    
class DataIdentifierCapFloorSABRNu(DataIdentifier):

    _data_type = 'CapFloor SABR Nu'

    def __init__(self, data_convention: DataConventionRFRCapFloor) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.01
    
class DataIdentifierCapFloorSABRRho(DataIdentifier):

    _data_type = 'CapFloor SABR Rho'

    def __init__(self, data_convention: DataConventionRFRCapFloor) -> None:
        super().__init__(data_convention)

    def unit(self):
        return 0.01

class DataIdentifierDataGeneric(DataIdentifier):

    _data_type = 'Data Generic'

    def __init__(self, data_label: str) -> None:
        super().__init__(data_label)

    def unit(self):
        pass

class DataIdentifierFXPair(DataIdentifier):

    _data_type = 'FX Spot Rate'

    def __init__(self, data_label: str) -> None:
        super().__init__(data_label)

    def unit(self):
        return 1.

class DataIdentifierProductBond(DataIdentifier):

    _data_type = 'BOND FIXED'

    def __init__(self, data_label: str) -> None:
        super().__init__(data_label)

    def unit(self):
        return 0.0001


### registration
DataIdentifierRegistry().register(DataIdentifierOvernightIndexFuture._data_type.upper(), DataIdentifierOvernightIndexFuture)
DataIdentifierRegistry().register(DataIdentifierOvernightIndexSwap._data_type.upper(), DataIdentifierOvernightIndexSwap)
DataIdentifierRegistry().register(DataIdentifierOvernightIndexBasisSwap._data_type.upper(), DataIdentifierOvernightIndexBasisSwap)
DataIdentifierRegistry().register(DataIdentifierJump._data_type.upper(), DataIdentifierJump)
DataIdentifierRegistry().register(DataIdentifierIFR._data_type.upper(), DataIdentifierIFR)
DataIdentifierRegistry().register(DataIdentifierZeroSpread._data_type.upper(), DataIdentifierZeroSpread)
DataIdentifierRegistry().register(DataIdentifierSwaptionNormalVolatility._data_type.upper(), DataIdentifierSwaptionNormalVolatility)
DataIdentifierRegistry().register(DataIdentifierSwaptionSABRBeta._data_type.upper(), DataIdentifierSwaptionSABRBeta)
DataIdentifierRegistry().register(DataIdentifierSwaptionSABRNu._data_type.upper(), DataIdentifierSwaptionSABRNu)
DataIdentifierRegistry().register(DataIdentifierSwaptionSABRRho._data_type.upper(), DataIdentifierSwaptionSABRRho)
DataIdentifierRegistry().register(DataIdentifierCapFloorNormalVolatility._data_type.upper(), DataIdentifierCapFloorNormalVolatility)
DataIdentifierRegistry().register(DataIdentifierCapFloorSABRBeta._data_type.upper(), DataIdentifierCapFloorSABRBeta)
DataIdentifierRegistry().register(DataIdentifierCapFloorSABRNu._data_type.upper(), DataIdentifierCapFloorSABRNu)
DataIdentifierRegistry().register(DataIdentifierCapFloorSABRRho._data_type.upper(), DataIdentifierCapFloorSABRRho)
DataIdentifierRegistry().register(DataIdentifierDataGeneric._data_type.upper(), DataIdentifierDataGeneric)
DataIdentifierRegistry().register(DataIdentifierFXPair._data_type.upper(), DataIdentifierFXPair)
DataIdentifierRegistry().register(DataIdentifierProductBond._data_type.upper(), DataIdentifierProductBond)