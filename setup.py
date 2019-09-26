import os
import json
from setuptools import setup

with open('README.md') as f:
    description_text = f.read()

with open('LICENSE') as f:
    license_text = f.read()

classifiers = [
    'Development Status :: 4 - Beta',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Topic :: Scientific/Engineering'
]

# load info from nixworks/info.json
with open(os.path.join("nixworks", "info.json")) as infofile:
    infodict = json.load(infofile)

VERSION = infodict["VERSION"]
AUTHOR = infodict["AUTHOR"]
CONTACT = infodict["CONTACT"]
BRIEF = infodict["BRIEF"]
HOMEPAGE = infodict["HOMEPAGE"]

setup(
    name='nixworks',
    version=VERSION,
    author=AUTHOR,
    author_email=CONTACT,
    url=HOMEPAGE,
    description=BRIEF,
    long_description=description_text,
    long_description_content_type='text/markdown',
    classifiers=classifiers,
    license='BSD',
    packages=['nixworks.plotter', 'nixworks.table'],
    scripts=[],
    tests_require=['pytest'],
    test_suite='pytest',
    setup_requires=['pytest-runner'],
    install_requires=['nixio'],
    package_data={'nixworks': [license_text, description_text]},
    include_package_data=True,
    zip_safe=False,
)
