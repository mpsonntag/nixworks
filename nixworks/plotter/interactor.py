from .plotter import *

from IPython import display
from ipywidgets import interact
import ipywidgets as widgets
from nixio import util


class Interactor:

    def __init__(self):
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        self.fig = fig
        self.ax = ax
        self.plotter_list= []
        # Tag for later references to all plotted objects
        self.mpl_tag = None
        # List of line references for later use
        self.lines = []
        # List for labels
        self.labels= {'x': None, 'y': None}

    @staticmethod
    def _check_da_combination(data_arrays):
        # checking if the DataArrays can be put in the same graph
        u = data_arrays[0].unit
        if not util.units.is_si(u):
            raise ValueError("Invalid Unit")
        bd = guess_best_xdim(data_arrays[0])
        dim_u = data_arrays[0].dimensions[bd].unit
        if isinstance(data_arrays[0].dimensions[bd], nix.SetDimension):
            for i, da in enumerate(data_arrays):
                bd = guess_best_xdim(data_arrays[0])
                if not isinstance(da.dimensions[bd], nix.SetDimension):
                    return False
        else:
            for i, da in enumerate(data_arrays):
                bd = guess_best_xdim(data_arrays[0])
                if isinstance(da.dimensions[bd], nix.SetDimension):
                    return False
                if u and not util.units.scalable(da.unit, u):
                    return False
                if dim_u and not util.units.scalable(da.dimensions[bd].unit, dim_u):
                    return False
        return True

    def _plot_da(self, data_arrays, x_name=None, y_name=None):
        plotter_list = [suggested_plotter(da) for da in data_arrays]
        xlabel = create_label(plotter_list[0].array.dimensions[plotter_list[0].xdim])
        ylabel = create_label(plotter_list[0].array)

        for a in plotter_list:
            a.plot(axis=self.ax)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
                   ncol=1, borderaxespad=0., handler_map={plt.axhline: InteractHandler()})
        plt.show()
        self.plotter_list = plotter_list


    def interact_da(self, data_arrays, enable_tag=True):
        if not self._check_da_combination(data_arrays):
            raise ValueError('Cannot plot these DataArrays in the same graph.')
        self._plot_da(data_arrays)
        def update_da(box):
            if not box['new']:
                idx = das.index(box['owner'])
                if self.ax.lines:
                    self.ax.lines[idx].set_visible(False)
                else:
                    for i, a in enumerate(self.plotter_list):
                        if  i == idx:
                            a.sc.set_visible(False)
                self.fig.canvas.draw_idle()
            else:
                idx = das.index(box['owner'])
                if self.ax.lines:
                    self.ax.lines[idx].set_visible(True)
                else:
                    for i, a in enumerate(self.plotter_list):
                        if i == idx:
                            a.sc.set_visible(True)
                self.fig.canvas.draw_idle()
        da1d_idx = np.arange(len(data_arrays))
        das= [widgets.Checkbox(True,description=str(data_arrays[n].name)) for n in da1d_idx]
        for box in das:
            box.observe(update_da, names='value')
            display.display(box)
        tag_drop = self._reverse_search_tag(data_arrays)

        def mark_tag(tag):
            if tag is None:
                if self.mpl_tag:
                    self.mpl_tag.remove()
                    self.mpl_tag = None
            else:
                x1, = tag.position
                y1 = 0
                if tag.extent:
                    if self.mpl_tag:
                        self.mpl_tag.remove()
                        self.mpl_tag = None
                    tagged = plt.axvspan(x1, x1+tag.extent[0], facecolor='#2ca02c', alpha=0.5, zorder=1)
                    self.mpl_tag = tagged
                else:
                    if self.mpl_tag:
                        self.mpl_tag.remove()
                        self.mpl_tag = None
                    tagged = plt.plot(x1, y1, 'ro')
                    self.mpl_tag = tagged

        if enable_tag:
            interact(mark_tag, tag=tag_drop)

    def _reverse_search_tag(self, data_arrays):
        # Only for data_arrays within the same block
        tag_list = [None]
        blk = data_arrays[0]._parent
        for da in data_arrays:
            for tag in blk.tags:
                if da in tag.references:
                    tag_list.append(tag)
        return tag_list


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

