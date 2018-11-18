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

    d1 = array.dimensions[0]
    d2 = array.dimensions[1]

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


def create_label(entity):
    label = ""
    if hasattr(entity, "label"):
        label += (entity.label if entity.label is not None else "")
        if len(label) == 0 and  hasattr(entity, "name"):
            label += entity.name
    if hasattr(entity, "unit") and entity.unit is not None:
        label += " [%s]" % entity.unit
    return label


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

    def __init__(self, data_array):
        self.array = data_array

    def plot(self, xdim=-1, axis=None):
        dim_count = len(self.array.dimensions)
        if dim_count > 2:
            return
        if dim_count == 1:
            return self.plot_array_1d(axis)
        else:
            return self.plot_array_2d(axis)

    def plot_array_1d(self, axis=None):
        if axis is None:
            fig = plt.figure()
            axis = fig.add_subplot(111)
        data = self.array[:]
        dim = self.array.dimensions[0]
        x = dim.axis(len(data))
        xlabel = dim.label + ("" if dim.unit is None else " [%s]" % (dim.unit))
        ylabel = self.array.label + ("" if self.array.unit is None else " [%s]" % (self.array.unit))
        axis.plot(x, data)
        axis.set_xlabel(xlabel)
        axis.set_ylabel(ylabel)
        return axis

    def plot_array_2d(self, xdim=None, axis=None):
        if axis is None:
            fig = plt.figure()
            axis = fig.add_subplot(111)
        if xdim is None:
            xdim = guess_buest_xdim(self.array)
        elif xdim > 2:
            raise ValueError("LinePlotter: xdim is larger than 2! Cannot plot that kind of data")

        data = self.array[:]
        x_dimension = self.array.dimensions[xdim]
        x = x_dimension.axis(data.shape[xdim])
        xlabel = x_dimension.label + ("" if x_dimension.unit is None else " [%s]" % (x_dimension.unit))
        ylabel = self.array.label + ("" if self.array.unit is None else " [%s]" % (self.array.unit))
        y_dimension = self.array.dimensions[1-xdim]
        labels = y_dimension.labels
        if len(labels) == 0:
            labels =list(map(str, range(self.array.shape[1-xdim])))
        print(labels)
        if xdim == 1:
            data = data.T
        for i, l in enumerate(labels):
            axis.plot(x, data[:, i], label=l)
        axis.set_xlabel(xlabel)
        axis.set_ylabel(ylabel)
        axis.legend(loc=1)
        return axis


        pass
def create_test_data():
    filename = "test.nix"
    f = nix.File.open(filename, nix.FileMode.Overwrite)
    b = f.create_block("test","test")
    data = np.zeros((10000,5))
    time = np.arange(10000) * 0.001
    for i in range(5):
        data[:,i] = np.sin(2*np.pi*time+np.random.randn(1)*np.pi)
    da = b.create_data_array("2d sampled-set", "test", data=data, dtype=nix.DataType.Double)
    da.label = "voltage"
    da.unit = "mV"
    da.append_sampled_dimension(0.001)
    da.append_set_dimension()
    da.dimensions[0].unit = "s"
    da.dimensions[0].label = "time"
    f.close()
    return filename


    def plot_array_2d(array):
        pass
if __name__ == "__main__":
    dataset = "/Users/jan/zwischenlager/2018-11-05-ab-invivo-1.nix"
    explore_file(dataset)
    explore_block
