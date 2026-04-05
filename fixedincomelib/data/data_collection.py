import pandas as pd
from typing import Dict, Tuple, List
from fixedincomelib.data.basics import DataObject, DataObjectDeserializerRegistry
from fixedincomelib.market import data_conventions
from fixedincomelib.market.data_identifiers import DataIdentifier
from fixedincomelib.market.registries import (DataConventionRegistry, DataIdentifierRegistry)

class DataCollection:

    _version = 1

    def __init__(self, data_list : List[DataObject]) -> None:
        self.data_col : dict[str, DataObject] = {}
        for each in data_list:
            self.data_col[each.data_identifier.to_string()] = each
        self.num_data_ = len(self.data_col)
        assert self.num_data_ != 0

    @property
    def num_data(self):
        return self.num_data_

    @property
    def items(self):
        return self.data_col.items()

    def __iter__(self):        
        for _, v in self.items:
            yield v

    def get_data_from_data_collection(self, data_type : str, data_conv : str) -> DataObject:
        func = DataIdentifierRegistry().get(data_type)
        this_data_conv = data_conv
        if DataConventionRegistry().exists(data_conv):
            this_data_conv = DataConventionRegistry().get(data_conv)
        di : DataIdentifier = func(this_data_conv)
        key =  di.to_string()
        if key not in self.data_col:
            raise Exception(f'Cannot find unique id with data type {data_type}, data convention {data_conv}.')
        return self.data_col[key]
    
    def modify_data_collection(self, dc_modifier : 'DataCollection') -> None:
        for key, value in dc_modifier.items:
            self.data_col[key] = value

    def display(self):
        content = []
        for _, v in self.data_col.items():
            name = v.data_convention if isinstance(v.data_convention, str) else v.data_convention.name
            content.append([v.data_shape, v.data_type, name])
        return pd.DataFrame(content, columns=['Data Shape', 'Data Type', 'Data Convention'])
    
    def serialize(self):
        content = {}
        content['VERSION'] = self._version
        content['TYPE'] = 'DATA_COLLECTION'
        count = 0
        for _, v in self.data_col.items():
            content[f'DATA_OBJECT_{count}'] = v.serialize()
            count += 1
        return content
    
    @classmethod
    def deserialize(cls, input_dict : dict):
        input_dict_ = input_dict.copy()
        assert 'VERSION' in input_dict_
        version = input_dict_['VERSION']
        input_dict_.pop('VERSION')
        assert 'TYPE' in input_dict_
        type = input_dict_['TYPE']
        input_dict_.pop('TYPE')
        data_list = []
        for _, v in input_dict_.items():
            assert 'DATA_SHAPE' in v
            func = DataObjectDeserializerRegistry().get(v['DATA_SHAPE'])
            data_list.append(func(v))
        return cls(data_list)
