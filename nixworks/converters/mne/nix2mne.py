"""
nix2mne.py

Usage:
  python nix2mne.py <nixfile>

Arguments:
  nixfile   Path to the NIX file to read.


(Requires Python 3)

Command line script for reading NIX files into an MNE structure (mne-python).
NIX file should have been created using the mne2nix.py script/module.  This
reader expects certain objects relationships and names to exist in order to
load all data and metadata successfully.  Refer to the "NIX Format Layout" in
the mne2nix.py module for details.

To include in a script, call the 'import_nix()' and provide a NIX filename.
"""
import sys

import mne
import nixio as nix
import numpy as np


DATA_BLOCK_NAME = "EEG Data Block"
DATA_BLOCK_TYPE = "Recording"
RAW_DATA_GROUP_NAME = "Raw Data Group"
RAW_DATA_GROUP_TYPE = "EEG Channels"
RAW_DATA_TYPE = "Raw Data"


TYPE_MAP = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "tuple": tuple,
    "list": list,
    "numpy.float64": np.float64,
    "numpy.ndarray": np.array,
}


def convert_prop_type(prop):
    prop_type = prop.type[8:-2]
    prop_val = prop.values
    if len(prop_val) == 1:
        prop_val = prop_val[0]

    return TYPE_MAP[prop_type](prop_val)


def md_to_dict(section):
    s_dict = dict()
    for prop in section.props:
        s_dict[prop.name] = convert_prop_type(prop)

    if section.type[8:-2] == "mne.transforms.Transform":
        to = s_dict["to"]
        fro = s_dict["from"]
        # trans = s_dict["trans"]
        trans = section.referring_data_arrays[0][:]
        return mne.Transform(fro=fro, to=to, trans=trans)

    for sec in section.sections:
        if sec.name == "chs":
            # make a list of dictionaries for the channels
            chan_list = list()
            for chan_sec in sec.sections:
                chan_list.append(md_to_dict(chan_sec))
                s_dict[sec.name] = chan_list
        else:
            s_dict[sec.name] = md_to_dict(sec)

    return s_dict


def merge_data_arrays(arrays):
    rows = [a[:] for a in arrays]
    return np.array(rows)


def create_mne_annotations(mtags):
    onset = list()
    duration = list()
    description = list()
    for mtag in mtags:
        pos_shape = mtag.positions.shape
        if len(pos_shape) == 1:
            onset.extend(mtag.positions)
            duration.extend(mtag.extents)
        else:
            onset.extend([p[1] for p in mtag.positions])
            duration.extend([e[1] for e in mtag.extents])

        description.extend(mtag.positions.dimensions[0].labels)

    return mne.Annotations(onset=onset,
                           duration=duration,
                           description=description)


def import_nix(nix_filename):
    """
    Import a NIX file (generated with mne2nix.py) into an MNE Raw structure.

    :param nix_filename: Path to the NIX file to be loaded.
    :rtype: mne.io.RawArray
    """
    nix_file = nix.File(nix_filename, mode=nix.FileMode.ReadOnly)

    # root, ext = os.path.splitext(nix_filename)
    # bvfilename = root + os.extsep + "vhdr"
    # bvfile = mne.io.read_raw_brainvision(bvfilename, stim_channel=False)

    # Create MNE Info object
    info_sec = nix_file.sections["Info"]
    n_chan = info_sec["nchan"]
    s_freq = info_sec["sfreq"]
    info = mne.create_info(n_chan, s_freq)

    nix_info_dict = md_to_dict(info_sec)
    info.update(nix_info_dict)

    # Read raw data into MNE objects
    data_group = nix_file.blocks[DATA_BLOCK_NAME].groups[RAW_DATA_GROUP_NAME]
    if len(data_group.data_arrays) > 1:
        # Data split: One DataArray per channel.  Merging
        nix_raw_data = merge_data_arrays(data_group.data_arrays)
    else:
        nix_raw_data = data_group.data_arrays[0][:]

    # Create MNE RawArray
    mne_raw_data = mne.io.RawArray(nix_raw_data, info)

    # Add annotations: Stimuli from MultiTags
    mtags = data_group.multi_tags
    annotations = create_mne_annotations(mtags)

    mne_raw_data.set_annotations(annotations)

    nix_file.close()

    return mne_raw_data


def main():
    if len(sys.argv) < 2:
        print("Please provide a NIX filename as the first argument")
        sys.exit(1)

    nix_filename = sys.argv[1]
    import_nix(nix_filename)


if __name__ == "__main__":
    main()
