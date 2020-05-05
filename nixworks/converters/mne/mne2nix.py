"""
mne2nix.py

Usage:
  python mne2nix.py [--split-data] [--split-stimuli] <datafile> <montage>

Arguments:
  datafile   Either an EDF file or a BrainVision header file (vhdr).
  montage    Any format montage file supported by MNE.

Flags:
  --split-data      If specified, each channel of raw data is stored in its own
                    separate DataArray.

  --split-stimuli   If specified, each stimulus type (identified by its label)
                    is stored in a separate MultiTag (one MultiTag per
                    stimulus type).


(Requires Python 3)

Command line script for reading EDF and BrainVision files using MNE
(mne-python) and storing the data and metadata into a NIX file.  Supports
reading montage files for recording channel locations.

To include in a script, call the 'write_raw_mne()' and provide a NIX filename
and MNE Raw structure as arguments.

NIX Format layout
=================

Data
----
Raw Data are stored in either a single 2-dimensional DataArray or a collection
of DataArrays (one per recording channel).  The latter makes tagging easier
since MultiTag positions and extents don't need to specify every channel they
reference.  However, creating multiple DataArrays makes file sizes much
bigger.

Stimuli
-------
MNE provides stimulus information through the Raw.annotations dictionary.
Onsets correspond to the 'positions' array and durations correspond to the
'extents' array of the "Stimuli" MultiTag.  If stimulus information is split
by label, each MultiTag uses the label as its name.

Metadata
--------
MNE collects metadata into a (nested) dictionary (Raw.info).  All non-empty
keys are converted into Properties in NIX.  The nested structure of the
dictionary is replicated in NIX by creating child Sections, starting with one
root section with name "Info".

Some extra metadata is kept in the '_raw_extras' private member when loading
from EDF files.  This seems to be missing from the 'Info' dictionary in order
to keep it anonymous (missing keys are 'subject_info', 'meas_date', 'file_id',
and 'meas_id').  The '_raw_extras' are also stored in the NIX file in a
separate Section with name "Extras".

"""
import os
import sys

from collections.abc import Iterable, Mapping

import matplotlib.pyplot as plt
import mne
import nixio as nix
import numpy as np


DATA_BLOCK_NAME = "EEG Data Block"
DATA_BLOCK_TYPE = "Recording"
RAW_DATA_GROUP_NAME = "Raw Data Group"
RAW_DATA_GROUP_TYPE = "EEG Channels"
RAW_DATA_TYPE = "Raw Data"


def plot_channel(data_array, index):
    signal = data_array[index]
    tdim = data_array.dimensions[1]
    datadim = data_array.dimensions[0]

    plt.plot(tdim.ticks, signal, label=datadim.labels[index])
    xlabel = f"({tdim.unit})"
    plt.xlabel(xlabel)
    ylabel = f"{datadim.labels[index]} ({data_array.unit})"
    plt.ylabel(ylabel)
    plt.legend()
    plt.show()


def create_md_tree(section, values, block):
    if values is None:
        return
    for k, val in values.items():
        if val is None:
            continue
        if isinstance(val, Iterable):
            if not val:
                continue
            ndim = np.ndim(val)
            if ndim > 1:
                data_array = block.create_data_array(k, "Multidimensional Metadata",
                                                     data=val)
                for _ in range(ndim):
                    data_array.append_set_dimension()
                prop = section.create_property(k, data_array.id)
                prop.type = str(val.__class__)
                data_array.metadata = section
                continue
            # check element type
            if isinstance(val, Mapping):
                # Create a new Section to hold the metadata found in the
                # dictionary
                subsec = section.create_section(k, str(val.__class__))
                create_md_tree(subsec, val, block)
                continue
            if isinstance(val[0], Mapping):
                # Create a new subsection to hold each nested dictionary as
                # sub-subsections
                subsec = section.create_section(k, str(val.__class__))
                for idx, subd in enumerate(val):
                    subsubsec = subsec.create_section(f"{k}-{idx}",
                                                      str(subd.__class__))
                    create_md_tree(subsubsec, subd, block)
                continue

        try:
            prop = section.create_property(k, val)
        except TypeError:
            # inconsistent iterable types: upgrade to floats
            prop = section.create_property(k, [float(vi) for vi in val])
        prop.type = str(val.__class__)


