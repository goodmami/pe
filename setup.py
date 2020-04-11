#!/usr/bin/env python3

import os

from setuptools import setup

base_dir = os.path.dirname(__file__)

long_description = ''
with open(os.path.join(base_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='pe',
    version='0.1.0',
    description='Parsing Expressions',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/goodmami/pe',
    author='Michael Wayne Goodman',
    author_email='goodman.m.w@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing',
        'Topic :: Utilities'
    ],
    keywords='peg parsing text',
    packages=[
        'pe',
    ],
    python_requires='>=3.6'
)
