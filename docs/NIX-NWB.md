# NIX-NWB conversion tool

The current conversion tool features two scripts that can be found in
`nixworks/converters/nwb` and can be run from the command line.

## nwb → nix
`nixworks/converters/nwb/nwb2nix.py`.

The "easier" path, because NIX is a more generic data format than
NWB. The script was built using a [data set][allen] from the Allen
institute: [H19.28.012.11.05-2.nwb][allen-data].

## nix → nwb
`nixworks/converters/nwb/nix2nwb.py`.

Since NIX is very the more abstract data format, a generic conversion
from NIX o NWB is not feasible. But for specific data that are stored
in a stereotypical way a it will be possible. `nix2nwb.py` was build
around a data set recorded with [relacs][relacs]. Since for the recording
at hand there was no corresponding high level type in NWB, for now the
generic `TimeSeries` data container was used.

[allan]: http://download.alleninstitute.org/informatics-archive/prerelease/H19.28.012.11.05-2.nwb
[allan-data]: http://download.alleninstitute.org/informatics-archive/prerelease/
[relacs]: https://github.com/relacs/relacs
[nix]: www.g-node.org/nix
[nwb]: https://www.nwb.org/
[nixworks]: https://github.com/G-Node/nixworks
