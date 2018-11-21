import os
import nixio as nix
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from PIL import Image as img

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
            return 0


def suggested_plotter(array):
    if len(array.dimensions) > 3:
        print("cannot handle more than 3D")
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
    elif dim_count == 2:
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
    elif dim_count == 3:
        return ImagePlotter(array)
    else:
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

    def __init__(self, data_array, xdim=-1):
        self.array = data_array
        self.dim_count = len(data_array.dimensions)
        if xdim == -1:
            self.xdim = guess_buest_xdim(self.array)
        elif xdim > 1:
            raise ValueError("EventPlotter: xdim is larger than 2! Cannot plot that kind of data")
        else:
            self.xdim = xdim

    def plot(self, axis=None):
        if axis is None:
            self.fig = plt.figure(figsize=[5.5, 2.])
            self.axis = self.fig.add_axes([0.15, .2, 0.8, 0.75])
            self.axis.set_title(self.array.name)
        if len(self.array.dimensions) == 1:
            return self.plot_1d()
        else:
            return None

    def plot_1d(self):
        data = self.array[:]
        xlabel = create_label(self.array.dimensions[self.xdim])
        if self.array.dimensions[self.xdim].dimension_type == nix.DimensionType.Range and \
           not self.array.dimensions[self.xdim].is_alias:
            ylabel = create_label(self.array)
        else:
            ylabel = ""
        self.axis.scatter(data, np.ones(data.shape))
        self.axis.set_ylim([0.5, 1.5])
        self.axis.set_yticks([1.])
        self.axis.set_yticklabels([])
        self.axis.set_xlabel(xlabel)
        self.axis.set_ylabel(ylabel)
        return self.axis


class CategoryPlotter:

    def __init__(self, data_array, xdim=-1):
        self.array = data_array
        if xdim == -1:
            self.xdim = guess_buest_xdim(self.array)
        elif xdim > 2:
            raise ValueError("CategoryPlotter: xdim is larger than 2! Cannot plot that kind of data")
        else:
            self.xdim = xdim

    def plot(self, axis=None):
        if axis is None:
            self.fig = plt.figure()
            self.axis = self.fig.add_axes([0.15, .2, 0.8, 0.75])
            self.axis.set_title(self.array.name)
        if len(self.array.dimensions) == 1:
            return self.plot_1d()
        elif len(self.array.dimensions) == 2:
            return self.plot_2d()
        else:
            return None

    def plot_1d(self):
        data = self.array[:]
        if self.array.dimensions[self.xdim].dimension_type == nix.DimensionType.Set:
            categories = list(self.array.dimensions[self.xdim].labels)
        else:
            return None
        if categories is None:
            categories = ["Cat-%i"%i for i in range(len(data))]
        ylabel = create_label(self.array)
        self.axis.bar(range(1, len(categories)+1), data, tick_label=categories)
        self.axis.set_ylabel(ylabel)
        return self.axis

    def plot_2d(self):
        data = self.array[:]
        if self.xdim == 1:
            data = data.T

        if self.array.dimensions[self.xdim].dimension_type == nix.DimensionType.Set:
            categories = list(self.array.dimensions[self.xdim].labels)
        if len(categories) == 0:
            categories = ["Cat-%i"%i for i in range(data.shape[self.xdim])]

        if self.array.dimensions[1-self.xdim].dimension_type == nix.DimensionType.Set:
            series_names = list(self.array.dimensions[1-self.xdim].labels)
        if len(series_names) == 0:
            series_names = ["Series-%i"%i for i in range(data.shape[1-self.xdim])]

        bar_width = 1/data.shape[1] * 0.75
        bars = []
        for i in range(data.shape[1]):
            x_values = np.arange(data.shape[0]) +  i * bar_width
            bars.append(self.axis.bar(x_values, data[:,i], width=bar_width, align="center")[0])
        self.axis.set_xticks(np.arange(data.shape[0]) + data.shape[1] * bar_width/2)
        self.axis.set_xticklabels(categories)
        self.axis.legend(bars, series_names, loc=1)
        return self.axis


class ImagePlotter:

    def __init__(self, data_array, xdim=-1):
        self.array = data_array

    def plot(self, axis=None):
        dim_count  = len(self.array.dimensions)
        if axis is None:
            self.fig = plt.figure()
            self.axis = self.fig.add_axes([0.15, .2, 0.8, 0.75])
            self.axis.set_title(self.array.name)
        if dim_count == 2:
            return self.plot_2d()
        elif dim_count == 3:
            return self.plot_3d()
        else:
            return None

    def plot_2d(self):
        data = self.array[:]
        x = self.array.dimensions[0].axis(data.shape[0])
        y = self.array.dimensions[1].axis(data.shape[1])
        xlabel = create_label(self.array.dimensions[0])
        ylabel = create_label(self.array.dimensions[1])
        self.axis.imshow(data, extent=[x[0], x[-1], y[0], y[-1]])
        self.axis.set_xlabel(xlabel)
        self.axis.set_ylabel(ylabel)
        self.axis.set
        return self.axis

    def plot_3d(self):
        if self.array.shape[2] > 3:
            print("cannot plot 3d data with more than 3 channels in the third dim")
            return None
        return self.plot_2d()


