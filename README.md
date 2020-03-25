# nixworks

This library is a Python package containing format converters and convenience scripts and tools for working with the [NIX (Neuroscience information exchange)](https://g-node.github.io/nix) format.

## Library content

### Convenience scripts

This library contains convenience scripts for
- plotting data stored in the NIX format
- importing data from a [Python pandas](https://pandas.pydata.org) DataFrame into a NIX DataFrame

### Converter tools
The library contains converter tools to converter data between NIX and other neuroscience specific data formats. Currently the following converters are available:
- MEG and EEG analysis and visualisation: the [MNE analysis format](https://github.com/mne-tools/mne-python)
- Neurodata without borders: the [NWB data format](https://www.nwb.org/)

## The NIX (Neuroscience information exchange) format

The NIX data model allows to store fully annotated scientific datasets, i.e. the 
data together with its metadata within the same container. Our aim is to achieve 
standardization by providing a common/generic data structure for a multitude of 
data types.

The source code of the core python library is freely available on 
[GitHub](https://github.com/G-Node/nixpy) and can be installed via the 
Python package manager `pip` by typing `pip install nixio`.

More information about the project including related projects as well as tutorials and
examples can be found at our odML [project page](https://g-node.github.io/nix/).
