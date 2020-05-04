#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script converts an electrophysiology data set recorded by the Allen Institute
and stored in the NWB data format to the NIX data format.
"""

import argparse
import dataclasses
import datetime
import sys

from pathlib import Path

import quantities as pq
import nixio as nix
import numpy as np
import pynwb as nwb


@dataclasses.dataclass
class Context:
    nf: nix.File
    ip: nwb.NWBFile

    # main items
    block: nix.pycore.Block
    metadata: nix.pycore.Section

    # current state
    group: nix.pycore.Group = None

    # general groups
    acq_group: nix.pycore.Group = None

    @property
    def acquisition(self) -> nix.pycore.Group:
        if self.acq_group is None:
            self.acq_group = self.block.create_group('acquisition', 'nwb.acquisition')
        return self.acq_group


def convert_time_series(ctx: Context, obj: nwb.base.TimeSeries,
                        typename='nwb.TimeSeries') -> nix.pycore.DataArray:
    """
    Convert 'obj' from nix (nf) to nwb (fin)
    """
    data = obj.data

    arr = np.empty(data.shape, dtype=data.dtype)
    data.read_direct(arr)

    data_array = ctx.block.create_data_array(obj.name, typename, shape=data.shape, data=arr)
    data_array.unit = obj.unit

    if obj.timestamps is not None:
        print('TODO')
    elif obj.rate > 0.0:
        stepsize = 1.0 / obj.rate
        dim = data_array.append_sampled_dimension(stepsize)
        dim.unit = "s"
        dim.label = "time"
        unit = obj.starting_time_unit
        if unit == 'Seconds':  # SI, eh?
            unit = 'second'
        quant = pq.Quantity(obj.starting_time, unit)
        dim.offset = float(quant.rescale(pq.sec))

    if ctx.group is not None:
        ctx.group.data_arrays.append(data_array)

    return data_array


def convert_voltage_clamp_series(ctx: Context, obj: nwb.icephys.VoltageClampSeries):
    """
    Convert NWB voltage clamp series object to NIX
    """
    _ = convert_time_series(ctx, obj, ' nwb.icephys.VoltageClampSeries')

    electrode = obj.electrode
    recording = ctx.metadata
    if electrode.name not in recording:
        metadata = recording.create_section(electrode.name, 'Electrode')
    else:
        metadata = recording[electrode.name]

    if electrode.description is not None:
        metadata['Description'] = electrode.description


def convert_current_clamp_series(ctx: Context, obj: nwb.icephys.CurrentClampSeries):
    """
    Convert NWB current clamp series object to NIX
    """
    _ = convert_time_series(ctx, obj, ' nwb.icephys.CurrentClampSeries')


def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(description='nwb2nix')
    parser.add_argument('-v', '--version', action='store_true', default=False)
    parser.add_argument('FILE', type=str)
    args = parser.parse_args()

    if args.version:
        print(f"NIX: {nix.__version__}")
        print(f"NWB: {nwb.__version__}")
        sys.exit(0)

    nwb_file_path = Path(args.FILE).resolve()
    print(f"Loading {nwb_file_path}", file=sys.stderr)

    nwb_file = nwb.NWBHDF5IO(str(nwb_file_path), 'r')
    fin = nwb_file.read()

    basename = nwb_file_path.stem
    nix_file = nix.File.open(basename + '.nix', nix.FileMode.Overwrite)
    block = nix_file.create_block(basename, 'nwb.file')

    metadata = nix_file.create_section(basename, 'recording')
    ctx = Context(nf=nix_file, ip=fin, block=block, metadata=metadata)

    sst = fin.session_start_time.astimezone(datetime.timezone.utc)

    recording = metadata.create_section('Recording', 'Recording')
    recording['Date'] = sst.date().isoformat()
    recording['Time'] = sst.time().isoformat()
    recording['TimeZone'] = 'UTC'

    for name in fin.acquisition:
        obj = fin.acquisition[name]
        print(f"{name} ({type(obj)})")
        ctx.group = ctx.acquisition
        if isinstance(obj, nwb.icephys.VoltageClampSeries):
            convert_voltage_clamp_series(ctx, obj)
        elif isinstance(obj, nwb.icephys.CurrentClampSeries):
            convert_current_clamp_series(ctx, obj)
        elif isinstance(obj, nwb.base.TimeSeries):
            convert_time_series(ctx, obj)


if __name__ == "__main__":
    main()
