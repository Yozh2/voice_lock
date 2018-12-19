# Project: Voice Lock
# Author: Nikolai Gaiduchenko, BSc, MIPT student
# Verion: 1.0

import glob
import os
import os.path as osp
import sys

# import PyQt5
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

# local imports
from .aes_cipher import AESCipher
from .wave_proc import *

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
        self.ui.console.append('Searching for reference samples...')

        enc_samples = glob.glob(osp.join(ref_dir, '*.wav.enc'))
        self.ui.console.append(f'Found {len(enc_samples)} reference samples in the {ref_dir} directory.')

        ref_samples = [make_enc_wave(sample, self.cipher) for sample in enc_samples]
        self.ui.console.append(f'Reference samples loaded successfully')

        return ref_samples



    def record_audio(self):
        pass

    def plot_waveform(self, wave):
        pass

    # === QPushButton SLOTS ===

    def _load_button_clicked(self):
        pass

    def _record_button_clicked(self):
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