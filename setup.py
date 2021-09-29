#!/usr/bin/env python3

from typing import Dict
import sys
import os

from setuptools import setup, Extension


# Conditional Cython setup

BUILD_OPTIONAL = os.environ.get('CIBUILDWHEEL', '0') != '1'

CYTHONIZE = False
if '--cythonize' in sys.argv:
    CYTHONIZE = True
    sys.argv.remove('--cythonize')
elif not BUILD_OPTIONAL:
    CYTHONIZE = True

ext = 'pyx' if CYTHONIZE else 'c'

extensions = [
    Extension('pe.scanners', [f'pe/scanners.{ext}'], optional=BUILD_OPTIONAL),
    Extension('pe.machine', [f'pe/machine.{ext}'], optional=BUILD_OPTIONAL),
]

if CYTHONIZE:
    try:
        from Cython.Build import cythonize
    except ImportError:
        sys.exit('Cython is required for building the extension modules.')
    extensions = cythonize(extensions, language_level='3')


# Dynamic project metadata

base_dir = os.path.dirname(__file__)
meta: Dict[str, str] = {}
with open(os.path.join(base_dir, "pe", "_meta.py")) as f:
    exec(f.read(), meta)


# Main setup call

setup(
    version=meta['__version__'],
    ext_modules=extensions,
    package_data={
        'pe': ['*.pyx', '*.pxd'],
    },
)
