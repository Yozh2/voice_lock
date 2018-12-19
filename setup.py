# Project: Voice Lock
# Author: Nikolai Gaiduchenko, BSc, MIPT student
# Verion: 1.0

# A script to build a .py file from .ui file made in QtCreator.
from setuptools import setup

try:
    from pyqt_distutils.build_ui import build_ui
    cmdclass = {"build_ui": build_ui}
except ImportError:
    cmdclass = {}

setup(
    name="voice_lock",
    version="1.0",
    packages=["voice_lock"],
    cmdclass=cmdclass,
)
