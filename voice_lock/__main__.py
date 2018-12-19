# Project: Voice Lock
# Author: Nikolai Gaiduchenko, BSc, MIPT student
# Verion: 1.0

"""
voice_lock - cryptograhic biometric authorisation tool
"""

import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from .main_window import MainWindow

def main():
    # Create and configure application window
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("fusion")  # Linux visual style
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":

    #############################################
    # PREVENTING QT FROM SILENCING EXCEPTIONS!
    #############################################
    sys._excepthook = sys.excepthook
    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(0)
    sys.excepthook = exception_hook
    ##############################################

    main()
