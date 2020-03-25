#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import dataclasses
import datetime
import argparse
import nixio as nix
import pynwb as nwb

from pathlib import Path

import numpy as np
import nixio as nix
import pynwb as nwb
import quantities as pq


@dataclasses.dataclass
class Context:
    nf: nix.File
    ip: nwb.NWBFile

    # main items
    block: nix.pycore.Block
    metadata: nix.pycore.Section

    # current state
    group: nix.pycore.Group = None

    #general groups
    acq_group: nix.pycore.Group = None

    @property
    def acquisition(self) -> nix.pycore.Group:
        if self.acq_group is None:
            self.acq_group = self.block.create_group('acquisition', 'nwb.acquisition')
        return self.acq_group


def convert_time_series(ctx: Context, obj: nwb.base.TimeSeries, typename='nwb.TimeSeries') -> nix.pycore.DataArray:
    '''convert 'obj' from nix (nf) to nwb (fin)'''
    data = obj.data

    arr = np.empty(data.shape, dtype=data.dtype)
    data.read_direct(arr)

    da = ctx.block.create_data_array(obj.name, typename, shape=data.shape, data=arr)
    da.unit = obj.unit

    if obj.timestamps is not None:
        print('TODO')
    elif obj.rate > 0.0:
        stepsize = 1.0 / obj.rate
        dim = da.append_sampled_dimension(stepsize)
        dim.unit = "s"
        dim.label = "time"
        unit = obj.starting_time_unit
        if unit == 'Seconds':  # SI, eh?
            unit = 'second'
        q = pq.Quantity(obj.starting_time, unit)
        dim.offset = float(q.rescale(pq.sec))

    if ctx.group is not None:
        ctx.group.data_arrays.append(da)

    return da


def convert_voltage_clamp_series(ctx: Context, obj: nwb.icephys.VoltageClampSeries):
    '''convert obj from nwb to nix'''
    da = convert_time_series(ctx, obj, ' nwb.icephys.VoltageClampSeries')

    el = obj.electrode
    recording = ctx.metadata
    if el.name not in recording:
        md = recording.create_section(el.name, 'Electrode')
    else:
        md = recording[el.name]

    if el.description is not None:
        md['Description'] = el.description


def convert_current_clamp_series(ctx: Context, obj: nwb.icephys.CurrentClampSeries):
    '''convert obj from nwb to nix'''
    da = convert_time_series(ctx, obj, ' nwb.icephys.CurrentClampSeries')


def main():
    '''main entry point'''
    parser = argparse.ArgumentParser(description='nwb2nix')
    parser.add_argument('-v', '--version', action='store_true', default=False)
    parser.add_argument('FILE', type=str)
    args = parser.parse_args()

    if args.version:
        print(f"NIX: {nix.__version__}")
        print(f"NWB: {nwb.__version__}")
        sys.exit(0)

    p = Path(args.FILE).resolve()
    print(f"Loading {p}", file=sys.stderr)

    f = nwb.NWBHDF5IO(str(p), 'r')
    fin = f.read()

    basename = p.stem
    nf = nix.File.open(basename + '.nix', nix.FileMode.Overwrite)
    block = nf.create_block(basename, 'nwb.file')

    md = nf.create_section(basename, 'recording')
    ctx = Context(nf=nf, ip=fin, block=block, metadata=md)

    sst = fin.session_start_time.astimezone(datetime.timezone.utc)

    recording = md.create_section('Recording', 'Recording')
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