class LinePlotter:

    def __init__(self, data_array, xdim=-1):
        self.array = data_array
        self.lines = []
        self.dim_count = len(data_array.dimensions)
        if xdim == -1:
            self.xdim = guess_buest_xdim(self.array)
        elif xdim > 2:
            raise ValueError("LinePlotter: xdim is larger than 2! Cannot plot that kind of data")
        else:
            self.xdim = xdim

    def plot(self, axis=None, maxpoints=100000):
        self.maxpoints = maxpoints
        if axis is None:
            self.fig = plt.figure()
            self.axis = self.fig.add_axes([0.15, .2, 0.8, 0.75])
            self.axis.set_title(self.array.name)
            self.__add_slider()

        dim_count = len(self.array.dimensions)
        if dim_count > 2:
            return
        if dim_count == 1:
            return self.plot_array_1d()
        else:
            return self.plot_array_2d()

    def __add_slider(self):
        steps = self.array.shape[self.xdim] / self.maxpoints
        slider_ax = self.fig.add_axes([0.15, 0.025, 0.8, 0.025])
        self.slider = Slider(slider_ax, 'Slider', 1., steps, valinit=1., valstep=0.25)
        self.slider.on_changed(self.__update)

    def __update(self, val):
        if len(self.lines) > 0:
            minimum = val * self.maxpoints - self.maxpoints
            start = minimum if minimum > 0 else 0
            end = val * self.maxpoints
            self.__draw(start, end)
        self.fig.canvas.draw_idle()

    def __draw(self, start, end):
        if self.dim_count == 1:
            self.__draw_1d(start, end)
        else:
            self.__draw_2d(start, end)

    def __draw_1d(self, start, end):
        if start < 0:
            start = 0
        if end > self.array.shape[self.xdim]:
            end = self.array.shape[self.xdim]

        y = self.array[int(start):int(end)]
        x = np.asarray(self.array.dimensions[self.xdim].axis(len(y), int(start)))

        if len(self.lines) == 0:
            self.lines.extend(self.axis.plot(x, y))
        else:
            self.lines[0].set_ydata(y)
            self.lines[0].set_xdata(x)

        self.axis.set_xlim([x[0], x[-1]])

    def __draw_2d(self, start, end):
        if start < 0:
            start = 0
        if end > self.array.shape[self.xdim]:
            end = self.array.shape[self.xdim]

        x_dimension = self.array.dimensions[self.xdim]
        x = np.asarray(x_dimension.axis(int(end-start), start))
        y_dimension = self.array.dimensions[1-self.xdim]
        labels = y_dimension.labels
        if len(labels) == 0:
            labels =list(map(str, range(self.array.shape[1-self.xdim])))

        for i, l in enumerate(labels):
            if (self.xdim == 0):
                y = self.array[int(start):int(end), i]
            else:
                y = self.array[i, int(start):int(end)]

            if len(self.lines) <= i:
                self.lines.extend(self.axis.plot(x, y, label=l))
            else:
                self.lines[i].set_ydata(y)
                self.lines[i].set_xdata(x)

        self.axis.set_xlim([x[0], x[-1]])

    def plot_array_1d(self):
        self.__draw_1d(0, self.maxpoints)
        xlabel = create_label(self.array.dimensions[self.xdim])
        ylabel = create_label(self.array)
        self.axis.set_xlabel(xlabel)
        self.axis.set_ylabel(ylabel)
        return self.axis

    def plot_array_2d(self):
        self.__draw_2d(0, self.maxpoints)
        xlabel = create_label(self.array.dimensions[self.xdim])
        ylabel = create_label(self.array)
        self.axis.set_xlabel(xlabel)
        self.axis.set_ylabel(ylabel)
        self.axis.legend(loc=1)
        return self.axis


def explore_file(dataset):
    f = nix.File.open(dataset, nix.FileMode.ReadOnly)
    for b in f.blocks:
        explore_block(b)
    f.close()


def explore_block(block):
    plot_array(block.data_arrays["V-1"])
    return
    fig = plt.figure()
    ax = fig.add_subplot(111)
    arrays = {}
    for a in block.data_arrays:
        dim = guess_buest_xdim(a)
        best_dim = a.dimensions[dim]

        if dim > -1 and  best_dim.dimension_type != nix.DimensionType.Set:
            if best_dim.dimension_type == nix.DimensionType.Sample:
                start = best_dim.position_at(0)
                end = best_dim.position_at(a.data_extent[dim]-1)
            elif best_dim.dimension_type == nix.DimensionType.Range:
                start = best_dim.tick_at(0)
                end = best_dim.tick_at(a.data_extent[dim]-1)
            arrays[a.name] = [(start, end)]


    for i, a in enumerate(arrays):
        ax.plot([arrays[a][0][0], arrays[a][0][1]], [i, i], lw=2.)

    tags = {}
    for t in block.tags:
        if len(t.references) == 0:
            continue
        dim = guess_buest_xdim(t.references[0])
        tags[t.name] = [(tag.position[dim])]
        pass
    plt.show()


if __name__ == "__main__":
    testfile = os.path.join("..", "test", "test.nix")
    if not os.path.exists(testfile):
        cwd = os.curdir
        import subprocess
        os.chdir("../test")
        subprocess.check_call(["python", "create_testfile.py"])
        os.chdir(cwd)

    f = nix.File.open(testfile, nix.FileMode.ReadWrite)
    b = f.blocks[0]
    for da in b.data_arrays:
        p = suggested_plotter(da)
        if p is not None:
            p.plot()
            plt.show()
    f.close()
