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


def _plot_block(blk):
    # Plot all DataArrays, Multitags, Tags in one graph
    if not isinstance(blk, nix.Block):
        raise TypeError
    dali_1d = []
    for idx, da in enumerate(blk.data_arrays):
        if len(da.dimensions) == 1:
            dali_1d.append(da)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    for da in dali_1d:
        ax.plot(np.arange(len(da)), da)
    for idx, tag in enumerate(blk.tags):
        if len(tag.position) == 2:
            plt.plot(tag.position[0][0], tag.position[0][1], 'ro')
        elif len(tag.position) == 1:
            refs = tag.references
            for i, r in enumerate(refs):
                intersect = np.interp(tag.position[i], np.arange(len(r)) , r)
                plt.plot(tag.position[i], intersect, 'ro')
    for mt in blk.multi_tags:
        if len(mt.positions.shape) == 1:
            refs = mt.references
            for i, r in enumerate(refs):
                intersect = np.interp(mt.positions[i], np.arange(len(r)), r)
                plt.plot(mt.positions[i], intersect, 'ro')
    plt.legend()
    plt.show()
    fig.canvas.draw_idle()
    return fig, ax, dali_1d


def interact_block(blk):
    fig,ax, dali = _plot_block(blk)

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
    da1d_idx = np.arange(len(dali))
    das= [widgets.Checkbox(True,description='DataArray - Name:'+dali[n].name) for n in da1d_idx]
    for box in das:
        box.observe(update, names='value')
        display.display(box)


def _guess_dimension(da):
    l = len(da.dimensions)
    return l

def _filter_x(blk, u, dim):
    # for filter which da can be put on the same graph
    if not util.units.is_si(u):
        raise ValueError("Invalid Unit")
    dali = []
    for i, da in enumerate(blk.data_arrays):
        if dim not in [dimen.dimension_type for dimen in da.dimensions]:
            continue
        else:
            bd = guess_best_xdim(da)
            if  da.dimensions[bd].dimension_type != dim:
                bd = 0 if bd == 1 else 1
        if da.unit:
            dau = da.unit[bd]
        if not util.units.scalable(u, dau):
            continue
        dali.append((i, bd))
    return dali