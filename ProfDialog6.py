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
from PyQt6.QtCore import QProcess, QSize, Qt, QThread, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
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
        butLayout = QHBoxLayout()
        self.setLayout(layout)
        self.currentprof = ""

        self.dropdownjs = QComboBox()
        self.choose = QPushButton("Select")
        self.choose.clicked.connect(self.select_prof)
        self.input = QInputDialog()
        self.input.setLabelText("New instead? Give it a name:")
        self.input.accepted.connect(self.new_prof)
        self.delete = QPushButton("Delete")
        self.delete.clicked.connect(self.delete_prof)

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("127.0.0.1", 5560))
        self.server.listen(1)
        self.server.setblocking(False)

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
        butLayout.addWidget(self.choose)
        butLayout.addWidget(self.delete)
        layout.addWidget(self.dropdownjs)
        layout.addLayout(butLayout)
        layout.addWidget(self.input)

    def select_prof(self):
        self.currentprof = self.dropdownjs.currentText()
        with open(f"Profiles/{self.currentprof}.json", "r") as prof:
            data = json.load(prof)
            for i in data.keys():
                bridge.send_freq({"freq": float(i), "id": data[i]})
        self.accept()

    def new_prof(self):
        text = self.input.textValue()
        new = {}
        try:
            conn, addr = self.server.accept()
            with conn:
                data = conn.recv(1024)
                if data and text:
                    clean_dict = json.loads(data.decode("utf-8"))
                    with open(f"Profiles/{text}.json", "w") as prof:
                        for i in range(len(clean_dict["asics"])):
                            if clean_dict["asics"][i] not in new.keys():
                                new[clean_dict["asics"][i]] = [i]
                            else:
                                new[clean_dict["asics"][i]].append(i)
                        json_str = json.dumps(new, indent=4)
                        prof.write(json_str)
            self.accept()
        except BlockingIOError:
            self.accept()  # No new mail yet

    def delete_prof(self):
        self.currentprof = self.dropdownjs.currentText()
        os.remove(f"Profiles/{self.currentprof}.json")
        self.accept()
