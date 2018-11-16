import nixio as nix
import matplotlib.pyplot as plt
import numpy as np
from IPython import embed


def guess_buest_xdim(array):
    data_extent = array.shape
    if len(data_extent) > 2:
        print("Cannot handle more than 2D, sorry!")
    if len(data_extent) == 1:
        return 0

    d1 = a.dimensions[0]
    d2 = a.dimensions[1]

    if d1.dimension_type == nix.DimensionType.Sample:
        return 0
    elif d2.dimension_type == nix.DimensionType.Sample:
        return 1
    else:
        if (d1.dimension_type == nix.DimensionType.Set) and \
           (d2.dimension_type == nix.DimensionType.Range):
            return 1
        elif (d1.dimension_type == nix.DimensionType.Range) and \
             (d2.dimension_type == nix.DimensionType.Set):
            return 0
        else:
            return -1
if __name__ == "__main__":
    dataset = "/Users/jan/zwischenlager/2018-11-05-ab-invivo-1.nix"
    explore_file(dataset)
    explore_block