def write_single_da(mneraw, block):
    # data and times
    data = mneraw.get_data()
    time = mneraw.times

    n_chan = mneraw.info["nchan"]
    print(f"Found {n_chan} channels with {mneraw.n_times} samples per channel")

    data_array = block.create_data_array("EEG Data", RAW_DATA_TYPE, data=data)
    block.groups[RAW_DATA_GROUP_NAME].data_arrays.append(data_array)
    data_array.unit = "V"

    for dim_len in data.shape:
        if dim_len == n_chan:
            # channel labels: SetDimension
            data_array.append_set_dimension(labels=mneraw.ch_names)
        elif dim_len == mneraw.n_times:
            # times: RangeDimension
            # NOTE: EDF always uses seconds
            data_array.append_range_dimension(ticks=time, label="time", unit="s")


def write_multi_da(mneraw, block):
    data = mneraw.get_data()
    time = mneraw.times

    n_chan = mneraw.info["nchan"]
    chan_names = mneraw.ch_names

    print(f"Found {n_chan} channels with {mneraw.n_times} samples per channel")

    # find the channel dimension to iterate over it
    for idx, dim_len in enumerate(data.shape):
        if dim_len == n_chan:
            chan_idx = idx
            break
    else:
        raise RuntimeError("Could not find data dimension that matches number "
                           "of channels")

    for idx, chan_data in enumerate(np.rollaxis(data, chan_idx)):
        ch_name = chan_names[idx]
        data_array = block.create_data_array(ch_name, RAW_DATA_TYPE, data=chan_data)
        block.groups[RAW_DATA_GROUP_NAME].data_arrays.append(data_array)
        data_array.unit = "V"

        # times: RangeDimension
        # NOTE: EDF always uses seconds
        data_array.append_range_dimension(ticks=time, label="time", unit="s")


def separate_stimulus_types(stimuli):
    # separate stimuli based on label
    stim_dict = dict()
    for label, onset, duration in zip(stimuli.description,
                                      stimuli.onset,
                                      stimuli.duration):
        if label not in stim_dict:
            stim_dict[label] = [(label, onset, duration)]
        else:
            stim_dict[label].append((label, onset, duration))
    return stim_dict


def write_stim_tags(mneraw, block, split):
    stimuli = mneraw.annotations

    if split:
        stim_tuples = separate_stimulus_types(stimuli)
        for label, stim in stim_tuples.items():
            label = label.replace("/", "|")
            create_stimulus_multi_tag(stim, block, mneraw, mtagname=label)
    else:
        stim_tuples = [(desc, onset, dur) for desc, onset, dur in zip(stimuli.description,
                                                                      stimuli.onset,
                                                                      stimuli.duration)]
        create_stimulus_multi_tag(stim_tuples, block, mneraw)


def create_stimulus_multi_tag(stimtuples, block, mneraw, mtagname="Stimuli"):
    # check dimensionality of data
    data_shape = block.groups[RAW_DATA_GROUP_NAME].data_arrays[0].shape

    labels = [st[0] for st in stimtuples]
    onsets = [st[1] for st in stimtuples]
    durations = [st[2] for st in stimtuples]

    n_dim = len(data_shape)
    if n_dim == 1:
        positions = onsets
        extents = durations
    else:
        channel_extent = mneraw.info["nchan"] - 1
        positions = [(0, pos) for pos in onsets]
        extents = [(channel_extent, ext) for ext in durations]

    pos_da = block.create_data_array(f"{mtagname} onset", "Stimuli Positions",
                                     data=positions)
    pos_da.append_set_dimension(labels=labels)

    ext_da = block.create_data_array(f"{mtagname} durations", "Stimuli Extents",
                                     data=extents)
    ext_da.append_set_dimension(labels=labels)

    for _ in range(n_dim-1):
        # extra set dimensions for any extra data dimensions (beyond the first)
        pos_da.append_set_dimension()
        ext_da.append_set_dimension()

    stim_mtag = block.create_multi_tag(mtagname, "EEG Stimuli",
                                       positions=pos_da)
    stim_mtag.extents = ext_da
    block.groups[RAW_DATA_GROUP_NAME].multi_tags.append(stim_mtag)

    for data_array in block.groups[RAW_DATA_GROUP_NAME].data_arrays:
        if data_array.type == RAW_DATA_TYPE:
            stim_mtag.references.append(data_array)


