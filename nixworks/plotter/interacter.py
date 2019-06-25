import os
import nixio as nix
import numpy as np
import matplotlib.pyplot as plt
from warnings import warn
from nixio import util
from .plotter import *

from matplotlib.widgets import Slider
import matplotlib.patches as mpatches
from mpl_toolkits.axes_grid1.inset_locator import mark_inset, zoomed_inset_axes
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

class AnyObject(object):
    pass

class InteractHandler(object):
    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        x0, y0 = handlebox.xdescent, handlebox.ydescent
        width, height = handlebox.width, handlebox.height
        patch = mpatches.Rectangle([x0, y0], width, height, facecolor='red',
                                   edgecolor='black', hatch='xx', lw=3,
                                   transform=handlebox.get_transform())
        handlebox.add_artist(patch)
        return patch

def _plot_da(data_arrays, x_axis=None, y_axis=None, enable_tag_list =False):
    plter_type = type(suggested_plotter(data_arrays[0]))
    axes_list = [plter_type(da) for da in data_arrays]
    xlabel = create_label(axes_list[0].array.dimensions[axes_list[0].xdim])
    ylabel = create_label(axes_list[0].array)
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111)
    for a in axes_list:
        a.plot(axis=ax)
        # bd = a.array.dimensions[a.xdim]
        # if isinstance(bd, nix.RangeDimension):
        #     ax.plot(bd.ticks, a.array[:], label=str(a.array.name))
        # else:
        #     ax.plot(np.arange(start=bd.offset, stop=bd.offset+
        #             bd.sampling_interval*len(a.array), step=bd.sampling_interval), a.array[:], label=str(a.array.name))
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if enable_tag_list:
        pass
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=1, borderaxespad=0., handler_map={plt.axhline: InteractHandler()})
    plt.show()
    return fig, ax, axes_list


def _reverse_search_tag(data_arrays):
    # Only for data_arrays within the same block
    tag_list = []
    blk = data_arrays[0]._parent
    for da in data_arrays:
        for tag in blk.tags:
            if da in tag.references:
                tag_list.append(tag)
    return tag_list


def interact_da(data_arrays):
    for d in data_arrays:
        pass

    fig,ax, axes_list = _plot_da(data_arrays)

    def update(box):
        if not box['new']:
            idx = das.index(box['owner'])
            if ax.lines:
                ax.lines[idx].set_visible(False)
            else:
                for i, a in enumerate(axes_list):
                    if  i == idx:
                        a.sc.set_visible(False)
            fig.canvas.draw_idle()
        else:
            idx = das.index(box['owner'])
            if ax.lines:
                ax.lines[idx].set_visible(True)
            else:
                for i, a in enumerate(axes_list):
                    if i == idx:
                        a.sc.set_visible(True)
            fig.canvas.draw_idle()
    da1d_idx = np.arange(len(data_arrays))
    das= [widgets.Checkbox(True,description=str(data_arrays[n].name)) for n in da1d_idx]
    for box in das:
        box.observe(update, names='value')
        display.display(box)
    tag_drop = _reverse_search_tag(data_arrays)

    def zoom_tag(tag):
        x1, = tag.position
        ref = tag.references
        y1 = 0
        if tag.extent:
            plt.axvspan(x1, x1+tag.extent[0], facecolor='#2ca02c', alpha=0.5)
        else:
            plt.plot(x1, y1, 'ro')
    interact(zoom_tag, tag=tag_drop)


def show_tag(show=True):
    pass





