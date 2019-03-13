import pandas as pd
import nixio as nix
import numpy as np


# def write_to_pandas(dataframe):
#     if not isinstance(dataframe, nix.DataFrame):
#         raise (TypeError, "the object is not a DataFrame")
#     tmp_list = []
#     tmp_list.extend(dataframe._h5group.group['data'][:])
#     li = [list(ite) for ite in tmp_list]  # make all element list
#     pd_df = pd.DataFrame(li, columns=[str(n) for n in dataframe.column_names])
#     return pd_df

def write_to_pandas_da(d):
    pass
