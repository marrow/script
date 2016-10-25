from setuptools import setup

setup(
	name = 'marrow.script-naval-example',
	version = '1.0',
	py_modules = ['naval'],
	include_package_data = False,
	install_requires = ['marrow.script'],
	entry_points = {'console_scripts': ['naval = naval:main']}
)
