#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from datetime import datetime, timedelta

from pathlib import Path

import nixio as nix
import quantities as pq

start = datetime.now()
import pynwb as nwb
print(f"nwb loading done in: {datetime.now() - start}")

def make_recoding_time(recording):
    '''extract date+time from metadata'''
    date = recording['Date']
    time = recording['Time']
    t = datetime.strptime(time,"%H:%M:%S")
    d = datetime.fromisoformat(date)
    return d + timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)


def convert_1d_sampled(out, data, metadata):
    '''convert one-dimensional sampled data'''
    spikes = data[:]
    unit = data.unit
    dim = data.dimensions[0]
    q = pq.Quantity(dim.sampling_interval, dim.unit)
    rate = (1 / q.rescale(pq.s)).rescale(pq.Hz)
    print(f"{data.name}, 1d, sampled data: {rate} Hz", file=sys.stderr)
    ts = nwb.TimeSeries(name=data.name, data=data[:], unit=unit, rate=float(rate))
    out.add_acquisition(ts)


def main():
    '''Main entry point'''
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
    nfd = nix.File.open(str(p), nix.FileMode.ReadOnly)
    for b in nfd.blocks:
        md = b.metadata
        recording = md['Recording']
        name = recording['Name']
        dt = make_recoding_time(recording)
        print(dt)
        # now to nwb

        out = nwb.NWBFile(identifier=name,
                          session_description=name,  #TODO
                          session_start_time=dt)

        for data in b.data_arrays:
            dims = data.dimensions
            if len(dims) == 1 and dims[0].dimension_type == nix.DimensionType.Sample:
                convert_1d_sampled(out, data, md)

        print(f'writing {name}.nwb', file=sys.stderr)
        with nwb.NWBHDF5IO(f'{name}.nwb', 'w') as w:
            w.write(out)
        print("all done", file=sys.stderr)



if __name__ == "__main__":
    main()
