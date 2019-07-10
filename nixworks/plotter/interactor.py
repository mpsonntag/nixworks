from .plotter import *

from IPython import display
from ipywidgets import interact
import ipywidgets as widgets
from nixio import util


class Interactor:

    def __init__(self):
        fig = plt.figure(figsize=(4, 3))
        ax = fig.add_subplot(111)
        self.fig = fig
        self.ax = ax
        self.plotter_list= []
        # Tag for later references to all plotted objects
        self.mpl_tag = None
        # List of line references for later use
        self.patches = []
        # List for labels
        self.labels= {'x': None, 'y': None, 'x_unit': None, 'y_unit': None}
        self.arrays = []
        self.check_box = []
        self.mpl_artists = []

    @staticmethod
    def _check_da_combination(data_arrays):
        # checking if the DataArrays can be put in the same graph
        u = data_arrays[0].unit
        if not util.units.is_si(u):
            raise ValueError("Invalid Unit")
        bd = guess_best_xdim(data_arrays[0])
        if isinstance(data_arrays[0].dimensions[bd], nix.SetDimension):
            for i, da in enumerate(data_arrays):
                bd = guess_best_xdim(data_arrays[0])
                if not isinstance(da.dimensions[bd], nix.SetDimension):
                    return False
        else:
            dim_u = data_arrays[0].dimensions[bd].unit
            for i, da in enumerate(data_arrays):
                bd = guess_best_xdim(data_arrays[0])
                if isinstance(da.dimensions[bd], nix.SetDimension):
                    return False
                if u and not util.units.scalable(da.unit, u):
                    return False
                if dim_u and not util.units.scalable(da.dimensions[bd].unit, dim_u):
                    return False
        return True

    def _plot_da(self, data_arrays, maxpoints):
        plotter_list = [suggested_plotter(da) for da in data_arrays]
        xlabel = create_label(plotter_list[0].array.dimensions[plotter_list[0].xdim])
        ylabel = create_label(plotter_list[0].array)

        for a in plotter_list:
            if isinstance(a, LinePlotter):
                a.plot(axis=self.ax, maxpoints=maxpoints)
            else:
                a.plot(axis=self.ax)
            self._populate_artist(a)

        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        # for i, da in enumerate(datal_arrays):
        #     self.patches.append(mpatches.Patch(color=str(plotter_list[i].sc.get_color()) ,label=da.name))
        handle1, legend1 = self.ax.get_legend_handles_labels()
        self.ax.legend(handle1, legend1, loc=0)
        plt.show()
        self.plotter_list = plotter_list

    def interact_da(self, data_arrays, enable_tag=True, enable_xzoom=True, maxpoints=None):
        # Check if the DataArrays can be plotted together
        if not self._check_da_combination(data_arrays):
            raise ValueError('Cannot plot these DataArrays in the same graph.')
        # Set maxpoints to the no. points of the longest array to be plotted if not being customized
        if maxpoints is None:
            maxpoints = len(max(data_arrays, key=len))
        self.arrays = data_arrays
        self.ax.clear()
        self._plot_da(data_arrays, maxpoints=maxpoints)
        # TODO: Add the for-Image Interactive function
        if np.any([isinstance(p, ImagePlotter) for p in self.plotter_list]):
            raise TypeError('Please use the interact function specific for Images')

        # Setting up checkboxes for interaction of da_visibility
        da1d_idx = np.arange(len(data_arrays))
        self.check_box = [widgets.Checkbox(True,description=str(data_arrays[n].name)) for n in da1d_idx]
        for box in self.check_box:
            box.observe(self._da_visibility, names='value')
            display.display(box)

        # Interactive Legends
        def legend_visibility(box):
            if not box['new']:
                self.ax.legend().set_visible(False)
                self.fig.canvas.draw_idle()
            else:
                self.ax.legend().set_visible(True)
                self.fig.canvas.draw_idle()
        legend_box = widgets.Checkbox(True, description='Legends')
        legend_box.observe(legend_visibility, names='value')
        display.display(legend_box)
        # Interactive Tagged Area
        if enable_tag:
            tag_drop = self._reverse_search_tag(data_arrays)
            interact(self._mark_tag, tag=tag_drop)
        # Interactive Sliders for zooming on x-axis
        if enable_xzoom:
            x_start = widgets.FloatSlider(self.ax.get_xlim()[0], description='X axis start')
            x_end = widgets.FloatSlider(self.ax.get_xlim()[1], description='X axis end')
            def change_x_start(start):
                self.ax.set(xlim=(start['new'], x_end.value))
                self.fig.canvas.draw_idle()
            x_start.observe(change_x_start, names='value')
            def change_x_end(end):
                self.ax.set(xlim=(x_start.value, end['new']))
                self.fig.canvas.draw_idle()
            x_end.observe(change_x_end, names='value')
            display.display(x_start, x_end)

    # Function for setting visibility of the DataArrays
    def _da_visibility(self, box):
        handle1, legend1 = self.ax.get_legend_handles_labels()
        if not box['new']:
            idx = self.check_box.index(box['owner'])
            for a in self.mpl_artists[idx]:
                a.set_visible(False)
            handle1 = self.ax.get_legend_handles_labels()[0]
            self.ax.legend(handle1, legend1, loc=0)
            self.fig.canvas.draw_idle()
        else:
            idx = self.check_box.index(box['owner'])
            for a in self.mpl_artists[idx]:
                a.set_visible(True)
            handle1, legend1 = self.ax.get_legend_handles_labels()
            self.ax.legend(handle1, legend1, loc=0)
            self.fig.canvas.draw_idle()

    def _mark_tag(self, tag):
        if tag is None:
            if self.mpl_tag:
                self.mpl_tag.remove()
                self.mpl_tag = None
        else:
            ref = tag.references
            for i, da in enumerate(self.arrays):
                if da not in ref:
                    try:
                        self.plotter_list[i].sc.set_visible(False)
                    except AttributeError:
                        self.plotter_list[i].lines.set_visible(False)
                    self.check_box[i].value = False
            x1, = tag.position
            y1 = 0
            if tag.extent:
                if self.mpl_tag:
                    self.mpl_tag.remove()
                    self.mpl_tag = None
                tagged = plt.axvspan(x1, x1 + tag.extent[0],
                                     facecolor='#2ca02c', alpha=0.5,
                                     zorder=1)
                self.mpl_tag = tagged
            else:
                if self.mpl_tag:
                    self.mpl_tag.remove()
                    self.mpl_tag = None
                tagged = plt.plot(x1, y1, 'ro')
                self.mpl_tag = tagged

    def _reverse_search_tag(self, data_arrays):
        # Only for data_arrays within the same block
        tag_list = [None]
        blk = data_arrays[0]._parent
        for da in data_arrays:
            for tag in blk.tags:
                if da in tag.references and tag not in tag_list:
                    tag_list.append(tag)
        return tag_list

    def _populate_artist(self, plotter):
        artist = []
        if isinstance(plotter, LinePlotter):
            artist.extend(plotter.lines)
        elif isinstance(plotter, EventPlotter):
            artist.extend(plotter.sc)
        elif isinstance(plotter, CategoryPlotter):
            for b in plotter.bars:
                artist.extend(b.patches)
        elif isinstance(plotter, ImagePlotter):
            artist.append(plotter.image)
        else:
            raise TypeError("Invalid Plotter")
        self.mpl_artists.append(artist)

    def group_da(self, files):
        for f in files:
            self.group_da_file(f)

    def group_da_file(self, f):
        for b in f.blocks:
            self.group_da_blk(b)
        f.close()

    @staticmethod
    def group_da_blk(block):
        arrays = {}
        for a in block.data_arrays:
            dim = guess_best_xdim(a)
            best_dim = a.dimensions[dim]

            if dim > -1 and best_dim.dimension_type != nix.DimensionType.Set:
                if best_dim.dimension_type == nix.DimensionType.Sample:
                    start = best_dim.position_at(0)
                    end = best_dim.position_at(a.data_extent[dim] - 1)
                elif best_dim.dimension_type == nix.DimensionType.Range:
                    start = best_dim.tick_at(0)
                    end = best_dim.tick_at(a.data_extent[dim] - 1)
                else:
                    start = 1
                    end = 1
                arrays[a.name] = [(start, end)]
