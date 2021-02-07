# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in next_manufacturing/__init__.py
from next_manufacturing import __version__ as version

setup(
	name='next_manufacturing',
	version=version,
	description='nextmanufacturing',
	author='Dexciss Technology',
	author_email='demo@dexciss.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
