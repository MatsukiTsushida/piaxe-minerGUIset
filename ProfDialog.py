import json
import os
import random
import signal
import socket
import sys
import time
from datetime import datetime

import psycopg2
import serial.tools.list_ports
from PyQt5.QtCore import QProcess, QSize, Qt, QThread, QTimer, center
from PyQt5.QtGui import *
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDial,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from ruamel.yaml import YAML

import bridge
from usb_detect import DeviceInterfaces, find_devices


class ProfileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profiles")

        self.jsprofiles = []
        self.profiles_dir = ""
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.currentprof = ""

        self.dropdownjs = QComboBox()
        self.choose = QPushButton("Select")
        self.choose.clicked.connect(self.select_prof)
        self.input = QInputDialog()
        self.input.setLabelText("New instead? Give it a name:")

        try:
            self.profiles_dir = os.path.join(os.path.dirname(__file__), "Profiles")

            # Ensure the directory actually exists so it doesn't crash on a fresh install
            if not os.path.exists(self.profiles_dir):
                os.makedirs(self.profiles_dir)

            files = os.listdir(self.profiles_dir)

            self.jsprofiles = [
                os.path.splitext(f)[0] for f in files if f.endswith(".json")
            ]
            print(self.jsprofiles)
            if not self.jsprofiles:
                self.dropdownjs.addItem("No profiles found")
            else:
                self.dropdownjs.addItems(self.jsprofiles)
        except Exception as e:
            print(f"Error scanning folder {e}")

        layout.addWidget(self.dropdownjs)
        layout.addWidget(self.choose)
        layout.addWidget(self.input)

    def select_prof(self):
        self.currentprof = self.dropdownjs.currentText()
        with open(f"Profiles/{self.currentprof}.json", "r") as prof:
            data = json.load(prof)
            for i in data.keys():
                bridge.send_freq({"freq": float(i), "id": data[i]})
        self.accept()

    def new_prof(self):
        pass
