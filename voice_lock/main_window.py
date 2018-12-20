# Project: Voice Lock
# Author: Nikolai Gaiduchenko, BSc, MIPT student
# Verion: 1.0

# System imports
import functools
import glob
import os
import os.path as osp
import sys
import time

# Third party imports
import numpy as np
from tqdm import tqdm, trange
import sounddevice as sd

# matplotlib imports
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

# import PyQt5
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QProgressBar, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5 import uic

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

        # Setup paths
        self.wd = osp.abspath(osp.dirname(__file__))
        self.refs_path = osp.join(self.wd, 'data', 'ref_samples')
        self.test_path = osp.join(self.wd, 'data', 'test_samples')
        self.recs_path = osp.join(self.wd, 'data', 'rec_samples')

        # Connect signals to SLOTs
        self.ui.load_button.clicked.connect(self._load_button_clicked)
        self.ui.record_button.clicked.connect(self._record_button_clicked)
        self.ui.login_button.clicked.connect(self.onStart)

        # Initialize AES Cipher
        self.cipher = AESCipher(key=b'Sixteen byte key')
        self.cipher.load_iv(osp.join(self.refs_path, 'iv'))

        # Setup matplotlib plotting widget
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Add plotting widget and toolbar to waveform_view
        self.ui.main_panel_layout.insertWidget(0, self.toolbar)
        self.ui.main_panel_layout.insertWidget(0, self.canvas)

        # Encrypt reference WAV samples
        # encrypt_wavs(dir_in=osp.join(self.wd, 'data/ref_samples_raw'),
        #              dir_out=osp.join(self.wd, 'data/ref_samples'),
        #              cipher=self.cipher)

        # Load reference samples of the Master
        self.ref_samples = self.load_ref_samples(ref_dir=self.refs_path)
        self.test_sample = None

        # Setup progress bar
        self.ui.progress_bar.setRange(0, len(self.ref_samples))

        # Setup QThread'ing procedure for comparison
        self.compare_task = TaskThread()
        self.compare_task.update_comparison.connect(self.onProgress)
        self.compare_task.comparison_completed.connect(self.onFinish)

        # Set classification cut-off threshold
        self.threshold = 0.6

    def __del__(self):
        self.ui = None

    def log(self, text, debug=True):
        self.ui.console.append(text)
        if debug:
            print(text)

    def load_ref_samples(self, ref_dir='./data/ref_samples'):
        self.log('Searching for reference samples...')

        enc_samples = glob.glob(osp.join(ref_dir, '*.wav.enc'))
        self.log(f'Found {len(enc_samples)} reference samples in {osp.basename(ref_dir)} directory.')

        ref_samples = [make_enc_wave(sample, self.cipher) for sample in enc_samples]
        self.log(f'Reference samples loaded successfully')

        return ref_samples

    def load_test_sample(self, test_path):
        self.test_sample = make_wave(test_path)
        self.display_waveform(self.test_sample)
        self.log('Test sample waveform loaded.')

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
            self.log(f'Loading test sample {osp.basename(fpath_load)}')
            self.load_test_sample(fpath_load)

    def _record_button_clicked(self):
        fs=44100
        duration=4
        self.log('Recording Audio: 4s')
        rec_wave = sd.rec(duration * fs, samplerate=fs, channels=1, dtype='float64')
        sd.wait()
        self.log('Recording finished')
        self.log('Replay for testing...')
        sd.play(rec_wave, fs)
        sd.wait()

        # Save waveform
        recordings = len(glob.glob(osp.join(self.recs_path, 'recording*.wav')))
        path = osp.join(self.recs_path, 'recording_%d.wav' % recordings)
        with open(path, 'wb') as rec_file:
            siw.write(rec_file, 44100, rec_wave)

        self.log(f'Waveform is saved as {path}')
        self.load_test_sample(path)

    # === Waveform processing and visualisation SLOTS ===

    def compare(self):
        conf = functools.reduce((lambda r, smp: r + corr_tuple(self.test_sample, smp)),
                               tqdm(self.ref_samples),
                               0) / len(self.ref_samples)

        self.log(f'Confidence is {conf}')

        if conf > self.threshold:
            self.log('Greetings, Master')
            self.show_secret()

        else:
            self.log("You are not Master to me.")
            self.log('The secret remains hidden.')

        return conf

    def display_waveform(self, wave_data):

        ax = self.figure.add_subplot(111)

        # discards the old graph
        ax.clear()

        # plot data
        if len(wave_data) == 2:
            ax.plot(np.arange(len(wave_data[0])), wave_data[0])
            ax.plot(np.arange(len(wave_data[1])), wave_data[1])
        else:
            ax.plot(np.arange(len(wave_data)), wave_data)

        # refresh canvas
        self.canvas.draw()

    def show_secret(self):
        self.log('Obama is gone')

    ### ~~~ QThread'ing merhods for comparison

    def onStart(self):
        '''Start of comparison'''
        self.ui.progress_bar.setValue(0)
        self.compare_task.set_args(self.ref_samples, self.test_sample)
        self.compare_task.start()

    def onProgress(self, i):
        '''Update progress bar for comparison'''
        self.ui.progress_bar.setValue(i)

    def onFinish(self, conf):
        self.log(f'Confidence is {conf}')

        if conf > self.threshold:
            self.log('Greetings, Master')
            self.show_secret()

        else:
            self.log("You are not Master to me.")
            self.log('The secret remains hidden.')

class TaskThread(QThread):
    update_comparison = pyqtSignal(int)
    comparison_completed = pyqtSignal(np.float64)

    def set_args(self, ref_samples, test_sample):
        self.ref_samples = ref_samples
        self.test_sample = test_sample

    def run(self):
        conf = 0
        for i in trange(len(self.ref_samples)):
            conf += corr_tuple(self.test_sample, self.ref_samples[i])
            self.update_comparison.emit(i+1)

        conf /= len(self.ref_samples)
        self.comparison_completed.emit(conf)


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