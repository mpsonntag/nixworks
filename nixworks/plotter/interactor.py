from .plotter import *

from IPython import display
from ipywidgets import interact
import ipywidgets as widgets
import nixio as nix
from nixio import util
import matplotlib.patches as patches


class Interactor:

    def __init__(self):
        fig = plt.figure(figsize=(4, 3))
        ax = fig.add_subplot(111)

        self.fig = fig
        self.ax = ax
        self.plotter_list = []
        # Tag for later references to all plotted objects
        self.mpl_tag = None
        # List for labels
        self.labels = {'x': None, 'y': None, 'x_unit': None, 'y_unit': None}
        # List of line references for later use
        self.arrays = []
        self.check_box = []
        self.mpl_artists = []

    @staticmethod
    def _check_da_combination(data_arrays):
        # checking if the DataArrays can be put in the same graph
        # Checks below not applicable to Images
        if np.any([len(da.dimensions) > 2 and type(suggested_plotter(da))
                   == ImagePlotter for da in data_arrays]):
            return True

        # Use first DataArray as benchmark
        u = data_arrays[0].unit
        bd = guess_best_xdim(data_arrays[0])

        if isinstance(data_arrays[0].dimensions[bd], nix.SetDimension):
            for i, cda in enumerate(data_arrays):
                bd = guess_best_xdim(data_arrays[0])
                if not isinstance(cda.dimensions[bd], nix.SetDimension):
                    return False
        else:
            dim_u = data_arrays[0].dimensions[bd].unit
            if not util.units.is_si(dim_u):
                for i, cda in enumerate(data_arrays):
                    bd = guess_best_xdim(cda)
                    if cda.dimensions[bd].unit != dim_u:
                        return False
            if not util.units.is_si(u):
                for i, cda in enumerate(data_arrays):
                    if cda.unit != u:
                        return False
            for i, cda in enumerate(data_arrays):
                bd = guess_best_xdim(cda)
                if isinstance(cda.dimensions[bd], nix.SetDimension):
                    return False
                if u and not util.units.scalable(cda.unit, u):
                    return False
                if dim_u and not util.units.scalable(cda.dimensions[bd].unit,
                                                     dim_u):
                    return False
        return True

    def _plot_da(self, data_arrays, maxpoints):
        plotter_list = [suggested_plotter(d) for d in data_arrays]

        for a in plotter_list:
            if isinstance(a, LinePlotter):
                a.plot(axis=self.ax, maxpoints=maxpoints)
            else:
                a.plot(axis=self.ax)
            self._populate_artist(a)
        if not np.any([isinstance(pl, ImagePlotter)
                       for pl in plotter_list]):
            xlabel = create_label(plotter_list[0].array.
                                  dimensions[plotter_list[0].xdim])
            ylabel = create_label(plotter_list[0].array)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)

            handle1, legend1 = self.ax.get_legend_handles_labels()
            self.ax.legend(handle1, legend1, loc=0)
        plt.show()
        self.plotter_list = plotter_list

    def interact_da(self, data_arrays, enable_tag=True, enable_xzoom=True,
                    maxpoints=None, enable_yzoom=False):
        # Check if the DataArrays can be plotted together
        if not self._check_da_combination(data_arrays):
            raise ValueError('Cannot plot these DataArrays in the same graph.')
        # Set maxpoints to the no. points of the longest array to be plotted
        # if not being customized
        if maxpoints is None:
            maxpoints = len(max(data_arrays, key=len))
        self.arrays = data_arrays
        self.ax.clear()
        self._plot_da(data_arrays, maxpoints=maxpoints)
        # Setting up checkboxes for interaction of da_visibility
        da1d_idx = np.arange(len(data_arrays))
        self.check_box = [widgets.Checkbox(True, description=str
                          (data_arrays[n].name)) for n in da1d_idx]
        for box in self.check_box:
            box.observe(self._da_visibility, names='value')
            display.display(box)

        # Interactive Legends
        def legend_visibility(cbox):
            if not cbox['new']:
                self.ax.legend().set_visible(False)
                self.fig.canvas.draw_idle()
            else:
                self.ax.legend().set_visible(True)
                self.fig.canvas.draw_idle()

        if not np.any([isinstance(pl, ImagePlotter)
                       for pl in self.plotter_list]):
            legend_box = widgets.Checkbox(True, description='Legends')
            legend_box.observe(legend_visibility, names='value')
            display.display(legend_box)
        # Interactive Tagged Area
        if enable_tag:
            tag_drop = self._reverse_search_tag(data_arrays)
            interact(self._mark_tag, tag=tag_drop)
        # Interactive Sliders for zooming on x-axis
        if enable_xzoom:
            xstart_offset, xend_offset = self.ax.get_xlim()
            x_size = xend_offset - xstart_offset
            x_start_slider = widgets.FloatSlider(0,
                                                 description='X axis start')
            x_end_slider = widgets.FloatSlider(100,
                                               description='X axis end')

            def change_x_start(start):
                start_point = start['new']*x_size/100 + xstart_offset
                end_point = x_end_slider.value*x_size/100 + xstart_offset
                self.ax.set(xlim=(start_point, end_point))
                self.fig.canvas.draw_idle()
            x_start_slider.observe(change_x_start, names='value')

            def change_x_end(end):
                start_point = x_start_slider.value*x_size/1000 + xstart_offset
                end_point = end['new']*x_size/100 + xstart_offset
                self.ax.set(xlim=(start_point, end_point))
                self.fig.canvas.draw_idle()
            x_end_slider.observe(change_x_end, names='value')
            display.display(x_start_slider, x_end_slider)

        if enable_yzoom:
            ystart_offset, yend_offset = self.ax.get_ylim()
            y_size = yend_offset - ystart_offset
            y_start_slider = widgets.FloatSlider(0,
                                                 description='Y axis bottom')
            y_end_slider = widgets.FloatSlider(100,
                                               description='Y axis top')

            def change_y_start(start):
                start_point = start['new'] * y_size / 100 + ystart_offset
                end_point = y_end_slider.value * y_size / 100 + ystart_offset
                self.ax.set(ylim=(start_point, end_point))
                self.fig.canvas.draw_idle()

            y_start_slider.observe(change_y_start, names='value')

            def change_y_end(end):
                start_point = y_start_slider.value * y_size / 1000 + ystart_offset
                end_point = end['new'] * y_size / 100 + ystart_offset
                self.ax.set(ylim=(start_point, end_point))
                self.fig.canvas.draw_idle()

            y_end_slider.observe(change_y_end, names='value')
            display.display(y_start_slider, y_end_slider)

    # Function for setting visibility of the DataArrays
    def _da_visibility(self, box):
        if not box['new']:
            idx = self.check_box.index(box['owner'])
            for a in self.mpl_artists[idx]:
                a.set_visible(False)
            if self.ax.get_legend() and self.ax.get_legend().get_visible():
                handle1, legend1 = self.ax.get_legend_handles_labels()
                self.ax.legend(handle1, legend1, loc=0)
            self.fig.canvas.draw_idle()
        else:
            idx = self.check_box.index(box['owner'])
            for a in self.mpl_artists[idx]:
                a.set_visible(True)
            if self.ax.get_legend() and self.ax.get_legend().get_visible():
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
            for i, da_tag in enumerate(self.arrays):
                if da_tag not in ref:
                    try:
                        self.plotter_list[i].sc.set_visible(False)
                    except AttributeError:
                        self.plotter_list[i].lines.set_visible(False)
                    self.check_box[i].value = False
            x1, = tag.position[0:1]
            y1 = 0
            if tag.extent:
                if self.mpl_tag:
                    self.mpl_tag.remove()
                    self.mpl_tag = None
                if np.any([isinstance(pl, ImagePlotter)
                          for pl in self.plotter_list]):
                    tagged = patches.Rectangle((tag.position[1],
                                               tag.position[0]), tag.extent[0],
                                               tag.extent[1], linewidth=1,
                                               edgecolor='r', facecolor='none')
                    self.ax.add_patch(tagged)
                else:
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

    @staticmethod
    def _reverse_search_tag(data_arrays):
        # Only for data_arrays within the same block
        tag_list = [None]
        blk = data_arrays[0]._parent
        for ref_da in data_arrays:
            for tag in blk.tags:
                if ref_da in tag.references and tag not in tag_list:
                    tag_list.append(tag)
        return tag_list

    def _populate_artist(self, plotter):
        artist = []
        if isinstance(plotter, LinePlotter):
            artist.extend(plotter.lines)
        elif isinstance(plotter, EventPlotter):
            artist.extend(plotter.sc)
        elif isinstance(plotter, CategoryPlotter):
            for bar in plotter.bars:
                artist.extend(bar.patches)
        elif isinstance(plotter, ImagePlotter):
            artist.append(plotter.image)
        else:
            raise TypeError("Invalid Plotter")
        self.mpl_artists.append(artist)

    @staticmethod
    def check_compatible_arrays(base_array, candidate_group=None):
        base_type = base_array.type
        list_of_compatible = []
        for candidate_da in candidate_group.data_arrays:
            if candidate_da.type == base_type:
                list_of_compatible.append(candidate_da)
        return base_type, list_of_compatible

    def group_arrays_by_compatibility(self, region_of_view):
        type_dict = dict()
        for com_da in region_of_view.data_arrays:
            if com_da.type in type_dict.keys():
                continue
            type_key, array_in_group = \
                self.check_compatible_arrays(com_da, region_of_view)
            type_dict[type_key] = array_in_group
        for (k, v) in type_dict.items():
            print("Type:{} No of Arrays:{}".format(k, len(v)))
            for d in v:
                print("        {}".format(d))
