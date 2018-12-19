# Project: Voice Lock
# Author: Nikolai Gaiduchenko, BSc, MIPT student
# Verion: 1.0

# System imports
import functools
import glob
import os
import os.path as osp
import sys

# Third party imports
import numpy as np
from tqdm import tqdm

# matplotlib imports
from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
else:
    from matplotlib.backends.backend_qt4agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

# import PyQt5
from PyQt5.QtWidgets import QFileDialog
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

# local imports
from .aes_cipher import AESCipher
from .wave_proc import *

# Load and preconfigure GUI from UI file
self_wd = osp.abspath(osp.dirname(__file__))
(Ui_MainWindow, QMainWindow) = uic.loadUiType(osp.join(self_wd, 'gui', 'mainwindow.ui'))

class MainWindow(QMainWindow):
    """MainWindow inherits QMainWindow"""

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.wd = osp.abspath(osp.dirname(__file__))
        self.refs_path = osp.join(self.wd, 'data', 'ref_samples')
        self.test_path = osp.join(self.wd, 'data', 'test_samples')

        self.ui.load_button.clicked.connect(self._load_button_clicked)
        self.ui.record_button.clicked.connect(self._record_button_clicked)

        # Initialize AES Cipher
        self.cipher = AESCipher(key=b'Sixteen byte key')
        self.cipher.load_iv(osp.join(self.refs_path, 'iv'))

        # encrypt_wavs(dir_in=osp.join(self.wd, 'data/ref_samples_raw'),
        #              dir_out=osp.join(self.wd, 'data/ref_samples'),
        #              cipher=self.cipher)

        # Load reference samples of the Master
        self.ref_samples = self.load_ref_samples(ref_dir=self.refs_path)

    def __del__(self):
        self.ui = None

    def load_ref_samples(self, ref_dir='./data/ref_samples'):
        self.log('Searching for reference samples...')

        enc_samples = glob.glob(osp.join(ref_dir, '*.wav.enc'))
        self.log(f'Found {len(enc_samples)} reference samples in the {ref_dir} directory.')

        ref_samples = [make_enc_wave(sample, self.cipher) for sample in enc_samples]
        self.log(f'Reference samples loaded successfully')

        return ref_samples

    def record_audio(self):
        pass

    def plot_waveform(self, wave):
        pass

    # === QPushButton SLOTS ===

    def _load_button_clicked(self):
        """Choose a file, then load it and process"""
        fpath_load = QFileDialog.getOpenFileName(self,
                                                 caption='Load voice sample',
                                                 directory=self.test_path,
                                                 filter='*.wav')[0]

        # If cancel button was pressed in QFileDialog, do nothing
        if fpath_load == '':
            return
        else:
            self.log(f'Loading test sample {fpath_load}')

        confidence = self.compare(fpath_load)



    def _record_button_clicked(self):
        pass

    def log(self, text, debug=True):
        self.ui.console.append(text)
        if debug:
            print(text)

    def compare(self, test_path):
        test_sample = make_wave(test_path)
        self.display_waveform(test_sample)
        self.log('Test sample waveform loaded.')

        rez = functools.reduce((lambda r, smp: r + corr_tuple(test_sample, smp)),
                               tqdm(self.ref_samples),
                               0) / len(self.ref_samples)

        self.log(f'Confidence is {rez}')

        return rez

    def display_waveform(self, wave_data):
        pass

#-----------------------------------------------------#
if __name__ == '__main__':
    # create application
    app = QApplication(sys.argv)
    app.setStyle("fusion")  # Linux visual style
    app.setApplicationName('VoiceLock')

    # create widget
    w = MainWindow()
    w.setWindowTitle('Voice Lock')
    w.show()

    app.installEventFilter(w)

    # execute application
    sys.exit(app.exec_())