def write_raw_mne(nfname, mneraw,
                  split_data_channels=False, split_stimuli=False):
    """
    Writes the provided Raw MNE structure to a NIX file with the given name.

    :param nfname: Name for the NIX file to write to. Existing file will be
    overwritten.
    :param mneraw: An MNE Raw structure (any mne.io.BaseRaw subclass).
    :param split_data_channels: If True, each raw data channel will be stored
    in a separate DataArray.
    :param split_stimuli: If True, stimuli will be split into separate
    MultiTags based on the stimulus type (label).
    :rtype: None
    """
    mne_info = mneraw.info
    extra_info = mneraw._raw_extras

    # Create NIX file
    nix_file = nix.File(nfname, nix.FileMode.Overwrite)

    # Write Data to NIX
    block = nix_file.create_block(DATA_BLOCK_NAME, DATA_BLOCK_TYPE,
                                  compression=nix.Compression.DeflateNormal)
    block.create_group(RAW_DATA_GROUP_NAME, RAW_DATA_GROUP_TYPE)

    if split_data_channels:
        write_multi_da(mneraw, block)
    else:
        write_single_da(mneraw, block)

    if mneraw.annotations:
        write_stim_tags(mneraw, block, split_stimuli)

    # Write metadata to NIX
    # info dictionary
    info_md = nix_file.create_section("Info", "File metadata")
    create_md_tree(info_md, mne_info, block)
    # extras
    if len(extra_info) > 1:
        for idx, emd_i in enumerate(extra_info):
            extras_md = nix_file.create_section(f"Extras-{idx}",
                                                "Raw Extras metadata")
            create_md_tree(extras_md, emd_i, block)
    elif extra_info:
        extras_md = nix_file.create_section("Extras", "Raw Extras metadata")
        create_md_tree(extras_md, extra_info[0], block)

    # all done
    nix_file.close()
    print(f"Created NIX file at '{nfname}'")
    print("Done")


def main():
    args = sys.argv
    if len(args) < 2:
        print("Please provide either a BrainVision vhdr or "
              "an EDF filename as the first argument")
        sys.exit(1)

    split_data = False
    if "--split-data" in args:
        split_data = True
        args.remove("--split-data")

    split_stim = False
    if "--split-stimuli" in args:
        split_stim = True
        args.remove("--split-stimuli")

    data_filename = args[1]
    montage = None
    if len(args) > 2:
        montage = args[2]
        montage = os.path.abspath(montage)
    root, ext = os.path.splitext(data_filename)
    nf_name = root + os.path.extsep + "nix"
    if ext.casefold() == ".edf".casefold():
        mneraw = mne.io.read_raw_edf(data_filename, montage=montage,
                                     preload=True, stim_channel=False)
    elif ext.casefold() == ".vhdr".casefold():
        mneraw = mne.io.read_raw_brainvision(data_filename, montage=montage,
                                             preload=True, stim_channel=False)
    else:
        raise RuntimeError(f"Unknown extension '{ext}'")
    print(f"Converting '{data_filename}' to NIX")
    if split_data:
        print("  Creating one DataArray per channel")
    if split_stim:
        print("  Creating one MultiTag for each stimulus type")

    write_raw_mne(nf_name, mneraw, split_data, split_stim)

    mneraw.close()


if __name__ == "__main__":
    main()
