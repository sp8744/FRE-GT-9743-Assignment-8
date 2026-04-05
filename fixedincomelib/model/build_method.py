from typing import List, Union, Self, Any
from abc import ABC, abstractmethod
import pandas as pd
from fixedincomelib.utilities.utils import Registry


class BuildMethodBuilderRregistry(Registry):
    
    def __new__(cls) -> Self:
        return super().__new__(cls, '', cls.__name__)

    def register(self, key : Any, value : Any) -> None:
        super().register(key, value)
        self._map[key] = value

class BuildMethod(ABC):

    _version = 1
    _build_method_type = ''

    def __init__(self, target : str, build_method_type : str, content : List|dict) -> None:

        self.bm_target = target
        self.bm_type = build_method_type.upper()
        self.bm_dict = {}
        if isinstance(content, list):
            self.bm_dict = {each[0].upper() : each[1] for each in content}
        else:
            self.bm_dict = {k.upper() : v for k, v in content.items()}
        if 'TARGET' not in self.bm_dict: self.bm_dict['TARGET'] = self.bm_target
        # validation
        valid_keys = self.get_valid_keys()
        for k, v in self.bm_dict.items():
            if k.upper() == 'TARGET':
                assert v != ''
                continue
            if k.upper() not in valid_keys:
                raise Exception(f'{k} is not a valid key.')
        for k in valid_keys:
            if k not in self.bm_dict:
                self.bm_dict[k.upper()] = ''
    
    @abstractmethod
    def calibration_instruments(self) -> set:
        pass

    @abstractmethod
    def additional_entries(self) -> set:
        pass
    
    def get_valid_keys(self) -> set:
        keys = self.additional_entries()
        keys.update(self.calibration_instruments())
        return keys
    
    def __getitem__(self, key : str):
        return self.bm_dict[key.upper()]
    
    @property
    def target(self):
        return self.bm_target
    
    @property
    def type(self):
        return self.bm_type

    @property
    def content(self):
        return self.bm_dict

    def display(self) -> pd.DataFrame:
        return pd.DataFrame(self.bm_dict.items(), columns=['Name', 'Value'])

    def serialize(self) -> dict:
        content = {}
        content['VERSION'] = self._version
        content['TYPE'] = self._build_method_type
        content['TARGET'] = self.bm_dict['TARGET']
        valid_keys = self.get_valid_keys()
        for each in valid_keys:
            content[each.upper()] = self.bm_dict[each.upper()]
        return content

    @classmethod
    def deserialize(cls, input_dict : dict) -> 'BuildMethod':
        input_dict_  = input_dict.copy()
        assert 'VERSION' in input_dict_
        version = input_dict_['VERSION']
        input_dict_.pop('VERSION')
        assert 'TYPE' in input_dict_
        type = input_dict_['TYPE']
        input_dict_.pop('TYPE')
        assert 'TARGET' in input_dict_
        target = input_dict_['TARGET']
        input_dict_.pop('TARGET')
        this_dict = cls.generate_content_based_on_version(version, input_dict_)
        return cls(target, this_dict)

    @classmethod
    def generate_content_based_on_version(cls, version : float, input_dict : dict):

        return {k.upper() : v for k, v in input_dict.items()}


class BuildMethodCollection:

    _version = 1

    def __init__(self, bm_list : List[BuildMethod]) -> None:
        self.bm_col = {}
        for each in bm_list:
            key = f'{each.type.upper()}:{each.target.upper()}'
            self.bm_col[key] = each
        self.num_bms = len(self.bm_col)

    @property
    def num_build_methods(self):
        return self.num_bms
    
    @property
    def items(self):
        return self.bm_col.items()

    def get_build_method_from_build_method_collection(
            self, 
            target : str, 
            type : str) -> BuildMethod:

        key = f'{type.upper()}:{target.upper()}'
        if key not in self.bm_col:
            raise Exception(f'Cannot find {key}.')
        return self.bm_col[key]
    
    def display(self):
        content = []
        for k, _ in self.bm_col.items():
            tokenized = k.split(':')
            content.append(tokenized)
        return pd.DataFrame(content, columns=['Name', 'Value'])
    
    def serialize(self):
        content = {}
        content['VERSION'] = self._version
        content['TYPE'] = 'BUILDMETHODCOLLECTION'
        count = 0
        for _, v in self.bm_col.items():
            content[f'BUILD_MEHTOD_{count}'] = v.serialize()
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
        bm_list = []
        for _, v in input_dict_.items():
            func = BuildMethodBuilderRregistry().get(v['TYPE'])
            bm = func.deserialize(v)
            bm_list.append(bm)
        return cls(bm_list)