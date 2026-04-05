import pandas as pd
from typing import Optional, List
from fixedincomelib.date import *
from fixedincomelib.market.data_conventions import (
    DataConvention, DataConventionRegistry, DataConventionRegFunction)
from fixedincomelib.market.registries import IndexFixingsManager, IndexRegistry

### data conventions 

def qfListAllDataConventions() -> dict:
    return DataConventionRegistry().display_all_data_conventions()

def qfClearDataConventionRegistry(convention : Optional[str]='*') -> None:
    if convention == '*':
        DataConventionRegistry().clear()
    else:
        if DataConventionRegistry().exists(convention):
            DataConventionRegistry().erase(convention)

def qfReloadDataConventions() -> None:
    DataConventionRegistry().reset_registry()
    DataConventionRegistry()
    print(f'Data convention is reloaded from file.')

def qfRegisterDataConvention(unique_name : str, type : str, content : dict) -> None:
    content_ = content.copy()
    if type not in content_:
        content_['type'] = type.upper()
    DataConventionRegistry().register(unique_name, content_)
    print(f'{unique_name} is registered.')

def qfDisplayDataConvention(data_convention: str) -> pd.DataFrame:
    this_convention : DataConvention = DataConventionRegistry().get(data_convention)
    return this_convention.display()


### index conventions

def qfListAllIndex() -> dict:
    return IndexRegistry().display_all_indices()

def qfReloadIndex() -> None:
    IndexRegistry().reset_registry()
    IndexRegistry()
    print(f'Indices is reloaded from file.')

def qfClearIndexRegistry(index : Optional[str]='*') -> None:
    if index == '*':
        IndexRegistry().clear()
    else:
        IndexRegistry().erase(index)

def qfRegisterIndex(unique_name : str, ql_name : str) -> None:
    IndexRegistry().register(unique_name, ql_name)
    print(f'{unique_name} is registered.')
    
def qfInsertIndexFixing(index : str, dates : str | List, values : float | List) -> None:
    if isinstance(dates, List):
        assert isinstance(values, List) and len(dates) == len(values)
    else:
        dates, values = [dates], [values]
    for each in zip(dates, values):
        d = Date(each[0])
        IndexFixingsManager().insert_fixing(index, d, each[1])
    print(f'{len(dates)} fixing(s) for {index} is(are) inserted.')

def qfRemoveIndexFixings(index : str, dates : Optional[List|str]=None) -> None:

    if index == '*':
        IndexFixingsManager().clear()
        return

    if dates is None:
        IndexFixingsManager().remove_fixing(index)
        print (f'The fixings of {index} are all removed.')
    else:
        these_dates = dates
        if isinstance(these_dates, str):
            these_dates = [dates]
        for date in these_dates:
            IndexFixingsManager().remove_fixing(index, Date(date))
        print(f'{len(these_dates)} fixings of {index} are moved.')

def qfListIndexFixings(
        index : str, 
        start_date : Optional[str]='*', 
        end_date : Optional[str]='') -> pd.DataFrame:
    
    if not IndexFixingsManager().exists(index):
            return pd.DataFrame(columns=['Date', 'Fixing'])
    
    fixings = IndexFixingsManager().get(index)
    if start_date == '*':
        this_df = pd.DataFrame(fixings.items(), columns=['Date', 'Fixing'])
        this_df['Date'] = this_df['Date'].apply(lambda x: x.ISO())
        return this_df
    if end_date == '':
        this_fixing = IndexFixingsManager().get_fixing(index, Date(start_date))
        return pd.DataFrame([[start_date, this_fixing]], columns=['Date', 'Fixing'])
    these_fixings = []
    for k, v in fixings.items():
        if k >= Date(start_date) and k <= Date(end_date):
            these_fixings.append([k.ISO(), v])
    return pd.DataFrame(these_fixings, columns=['Date', 'Fixing'])

def qfListAllIndexFixings(index : Optional[str]='*') -> pd.DataFrame:
    if index == '*':
        return pd.DataFrame(IndexFixingsManager().get_keys, columns=['Index'])
    else: 
        if not IndexFixingsManager().exists(index):
            return pd.DataFrame(columns=['Date', 'Fixing'])
        fixings = IndexFixingsManager().get(index)
        return pd.DataFrame(fixings.items(), columns=['Date', 'Fixing'])

def qfReloadIndexFixings() -> None:
    IndexFixingsManager().reset_registry()
    IndexFixingsManager()
    print(f'All fxings are reloaded from file.')

        


