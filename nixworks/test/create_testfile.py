import nixio as nix
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import multivariate_normal
from matplotlib.widgets import Slider
from PIL import Image as img


def create_1d_sampled(block):
    dt = 0.001
    time = np.arange(500000) * dt
    data = np.random.randn(len(time)) * 0.1 + np.sin(2*np.pi*time) * \
        (np.sin(2 * np.pi * time * 0.0125) * 0.2)
    da2 = block.create_data_array("long 1d data", "test",\
                                  dtype=nix.DataType.Double, data=data)
    da2.label = "intensity"
    da2.unit = "V"
    sd = da2.append_sampled_dimension(dt)
    sd.label = "time"
    sd.unit = "s"


def create_1d_range(block):
    times = np.linspace(0.0, 10., 25)
    values = np.sin(np.pi * 2 * times/2)
    range_da = block.create_data_array("1-d range data", "test", \
                                       dtype=nix.DataType.Double, data=values)
    range_da.unit = "mV"
    range_da.label = "voltage"
    rd = range_da.append_range_dimension(times)
    rd.label = "time"
    rd.unit = "s"


def create_1d_event(block):
    times = np.linspace(0.0, 10., 25)
    times = times + np.random.randn(len(times)) * 0.05
    alias_range_da = block.create_data_array("1d event data", "test", \
                                             dtype=nix.DataType.Double, data=times)
    alias_range_da.append_alias_range_dimension()
    alias_range_da.label = "time"
    alias_range_da.unit = "ms"


def create_1d_category(block):
    months = np.arange(0.,12.,1.)
    temperatures = np.sin(np.pi * 2 * months/12 + 7) * 25.
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", \
              "Oct", "Nov","Dec"]
    set_data = block.create_data_array("1d set", "test", dtype=nix.DataType.Double, \
                                       data=temperatures)
    set_data.label = "temperature"
    set_data.unit = "K"
    sd = set_data.append_set_dimension()
    sd.labels = labels


def create_2d_category(block):
    months = np.arange(0.,12.,1.)
    places = ["A", "B", "C"]
    temperatures = np.sin(np.pi * 2 * months/12 + 7) * 25.
    values = np.zeros((len(months), len(places)))
    for i in range(len(places)):
        values[:, i] = temperatures - 30 + i * 15
    sets_da = block.create_data_array("2d set data", "test", \
                                  dtype=nix.DataType.Double, \
                                  data=values)
    sd = sets_da.append_set_dimension()
    sd.labels = labels
    sd = sets_da.append_set_dimension()
    sd.labels = places

def create_2d_sampled_set(block):
    dt = 0.001
    data = np.zeros((10000,5))
    time = np.arange(10000) * dt
    for i in range(5):
        data[:,i] = np.sin(2*np.pi*time+np.random.randn(1)*np.pi)
    da = block.create_data_array("2d sampled-set", "test", data=data, \
                                 dtype=nix.DataType.Double)
    da.label = "voltage"
    da.unit = "mV"
    da.append_sampled_dimension(dt)
    da.append_set_dimension()
    da.dimensions[0].unit = "s"
    da.dimensions[0].label = "time"


def create_2d_range_set(block):
    times = np.linspace(0.0, 10., 25)
    values = np.random.randn(len(times), 5)
    for i in range(5):
        values[:, i] += np.linspace(0.0, 3.0 * i, len(times))
    range_recordings = block.create_data_array("2d range data", "test", \
                                               dtype=nix.DataType.Double, data=values)
    rd = range_recordings.append_range_dimension(times)
    rd.unit = "s"
    rd.label = "time"
    labels = ["V-1", "V-2", "V-3", "V-4", "V-5"]
    sd = range_recordings.append_set_dimension()
    sd.labels = labels


def create_2d_sampled_sampled(block):
    delta = 0.025
    x = y = np.arange(-3.0, 3.0, delta)
    X, Y = np.meshgrid(x, y)
    pos = np.dstack((X, Y))
    rv1 = multivariate_normal([0.5, -0.2], [[2.0, 0.3], [0.3, 0.5]])
    rv2 = multivariate_normal([0.5, -0.2], [[1.0, 1.7], [0.5, 0.5]])
    z1 = rv1.pdf(pos)
    z2 = rv2.pdf(pos)
    z = z1 - z2

    da = block.create_data_array("difference of Gaussians", "nix.2d.heatmap", data=z)
    d1 = da.append_sampled_dimension(delta)
    d1.label = "x"
    d1.offset = -3.
    d2 = da.append_sampled_dimension(delta)
    d2.label = "y"
    d2.offset = -3.


def create_3d_image(block):
    image = img.open('lena.bmp')
    img_data = np.array(image)
    channels = list(image.mode)
    image_da = block.create_data_array("lena", "nix.image.rgb", data=img_data)
    height_dim = image_da.append_sampled_dimension(1)
    height_dim.label = "height"
    width_dim = image_da.append_sampled_dimension(1)
    width_dim.label = "width"
    color_dim = image_da.append_set_dimension()
    color_dim.labels = channels


def create_test_data():
    f = nix.File.open("test.nix", nix.FileMode.Overwrite)
    b = f.create_block("test","test")
    create_1d_sampled(b)
    create_1d_range(b)
    create_1d_event(b)
    create_1d_category(b)
    create_2d_range_set(b)
    create_2d_sampled_sampled(b)
    create_2d_sampled_set(b)
    create_3d_image(b)
    f.close()


if __name__ == "__main__":
    create_test_data()
