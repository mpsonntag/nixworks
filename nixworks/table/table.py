import pandas as pd
import nixio as nix
import numpy as np


def write_to_pandas(dataframe):
    if not isinstance(dataframe, nix.DataFrame):
        raise TypeError("The given object is not a DataFrame")
    tmp_list = []
    tmp_list.extend(dataframe._h5group.group['data'][:])
    li = [list(ite) for ite in tmp_list]  # make all element list
    pd_df = pd.DataFrame(li, columns=[str(n) for n in dataframe.column_names])
    return pd_df


def create_from_pandas(blk, pd_df, name, definition=None):
    """
    This function create Nixpy DataFrame from Pandas DataFrame.

    :param blk: the NIX Block on which the DataFrame will be created on
    :type blk: nix.Block
    :param pd_df: The source Pandas DataFrame
    :type pd_df: pandas.DataFrame
    :param name: The name of the DataFrame
    :type name: str
    :param definition: The definition of the DataFrame
    :type definition: str
    """
    if not isinstance(blk, nix.Block):
        raise TypeError("The first argument must be a NIX Block")
    if not isinstance(pd_df, pd.DataFrame):
        raise TypeError("The second argument must be a Pandas DataFrame")
    if definition is None:
        definition = "created from Pandas"
    content = pd_df.to_numpy()
    col_dict = pd_df.dtypes.to_dict()
    for (k, v) in col_dict.items():
        if v == np.dtype('O'):
            col_dict[k] = str
    df = blk.create_data_frame(name, definition,
                               col_dict=col_dict, data=content)
    return df
