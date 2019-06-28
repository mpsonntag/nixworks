from .plotter import *

from IPython import display
from ipywidgets import interact
import ipywidgets as widgets


class Interactor:

    def __init__(self):
        # Tag for later references to all plotted objects
        self.mpl_tag = None
        # List of line references for later use
        self.lines = []
        # List for labels
        self.labels= {'x': None, 'y': None}

    def _plot_da(self, data_arrays, enable_tag_list =False):
        plter_type = type(suggested_plotter(data_arrays[0]))
        plotter_list = [plter_type(da) for da in data_arrays]
        xlabel = create_label(plotter_list[0].array.dimensions[plotter_list[0].xdim])
        ylabel = create_label(plotter_list[0].array)
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        for a in plotter_list:
            a.plot(axis=ax)

        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        if enable_tag_list:
            pass
        plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
                   ncol=1, borderaxespad=0.)
        plt.show()
        return fig, ax, plotter_list

    def interact_da(self, data_arrays):
        fig,ax, axes_list = self._plot_da(data_arrays)

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
        tag_drop = self._reverse_search_tag(data_arrays)

        def zoom_tag(tag):
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
                    tagged = plt.axvspan(x1, x1+tag.extent[0], facecolor='#2ca02c', alpha=0.5, zorder=1)
                    self.mpl_tag = tagged
                else:
                    if self.mpl_tag:
                        self.mpl_tag.remove()
                        self.mpl_tag = None
                    tagged = plt.plot(x1, y1, 'ro')
                    self.mpl_tag = tagged
        interact(zoom_tag, tag=tag_drop)

    def _reverse_search_tag(self, data_arrays):
        # Only for data_arrays within the same block
        tag_list = [None]
        blk = data_arrays[0]._parent
        for da in data_arrays:
            for tag in blk.tags:
                if da in tag.references:
                    tag_list.append(tag)
        return tag_list

