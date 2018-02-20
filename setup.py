import sys
sys.path.pop(0)
from setuptools import setup
sys.path.append("..")

import sdist_upip

from ucayenne import __version__

setup(name='micropython-ucayenne',
      version=__version__,
      description='A very light clone of Cayenne-MQTT-Python for MicroPython',
      long_description=open('README.rst').read(),
      url='https://github.com/xavierlesa/ucayenne',
      author='Xavier Lesa',
      author_email='xavierlesa@gmail.com',
      license="GPLv3+",
      cmdclass={'sdist': sdist_upip.sdist},      
      py_modules=["ucayenne"],
      install_requires=[
          "micropython-umqtt.simple",
          "micropython-umqtt.robust",
          ],
      )
