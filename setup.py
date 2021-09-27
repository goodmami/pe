#!/usr/bin/env python3

from typing import Dict
import sys
import os

from setuptools import setup, Extension

# Conditional Cython setup

try:
    from Cython.Build import cythonize
    extensions = cythonize('pe/*.pyx', language_level='3')
except ImportError:
    extensions = []  # don't build C files for source install


# Dynamic project metadata

base_dir = os.path.dirname(__file__)
meta: Dict[str, str] = {}
with open(os.path.join(base_dir, "pe", "_meta.py")) as f:
    exec(f.read(), meta)

setup(
    version=meta['__version__'],
    ext_modules=extensions,
    package_data={
        'pe': ['*.pyx', '*.pxd'],
    }
)
