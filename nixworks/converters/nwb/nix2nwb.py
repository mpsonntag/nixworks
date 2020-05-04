#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script converts a data set recorded with https://github.com/relacs/relacs
and stored in the NIX data format to the NWB format.
"""

import argparse
import sys

from datetime import datetime, timedelta
from pathlib import Path

import nixio as nix
import pynwb as nwb
import quantities as pq


def make_recoding_time(recording):
    """
    Extract date and time from metadata

    :param recording: NIX metadata containing recording timestamp
    """
    date = recording['Date']
    time = recording['Time']
    fmt_t = datetime.strptime(time, "%H:%M:%S")
    fmt_d = datetime.fromisoformat(date)

    return fmt_d + timedelta(hours=fmt_t.hour, minutes=fmt_t.minute, seconds=fmt_t.second)


def convert_1d_sampled(out, data, metadata):
    """
    Convert one-dimensional sampled data

    :param out: NWB file
    :param data: NIX DataArray
    :param metadata: NIX Block metadata
    """
    unit = data.unit
    dim = data.dimensions[0]
    quant = pq.Quantity(dim.sampling_interval, dim.unit)
    rate = (1 / quant.rescale(pq.s)).rescale(pq.Hz)
    print(f"{data.name}, 1d, sampled data: {rate} Hz", file=sys.stderr)
    time_series = nwb.TimeSeries(name=data.name, data=data[:], unit=unit, rate=float(rate))
    out.add_acquisition(time_series)


def main():
    """
    Main entry point of the NIX to NWB converter. The conversion is specific to NIX files
    created with the relacs electrophysiology recording software.
    """
    parser = argparse.ArgumentParser(description='nwb2nix')
    parser.add_argument('-v', '--version', action='store_true', default=False)
    parser.add_argument('FILE', type=str)
    args = parser.parse_args()

    if args.version:
        print(f"NIX: {nix.__version__}")
        print(f"NWB: {nwb.__version__}")
        sys.exit(0)

    nix_file = Path(args.FILE).resolve()
    print(f"Loading {nix_file}", file=sys.stderr)
    nfd = nix.File.open(str(nix_file), nix.FileMode.ReadOnly)
    for block in nfd.blocks:
        meta = block.metadata
        recording = meta['Recording']
        name = recording['Name']
        timestamp = make_recoding_time(recording)
        print(timestamp)

        # Convert to NWB format
        # TODO session description
        out = nwb.NWBFile(identifier=name,
                          session_description=name,
                          session_start_time=timestamp)

        for data in block.data_arrays:
            dims = data.dimensions
            if len(dims) == 1 and dims[0].dimension_type == nix.DimensionType.Sample:
                convert_1d_sampled(out, data, meta)

        print(f'writing {name}.nwb', file=sys.stderr)
        with nwb.NWBHDF5IO(f'{name}.nwb', 'w') as nwb_file:
            nwb_file.write(out)
        print("all done", file=sys.stderr)


if __name__ == "__main__":
    main()
