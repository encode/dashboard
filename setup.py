#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from setuptools import setup



def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def read(f):
    return open(f, 'r', encoding='utf-8').read()


version = get_version('dashboard')


setup(
    name='dashboard',
    version=version,
    url='https://github.com/encode/dashboard',
    license='BSD',
    description='An admin dashboard.',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='Tom Christie',
    author_email='tom@tomchristie.com',
    packages=get_packages('dashboard'),
    include_package_data=True,
    install_requires=[
        'aiofiles',
        'starlette',
        'uvicorn',  # Not strictly true, but we'll have it here for now.
        'jinja2',
        'python-multipart',
        'orm~=0.2',
        'typesystem~=0.3',
        'databases[sqlite]~=0.5',  # Not strictly true, but we'll have it here for now.
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ]
)
