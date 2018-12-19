# Project: Voice Lock
# Author: Nikolai Gaiduchenko, BSc, MIPT student
# Verion: 1.0

import os
import os.path as osp
import sys
import json
from pprint import pprint

# import PyQt5
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

# local imports
from aes_cipher import AESCipher
from wave_proc import *

self_wd = osp.abspath(osp.dirname(__file__))
(Ui_MainWindow, QMainWindow) = uic.loadUiType(osp.join(self_wd, 'gui', 'mainwindow.ui'))

class MainWindow(QMainWindow):
    """MainWindow inherits QMainWindow"""

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.load_button.clicked.connect(_load_button_clicked)
        self.ui.record_button.clicked.connect(_record_button_clicked)

        # Load reference samples of the Master
        self.ref_samples = []
        self.load_ref_samples(dir='./data/ref_samples')

    def __del__(self):
        self.ui = None

    def load_ref_samples(self, dir='./data/ref_samples'):
        pass

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