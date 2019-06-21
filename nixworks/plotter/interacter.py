import os
import nixio as nix
import numpy as np
import matplotlib.pyplot as plt
from warnings import warn
from nixio import util
from .plotter import *

from matplotlib.widgets import Slider
from PIL import Image as img

from IPython import embed, display
from ipywidgets import interact, interactive, fixed, interact_manual, Checkbox
import ipywidgets as widgets


def line_interact(da):
    data = da[:]
    p = LinePlotter(da)
    p.plot()
    fig = p.fig
    ax = p.axis
    line, = ax.get_lines()


    def update(val=1.0):
        line.set_ydata(val*data)
        line.set_xdata(val*data)
        fig.canvas.draw_idle()

    interact(update, val=(0,2.0));


def _plot_block(blk, da_idx=None, x_unit='s'):
    # Plot all DataArrays, Multitags, Tags in one graph
    if not isinstance(blk, nix.Block):
        raise TypeError
    filter_list = _filter_da(blk, x_unit)
    fig, ax = plot_da(blk.data_arrays[filter_list])


    # for idx, tag in enumerate(blk.tags):
    #     if len(tag.position) == 2:
    #         plt.plot(tag.position[0][0], tag.position[0][1], 'ro')
    #     elif len(tag.position) == 1:
    #         refs = tag.references
    #         for i, r in enumerate(refs):
    #             intersect = np.interp(tag.position[i], np.arange(len(r)) , r)
    #             plt.plot(tag.position[i], intersect, 'ro')
    # for mt in blk.multi_tags:
    #     if len(mt.positions.shape) == 1:
    #         refs = mt.references
    #         for i, r in enumerate(refs):
    #             intersect = np.interp(mt.positions[i], np.arange(len(r)), r)
    #             plt.plot(mt.positions[i], intersect, 'ro')
    plt.legend()
    plt.show()
    fig.canvas.draw_idle()
    return fig, ax


def interact_block(blk):
    fig,ax = _plot_block(blk)

    def update(box):
        print(box)
        if not box['new']:
            idx = das.index(box['owner'])
            ax.lines[idx].set_visible(False)
            fig.canvas.draw_idle()
        else:
            idx = das.index(box['owner'])
            ax.lines[idx].set_visible(True)
            fig.canvas.draw_idle()
    da1d_idx = np.arange(len(blk.data_arrays))
    das= [widgets.Checkbox(True,description='DataArray - Name:'+blk.data_arrays[n].name) for n in da1d_idx]
    for box in das:
        box.observe(update, names='value')
        display.display(box)


def _guess_dimension(da):
    l = len(da.dimensions)
    return l

def _filter_da(blk, u):
    # for filter which da can be put on the same graph
    if not util.units.is_si(u):
        raise ValueError("Invalid Unit")
    dali = []
    for i, da in enumerate(blk.data_arrays):
        bd = guess_best_xdim(da)
        if isinstance(da.dimensions[bd], nix.SetDimension):
            continue
        if not da.dimensions[bd].unit:
            continue
        if not util.units.scalable(da.dimensions[bd].unit, u):
            continue

        dali.append(i)
    return dali


def plot_da(data_arrays, x_axis=None, y_axis=None):
    plter_type = type(suggested_plotter(data_arrays[0]))
    axes_list = [plter_type(da) for da in data_arrays]
    xlabel = create_label(axes_list[0].array.dimensions[axes_list[0].xdim])
    ylabel = create_label(axes_list[0].array)
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111)
    for a in axes_list:
        bd = a.array.dimensions[a.xdim]
        if isinstance(bd, nix.RangeDimension):
            ax.plot(bd.ticks, a.array[:])
        else:
            ax.plot(np.arange(start=bd.offset, stop=bd.offset+
                    bd.sampling_interval*len(a.array), step=bd.sampling_interval), a.array[:])
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    fig.legend()
    plt.show()
    return fig, ax

def interact_da(data_arrays):
    fig,ax = plot_da(data_arrays)

    def update(box):
        if not box['new']:
            idx = das.index(box['owner'])
            ax.lines[idx].set_visible(False)
            fig.canvas.draw_idle()
        else:
            idx = das.index(box['owner'])
            ax.lines[idx].set_visible(True)
            fig.canvas.draw_idle()
    da1d_idx = np.arange(len(data_arrays))
    das= [widgets.Checkbox(True,description='DataArray - Name:'+data_arrays[n].name) for n in da1d_idx]
    for box in das:
        box.observe(update, names='value')
        display.display(box)



