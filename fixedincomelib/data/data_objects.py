from typing import Sequence, Union, List, Any
import pandas as pd
from fixedincomelib.market import (DataConvention, DataConventionRegistry)
from fixedincomelib.data.basics import DataObject, DataObjectDeserializerRegistry


class DataTable(DataObject):

    _version = 1
    _data_shape = 'DATATABLE'

    def __init__(self, 
                 data_type : str, 
                 data_conv : DataConvention|str, 
                 header: Sequence[str], 
                 content: Sequence[Sequence]):
        super().__init__(data_type, data_conv)
        assert len(content) > 0
        assert len(header) == len(content[0])
        self.header_ = list(header)
        self.values_ = list(content)

    @property
    def data_shape(self):
        return self._data_shape

    @property
    def header(self):
        return self.header_

    @property
    def values(self):
        return self.values_

    def display(self) -> pd.DataFrame:
        df = pd.DataFrame(self.values, columns=self.header)
        return df

    def serialize(self) -> dict:
        content = {}
        content['VERSION'] = self._version
        content['DATA_SHAPE'] = self.data_shape
        content['DATA_TYPE'] = self.data_type
        content['DATA_CONVENTION'] = self.data_convention.name
        content['HEADER'] = self.header
        content['VALUES'] = self.values
        return content

    @classmethod        
    def deserialize(cls, input_dict : dict) -> "DataObject":
        assert 'VERSION' in input_dict
        version = input_dict['VERSION']
        assert 'DATA_TYPE' in input_dict
        data_type = input_dict['DATA_TYPE']
        assert 'DATA_CONVENTION' in input_dict
        data_conv = DataConventionRegistry().get(input_dict['DATA_CONVENTION'])
        assert 'HEADER' in input_dict
        header = input_dict['HEADER']
        assert 'VALUES' in input_dict
        values = input_dict['VALUES']
        return cls(data_type, data_conv, header, values)
    
class DataGeneric(DataTable):

    _version = 1
    _data_shape = 'DATAGENERIC'

    def __init__(self, 
                 data_type : str, 
                 data_label : str, 
                 header: Sequence[str], 
                 content: Sequence[Sequence]):
        super().__init__(data_type, data_label, header, content)
        assert len(content) > 0
        assert len(header) == len(content[0])
        self.header_ = list(header)
        self.values_ = list(content)

    @property
    def data_label(self):
        return self.data_convention_

    def serialize(self) -> dict:
        content = {}
        content['VERSION'] = self._version
        content['DATA_SHAPE'] = self.data_shape
        content['DATA_TYPE'] = self.data_type
        content['DATA_LABEL'] = self.data_label
        content['HEADER'] = self.header
        content['VALUES'] = self.values
        return content

    @classmethod        
    def deserialize(cls, input_dict : dict) -> "DataObject":
        assert 'VERSION' in input_dict
        version = input_dict['VERSION']
        assert 'DATA_TYPE' in input_dict
        data_type = input_dict['DATA_TYPE']
        assert 'DATA_LABEL' in input_dict
        data_label = input_dict['DATA_LABEL']
        assert 'HEADER' in input_dict
        header = input_dict['HEADER']
        assert 'VALUES' in input_dict
        values = input_dict['VALUES']
        return cls(data_type, data_label, header, values)


class Data1D(DataObject):

    _version = 1
    _data_shape = 'DATA1D'

    def __init__(
        self,
        data_type: str,
        data_convention: DataConvention,
        axis1: Sequence[str],
        values: Sequence[float]
    ):
        super().__init__(data_type, data_convention)
        if len(axis1) != len(values):
            raise ValueError("`axis1` and `values` must be the same length")
        self.axis1_ = list(axis1)
        self.values_ = list(values)

    @property
    def data_shape(self):
        return self._data_shape

    @property
    def axis1(self):
        return self.axis1_

    @property
    def values(self):
        return self.values_

    def display(self) -> pd.DataFrame:
        df = pd.DataFrame(columns=['axis1', 'values'])
        df['axis1'] = self.axis1
        df['values'] = self.values
        return df

    def serialize(self) -> dict:
        content = {}
        content['VERSION'] = self._version
        content['DATA_SHAPE'] = self.data_shape
        content['DATA_TYPE'] = self.data_type
        content['DATA_CONVENTION'] = self.data_convention.name
        content['AXIS1'] = self.axis1
        content['VALUES'] = self.values
        return content
        
    @classmethod
    def deserialize(cls, input_dict : dict) -> "DataObject":
        assert 'VERSION' in input_dict
        version = input_dict['VERSION']
        assert 'DATA_TYPE' in input_dict
        data_type = input_dict['DATA_TYPE']
        assert 'DATA_CONVENTION' in input_dict
        data_conv = DataConventionRegistry().get(input_dict['DATA_CONVENTION'])
        assert 'AXIS1' in input_dict
        axis1 = input_dict['AXIS1']
        assert 'VALUES' in input_dict
        values = input_dict['VALUES']
        return cls(data_type, data_conv, axis1, values)

class Data2D(DataObject):

    _version = 1
    _data_shape = 'DATA2D'

    def __init__(
        self,
        data_type: str,
        data_convention: DataConvention,
        axis1: Sequence[str],
        axis2: Sequence[str],
        values: Sequence[float]
    ):
        super().__init__(data_type, data_convention)
        if len(axis1) != len(values):
            raise ValueError("`axis1` and `values` must be the same length")
        self.axis1_ = list(axis1)
        self.axis2_ = list(axis2)
        self.values_ = list(values)

    @property
    def data_shape(self):
        return self._data_shape

    @property
    def axis1(self):
        return self.axis1_

    @property
    def axis2(self):
        return self.axis2_

    @property
    def values(self):
        return self.values_

    def display(self) -> pd.DataFrame:
        return pd.DataFrame(self.values, columns=self.axis2, index=self.axis1)

    def serialize(self) -> dict:
        content = {}
        content['VERSION'] = self._version
        content['DATA_SHAPE'] = self.data_shape
        content['DATA_TYPE'] = self.data_type
        content['DATA_CONVENTION'] = self.data_convention.name
        content['AXIS1'] = self.axis1
        content['AXIS2'] = self.axis2
        content['VALUES'] = self.values
        return content
    
    @classmethod
    def deserialize(cls, input_dict : dict) -> "DataObject":
        assert 'VERSION' in input_dict
        version = input_dict['VERSION']
        assert 'DATA_TYPE' in input_dict
        data_type = input_dict['DATA_TYPE']
        assert 'DATA_CONVENTION' in input_dict
        data_conv = DataConventionRegistry().get(input_dict['DATA_CONVENTION'])
        assert 'AXIS1' in input_dict
        axis1 = input_dict['AXIS1']
        assert 'AXIS2' in input_dict
        axis2 = input_dict['AXIS2']
        assert 'VALUES' in input_dict
        values = input_dict['VALUES']
        return cls(data_type, data_conv, axis1, axis2, values)

### register
DataObjectDeserializerRegistry().register(Data1D._data_shape, Data1D.deserialize)
DataObjectDeserializerRegistry().register(Data2D._data_shape, Data2D.deserialize)
DataObjectDeserializerRegistry().register(DataTable._data_shape, DataTable.deserialize)
DataObjectDeserializerRegistry().register(DataGeneric._data_shape, DataGeneric.deserialize)