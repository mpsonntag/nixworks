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

def suggested_plotter(array):
    if len(array.dimensions) > 2:
        print("cannot handle more than 2D")
        return None
    dim_types = [d.dimension_type for d in array.dimensions]
    dim_count = len(dim_types)
    if dim_count == 1:
        if dim_types[0] == nix.DimensionType.Sample:
            return LinePlotter(array)
        elif dim_types[0] == nix.DimensionType.Range:
            if array.dimensions[0].is_alias:
                return EventPlotter(array)
            else:
                return LinePlotter(array)
        elif dim_types[0] == nix.DimensionType.Set:
            return CategoryPlotter(array)
        else:
            return None
    else:
        if dim_types[0] == nix.DimensionType.Sample:
            if dim_types[1] == nix.DimensionType.Sample or \
               dim_types[1] == nix.DimensionType.Range:
                return ImagePlotter(array)
            else:
                return LinePlotter(array)
        elif dim_types[0] == nix.DimensionType.Range:
            if dim_types[1] == nix.DimensionType.Sample or \
               dim_types[1] == nix.DimensionType.Range:
                return ImagePlotter(array)
            else:
                return LinePlotter(array)
        elif dim_types[0] == nix.DimensionType.Set:
            if dim_types[1] == nix.DimensionType.Sample or \
               dim_types[1] == nix.DimensionType.Range:
                return LinePlotter(array)
            else:
                return CategoryPlotter(array)
        else:
            print("Sorry, not a supported combination of dimensions!")
            return None


class EventPlotter:

    def __init__(self, array):
        pass


class CategoryPlotter:

    def __init__(self, array):
        pass

class ImagePlotter:

    def __init__(self, array):
        pass


class LinePlotter:

    def __init__(self, array):
        self.array = data_array

    def plot(self):
        embed()
        dim_count = len(array.dimensions)
        if dim_count > 2:
            return
        if dim_count == 1:
            plot_array_1d(array)
        else:
            plot_array_2d(array)
            dim = guess_buest_xdim(a)
            best_dim = a.dimensions[dim]
        
    def plot_array_1d(array):
        pass

    def plot_array_2d(array):
        pass
if __name__ == "__main__":
    dataset = "/Users/jan/zwischenlager/2018-11-05-ab-invivo-1.nix"
    explore_file(dataset)
    explore_block
