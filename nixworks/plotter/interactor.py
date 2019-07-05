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

    def _plot_da(self, data_arrays, maxpoints=100000):
        plotter_list = [suggested_plotter(da) for da in data_arrays]
        xlabel = create_label(plotter_list[0].array.dimensions[plotter_list[0].xdim])
        ylabel = create_label(plotter_list[0].array)
        for a in plotter_list:
            if isinstance(a, LinePlotter):
                a.plot(axis=self.ax, maxpoints=maxpoints)
            else:
                a.plot(axis=self.ax)
            self.populate_artist(a)

        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        # for i, da in enumerate(data_arrays):
        #     self.patches.append(mpatches.Patch(color=str(plotter_list[i].sc.get_color()) ,label=da.name))
        legend1 = plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
                   ncol=1, borderaxespad=0.)
        plt.gca().add_artist(legend1)
        plt.show()
        self.plotter_list = plotter_list

    def interact_da(self, data_arrays, enable_tag=True, maxpoints=100000):
        if not self._check_da_combination(data_arrays):
            raise ValueError('Cannot plot these DataArrays in the same graph.')
        self.arrays = data_arrays
        self.ax.clear()
        self._plot_da(data_arrays, maxpoints=maxpoints)
        def update_da(box):
            if not box['new']:
                idx = self.check_box.index(box['owner'])
                for a in self.mpl_artists[idx]:
                    a.set_visible(False)
                self.fig.canvas.draw_idle()
            else:
                idx = self.check_box.index(box['owner'])
                for a in self.mpl_artists[idx]:
                    a.set_visible(True)
                self.fig.canvas.draw_idle()
        da1d_idx = np.arange(len(data_arrays))
        self.check_box = [widgets.Checkbox(True,description=str(data_arrays[n].name)) for n in da1d_idx]
        for box in self.check_box:
            box.observe(update_da, names='value')
            display.display(box)

        def mark_tag(tag):
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
        if enable_tag:
            tag_drop = self._reverse_search_tag(data_arrays)
            interact(mark_tag, tag=tag_drop)

    def _reverse_search_tag(self, data_arrays):
        # Only for data_arrays within the same block
        tag_list = [None]
        blk = data_arrays[0]._parent
        for da in data_arrays:
            for tag in blk.tags:
                if da in tag.references and tag not in tag_list:
                    tag_list.append(tag)
        return tag_list

    def rescale_axis(self, new_unit, axis='x'):
        pass

    def show_tag(self):
        self.ax.clear()

    def populate_artist(self, plotter):
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
