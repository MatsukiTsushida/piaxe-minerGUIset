import os
import signal
import sys
from datetime import datetime

import psycopg2
from PyQt5.QtCore import QProcess, QSize, Qt, QThread
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
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

from usb_detect import DeviceInterfaces, find_devices

# Database connection parameters
DB_CONFIG = {
    "host": "localhost",  # Change if your PostgreSQL is on a different host
    "database": "postgres",
    "user": "postgres",  # Change if you have a different username
    "password": "1324",
    "port": 5432,
}

flag = None


class PostgresDialog(QDialog):
    def __init__(self):
        super().__init__()
        # self.main_window = main_window
        self.setWindowTitle("Connect to Postgres?")
        self.setFixedSize(300, 150)
        self.setModal(True)
        self.flag = False
        self.show = False

        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create button layout
        button_layout = QHBoxLayout()

        # Create buttons
        yes_button = QPushButton("Yes")
        no_button = QPushButton("No")

        yes_button.clicked.connect(self.show_main_window)
        no_button.clicked.connect(self.close_application)

        # Add buttons to layout
        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)

        # Add widgets to main layout
        layout.addLayout(button_layout)

    def show_main_window(self):
        print("Hell yeah")
        self.accept()
        # self.main_window.show()

    def close_application(self):
        print("WTF")
        self.reject()
        # self.main_window.show()

    def flag(self):
        return flag


# Setting up the AppWindow and fucntionality
class MainWindow(QMainWindow):
    def __init__(self, flag=False):
        super().__init__()
        self.p = None
        self.k = None
        self.setWindowTitle("ClockEngage QAxe")
        self.setWindowIcon(QIcon("axe.jpg"))
        self.resize(QSize(800, 800))
        self.list = [
            200,
            225,
            250,
            275,
            300,
            325,
            350,
            375,
            400,
            425,
            450,
            475,
            500,
            525,
            550,
            575,
            600,
            625,
            650,
        ]
        self.flag = flag
        print(f"The flag is ${self.flag}")

        # try:
        #     self.conn = psycopg2.connect(
        #         dbname = "postgres",
        #         user = "postgres",
        #         password = "1324",
        #         host = "localhost",
        #         port = 5432
        #     )
        #     self.cur = self.conn.cursor()
        #     print("Connection successful")
        # except Error as e:
        #     print(f"Error connecting to PostgreSQL: {e}")
        #     return False
        self.hash = 3.6
        self.tempset = None
        self.hash2 = None
        self.tempset2 = None

        self.buttonBox = QMessageBox()
        self.buttonBox.setText("Do you want to add a DataBase for Grafana?")
        self.buttonBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        self.buttonBox.accepted.connect(self.pressed_ok)
        self.buttonBox.rejected.connect(self.pressed_cancel)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout2 = QVBoxLayout()
        layout2.setAlignment(Qt.AlignCenter)
        layout3 = QHBoxLayout()
        layout4 = QHBoxLayout()
        layout5 = QHBoxLayout()
        layout6 = QHBoxLayout()
        layout7 = QHBoxLayout()
        layout8 = QHBoxLayout()
        layout9 = QHBoxLayout()
        layout10 = QVBoxLayout()
        layout11 = QVBoxLayout()

        zrame = QFrame()
        zrame.resize(1, 1)
        zrame.setFrameShadow(QFrame.Plain)
        zrame.setFrameShape(QFrame.Box)
        zrame.setStyleSheet("border: 2px solid black;")

        yrame = QFrame()
        yrame.resize(1, 1)
        yrame.setFrameShadow(QFrame.Plain)
        yrame.setFrameShape(QFrame.Box)
        yrame.setStyleSheet("border: 1px solid blue;")

        xrame = QFrame()
        xrame.resize(1, 1)
        xrame.setFrameShadow(QFrame.Plain)
        xrame.setFrameShape(QFrame.Box)
        xrame.setStyleSheet("border: 1px solid green;")

        self.pid1 = 0
        self.pid2 = 0

        # Create button
        self.btn = QPushButton("Start mining worker2")
        self.btn.setFixedSize(QSize(200, 100))
        self.btn.pressed.connect(self.start_process1)

        self.btn2 = QPushButton("Stop mining worker2")
        self.btn2.setFixedSize(QSize(200, 100))
        self.btn2.pressed.connect(self.stop_process1)

        self.btn3 = QPushButton("Start mining worker3")
        self.btn3.setFixedSize(QSize(200, 100))
        self.btn3.pressed.connect(self.start_process2)

        self.btn4 = QPushButton("Stop mining worker3")
        self.btn4.setFixedSize(QSize(200, 100))
        self.btn4.pressed.connect(self.stop_process2)

        # self.bttn = QPushButton('Submit1')
        # self.bttn.pressed.connect(self.change1)
        self.bttn2 = QPushButton("Submit2")
        self.bttn2.pressed.connect(self.change2)

        self.c_speed1 = QLineEdit()
        self.c_speed1.setPlaceholderText("Clock speed worker2:")
        self.c_speed2 = QLineEdit()
        self.c_speed2.setPlaceholderText("Clock speed worker3:")

        # Create text area for output (optional)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(200)

        self.output_text2 = QTextEdit()
        self.output_text2.setReadOnly(True)
        self.output_text2.setMaximumHeight(200)
        self.output_text2.setMaximumWidth(200)

        self.temp_out1 = QLabel("0°C")
        self.temp_out1.setAlignment(Qt.AlignCenter)
        self.temp_out1.setMaximumHeight(15)
        self.temp_out1.setMaximumWidth(50)

        self.temp_out2 = QLabel("0°C")
        self.temp_out2.setAlignment(Qt.AlignCenter)
        self.temp_out2.setMaximumHeight(15)
        self.temp_out2.setMaximumWidth(50)

        self.temp_out3 = QLabel("0°C")
        self.temp_out3.setAlignment(Qt.AlignCenter)
        self.temp_out3.setMaximumHeight(15)
        self.temp_out3.setMaximumWidth(50)

        self.temp_out4 = QLabel("0°C")
        self.temp_out4.setAlignment(Qt.AlignCenter)
        self.temp_out4.setMaximumHeight(15)
        self.temp_out4.setMaximumWidth(50)

        self.temp_out5 = QLabel("0°C")
        self.temp_out5.setAlignment(Qt.AlignCenter)
        self.temp_out5.setMaximumHeight(15)
        self.temp_out5.setMaximumWidth(50)

        self.temp_out6 = QLabel("0°C")
        self.temp_out6.setAlignment(Qt.AlignCenter)
        self.temp_out6.setMaximumHeight(15)
        self.temp_out6.setMaximumWidth(50)

        self.temp_out7 = QLabel("0°C")
        self.temp_out7.setAlignment(Qt.AlignCenter)
        self.temp_out7.setMaximumHeight(15)
        self.temp_out7.setMaximumWidth(50)

        self.temp_out8 = QLabel("0°C")
        self.temp_out8.setAlignment(Qt.AlignCenter)
        self.temp_out8.setMaximumHeight(15)
        self.temp_out8.setMaximumWidth(50)

        self.temp_out9 = QLabel("0°C")
        self.temp_out9.setAlignment(Qt.AlignCenter)
        self.temp_out9.setMaximumHeight(15)
        self.temp_out9.setMaximumWidth(50)

        self.temp_out10 = QLabel("0°C")
        self.temp_out10.setAlignment(Qt.AlignCenter)
        self.temp_out10.setMaximumHeight(15)
        self.temp_out10.setMaximumWidth(50)

        self.temp_out11 = QLabel("0°C")
        self.temp_out11.setAlignment(Qt.AlignCenter)
        self.temp_out11.setMaximumHeight(15)
        self.temp_out11.setMaximumWidth(50)

        self.temp_out12 = QLabel("0°C")
        self.temp_out12.setAlignment(Qt.AlignCenter)
        self.temp_out12.setMaximumHeight(15)
        self.temp_out12.setMaximumWidth(50)

        self.temp_out13 = QLabel("0°C")
        self.temp_out13.setAlignment(Qt.AlignCenter)
        self.temp_out13.setMaximumHeight(15)
        self.temp_out13.setMaximumWidth(50)

        self.temp_out14 = QLabel("0°C")
        self.temp_out14.setAlignment(Qt.AlignCenter)
        self.temp_out14.setMaximumHeight(15)
        self.temp_out14.setMaximumWidth(50)

        self.temp_out15 = QLabel("0°C")
        self.temp_out15.setAlignment(Qt.AlignCenter)
        self.temp_out15.setMaximumHeight(15)
        self.temp_out15.setMaximumWidth(50)

        self.temp_out16 = QLabel("0°C")
        self.temp_out16.setAlignment(Qt.AlignCenter)
        self.temp_out16.setMaximumHeight(15)
        self.temp_out16.setMaximumWidth(50)

        rightTopFrame = QFrame()
        rightTopFrame.resize(1, 1)
        rightTopFrame.setStyleSheet("background-color: yellow")

        self.dial = QDial()
        # self.dial.move(175, 175)
        # self.dial.setGeometry(50, 50, 50, 50)
        self.dial.setFixedSize(300, 300)
        self.dial.setMinimum(200)
        self.dial.setMaximum(650)
        self.dial.setSingleStep(25)
        self.dial.valueChanged.connect(self.value1)
        self.dial.sliderReleased.connect(self.change1)
        self.dial.setNotchesVisible(True)
        self.dial2 = QDial()
        self.dial2.setGeometry(200, 200, 200, 200)
        self.dial2.setMinimum(200)
        self.dial2.setMaximum(650)
        self.dial2.setSingleStep(25)
        self.dial2.valueChanged.connect(self.value2)
        self.dial2.sliderReleased.connect(self.change2)
        self.dial2.setNotchesVisible(True)

        self.freq = QLabel("", self)
        self.freq.setAlignment(Qt.AlignCenter)
        self.freq.setMaximumHeight(50)
        # self.freq2 = QLabel('', self)
        # self.freq2.setAlignment(Qt.AlignCenter)
        # self.freq2.setMaximumHeight(50)

        self.freq3 = QLabel("Clock speed dial:", self)
        self.freq3.setAlignment(Qt.AlignCenter)
        self.freq3.setMaximumHeight(50)
        # self.freq4 = QLabel('ClockSpeed worker3', self)
        # self.freq4.setAlignment(Qt.AlignCenter)
        # self.freq4.setMaximumHeight(50)

        # layout.addLayout(layout3)
        # zrame.setLayout(layout4)
        # layout.addWidget(zrame)
        # layout.addLayout(layout7)
        # layout10.addLayout(layout5)
        # layout10.addLayout(layout6)
        # layout11.addLayout(layout8)
        # layout11.addLayout(layout9)
        # xrame.setLayout(layout10)
        # yrame.setLayout(layout11)
        # layout4.addWidget(xrame)
        # layout4.addWidget(yrame)
        # layout3.addLayout(layout2)
        # layout3.addWidget(self.btn)
        # layout3.addWidget(self.btn2)
        # layout2.addWidget(self.freq3)
        # layout2.addWidget(self.dial)
        # layout2.addWidget(self.freq)
        # layout5.addWidget(self.temp_out1000)
        # layout5.addWidget(self.temp_out2000)
        # layout5.addWidget(self.temp_out3000)
        # layout5.addWidget(self.temp_out4000)
        # layout6.addWidget(self.temp_out0100)
        # layout6.addWidget(self.temp_out0200)
        # layout6.addWidget(self.temp_out0300)
        # layout6.addWidget(self.temp_out0400)
        # layout8.addWidget(self.temp_out0010)
        # layout8.addWidget(self.temp_out0020)
        # layout8.addWidget(self.temp_out0030)
        # layout8.addWidget(self.temp_out0040)
        # layout9.addWidget(self.temp_out0001)
        # layout9.addWidget(self.temp_out0002)
        # layout9.addWidget(self.temp_out0003)
        # layout9.addWidget(self.temp_out0004)
        # layout7.addWidget(self.output_text)

        layout.addLayout(layout3)
        zrame.setLayout(layout4)
        layout.addWidget(zrame)
        layout.addLayout(layout7)
        layout3.addWidget(self.freq3)
        layout3.addWidget(self.dial)
        layout3.addWidget(self.freq)
        xrame.setLayout(layout10)
        yrame.setLayout(layout11)
        layout4.addWidget(xrame)
        layout4.addWidget(yrame)
        layout10.addLayout(layout5)
        layout10.addLayout(layout6)
        layout11.addLayout(layout8)
        layout11.addLayout(layout9)
        layout5.addWidget(self.temp_out1)
        layout5.addWidget(self.temp_out2)
        layout5.addWidget(self.temp_out3)
        layout5.addWidget(self.temp_out4)
        layout6.addWidget(self.temp_out8)
        layout6.addWidget(self.temp_out7)
        layout6.addWidget(self.temp_out6)
        layout6.addWidget(self.temp_out5)
        layout8.addWidget(self.temp_out9)
        layout8.addWidget(self.temp_out10)
        layout8.addWidget(self.temp_out11)
        layout8.addWidget(self.temp_out12)
        layout9.addWidget(self.temp_out16)
        layout9.addWidget(self.temp_out15)
        layout9.addWidget(self.temp_out14)
        layout9.addWidget(self.temp_out13)
        layout7.addWidget(self.btn)
        layout7.addWidget(self.btn2)

        with open("config.yml", "r") as f:
            yaml = YAML()
            data = yaml.load(f)
            print(data["qaxe"]["asic_frequency"])
            self.freq.setText(str(data["qaxe"]["asic_frequency"]) + "Mhz")
            self.dial.setValue(data["qaxe"]["asic_frequency"])
        # with open('config2.yml', 'r') as f:
        #     yaml = YAML()
        #     data = yaml.load(f)
        #     print(data["qaxe"]["asic_frequency"])
        #     self.freq2.setText(str(data["qaxe"]["asic_frequency"]) + 'Mhz')
        #     self.dial2.setValue(data["qaxe"]["asic_frequency"])

    def connect_post(self):
        if self.flag:
            try:
                self.conn = psycopg2.connect(
                    dbname="postgres",
                    user="postgres",
                    password="1324",
                    host="localhost",
                    port=5432,
                )
                self.cur = self.conn.cursor()
                print("Connection successful")
            except Error as e:
                print(f"Error connecting to PostgreSQL: {e}")
                return False

    def pressed_ok(self):
        self.flag = True
        print(self.flag)

    def pressed_cancel(self):
        self.flag = False
        print(self.flag)

    def value1(self):
        entry = self.dial.value()
        self.dial.setValue(min(self.list, key=lambda x: abs(x - entry)))
        self.freq.setText(str(self.dial.value()) + "Mhz")

    def value2(self):
        entry = self.dial2.value()
        self.dial2.setValue(min(self.list, key=lambda x: abs(x - entry)))
        self.freq2.setText(str(self.dial2.value()) + "Mhz")

    def change1(self):
        print(self.flag)
        self.output_text.append("Recalibrating frequency for worker 2 wait...")
        if self.p is None:
            # a = self.c_speed1.text()
            a = self.dial.value()
            print(a)
            with open("config.yml", "r") as file:
                yaml = YAML()
                data = yaml.load(file)
                print(data)
                data["qaxe"]["asic_frequency"] = a
                print(data)
                print(a)
            with open("config.yml", "w") as f:
                yaml.dump(data, f)
        else:
            self.stop_process1()
            self.change1()
            self.start_process1()
        self.output_text.append("Calibration complete.")

    def change2(self):
        self.output_text2.append("Recalibrating frequency for worker 3 wait...")
        if self.k is None:
            # a = self.c_speed2.text()
            a = self.dial2.value()
            print(a)
            with open("config2.yml", "r") as file:
                yaml = YAML()
                data = yaml.load(file)
                print(data)
                data["qaxe"]["asic_frequency"] = a
                print(data)
                print(a)
            with open("config2.yml", "w") as f:
                yaml.dump(data, f)
        else:
            self.stop_process2()
            self.change2()
            self.start_process2()
        self.output_text2.append("Calibration complete.")

    def start_process1(self):
        if self.p is None:
            print("Executing process 2...")
            self.output_text.append("Starting mining process 2...")

            self.p = QProcess()
            self.p.readyReadStandardOutput.connect(self.handle_stdout)
            self.p.readyReadStandardError.connect(self.handle_stderr)

            # Method 1: Use QProcess.start() with separate arguments
            program = "python3"
            arguments = [
                "pyminer.py",
                "-c",
                "config.yml",
                "-o",
                "stratum+tcp://de.kano.is:3333",
                "-u",
                "flowsolve.test16-daniel",
                "-p",
                "X",
                "-d",
            ]

            self.p.start(program, arguments)
            self.pid1 = self.p.processId()

            with open("config.yml", "r") as f:
                yaml = YAML()
                data = yaml.load(f)
                print(data["qaxe"]["asic_frequency"])
                self.freq.setText(str(data["qaxe"]["asic_frequency"]) + "Mhz")
                self.dial.setValue(data["qaxe"]["asic_frequency"])

            # Update button text
            self.btn.setText("Mining2...")
            self.btn.setEnabled(False)

            devices = find_devices()  # uses default VID=0xCAFE, PID=0x4003
            for dev in devices:
                print(dev)
                n = dev.interface_0.port
                print(n[4:])
                print(dev.interface_1.port)
                print(f"  IF2 → {dev.interface_2.port}")
        else:
            print("Process already 2 running")

    def start_process2(self):
        if self.k is None:
            print("Executing process 3...")
            self.output_text2.append("Starting mining process 3...")
            self.k = QProcess()
            self.k.readyReadStandardOutput.connect(self.handle_stdout2)
            self.k.readyReadStandardError.connect(self.handle_stderr2)

            # Method 1: Use QProcess.start() with separate arguments
            program = "python3"
            arguments = [
                "pyminer.py",
                "-o",
                "stratum+tcp://de.kano.is:3333",
                "-u",
                "flowsolve.worker3",
                "-p",
                "X",
                "-c",
                "config2.yml",
            ]

            self.k.start(program, arguments)
            self.pid2 = self.k.processId()

            with open("config2.yml", "r") as f:
                yaml = YAML()
                data = yaml.load(f)
                print(data["qaxe"]["asic_frequency"])
                self.freq2.setText(str(data["qaxe"]["asic_frequency"]) + "Mhz")
                self.dial2.setValue(data["qaxe"]["asic_frequency"])

            # Update button text
            self.btn3.setText("Mining3...")
            self.btn3.setEnabled(False)
        else:
            print("Process already 3 running")

    def handle_stdout(self):
        data = self.p.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        print(stdout)
        self.output_text.append(stdout)

    def handle_stdout2(self):
        data = self.k.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.output_text2.append(stdout)

    def handle_stderr(self):
        data = self.p.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        print(stderr)
        if "hash rate" in stderr:
            b = stderr
            z = b.split("\n")
            print("WELL THIS HAS TO BE OK RIGHT??? -->" + z[0])
        if "temperature and voltage" in stderr:
            res = []
            a = stderr[68:]
            if "INFO" not in a:
                print(a)
                for i in range(len(a)):
                    if a[i] == "h":
                        b = a[i + 13 : i + 43]
                        print(b)
                        res1 = [float(i) for i in b.split(", ")]
                        c = a[i + 60 : i + 90]
                        res2 = [float(i) for i in c.split(", ")]
                        # res = [float(i) for i in a[:i-2].split(', ')]
                        # type(res[0])
                        self.tempset = res1
                        self.tempset2 = res2
                        print(res1[0])
                        print("THE THING ABOVE IS WHAT U NEED RAHHH")
                        break
                self.temp_out1.setText(str(res1[0]) + " °C")
                self.temp_out2.setText(str(res1[1]) + " °C")
                self.temp_out3.setText(str(res1[2]) + " °C")
                self.temp_out4.setText(str(res1[3]) + " °C")
                self.temp_out5.setText(str(res1[4]) + " °C")
                self.temp_out6.setText(str(res1[5]) + " °C")
                self.temp_out7.setText(str(res1[6]) + " °C")
                self.temp_out8.setText(str(res1[7]) + " °C")
                self.temp_out9.setText(str(res2[0]) + " °C")
                self.temp_out10.setText(str(res2[1]) + " °C")
                self.temp_out11.setText(str(res2[2]) + " °C")
                self.temp_out12.setText(str(res2[3]) + " °C")
                self.temp_out13.setText(str(res2[4]) + " °C")
                self.temp_out14.setText(str(res2[5]) + " °C")
                self.temp_out15.setText(str(res2[6]) + " °C")
                self.temp_out16.setText(str(res2[7]) + " °C")
        if self.hash != None and self.tempset != None and self.flag:
            print("ITS HEREEEE")
            self.cur.execute(
                "INSERT INTO grafana (temp1, temp2, temp3, temp4, temp5, temp6, temp7, temp8, hash) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);",
                (
                    self.tempset[0],
                    self.tempset[1],
                    self.tempset[2],
                    self.tempset[3],
                    self.tempset[4],
                    self.tempset[5],
                    self.tempset[6],
                    self.tempset[7],
                    self.hash,
                ),
            )
            self.conn.commit()
            self.cur.execute("SELECT hash, temp FROM grafana")
            self.conn.commit()
            sus = self.cur.fetchall()
            # print(sus)
            # self.hash = None
            # self.tempset = None
        self.output_text.append(f"Error: {stderr}")

    def handle_stderr2(self):
        data = self.k.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        if "temperature and voltage" in stderr:
            res = []
            a = stderr[68:]
            if "INFO" not in a:
                print(a)
                for i in range(len(a)):
                    if a[i] == "N":
                        res = [float(i) for i in a[: i - 2].split(", ")]
                        self.tempset2 = res[0]
                        break
                # self.temp_out2.setText(str((res[0] + res[1]) / 2))
                self.temp_out21.setText(str(res[0]) + " °C")
                self.temp_out22.setText(str(res[1]) + " °C")
        if self.hash2 != None and self.tempset2 != None and self.flag == True:
            self.cur.execute(
                "INSERT INTO grafana2 (temp2, hash2) VALUES (%s, %s);",
                (
                    self.tempset2,
                    self.hash2,
                ),
            )
            self.conn.commit()
            self.hash = None
            self.tempset = None
        self.output_text2.append(f"Error: {stderr}")

    def stop_process1(self):
        if self.p:
            # os.kill(self.pid1, signal.SIGINT)
            self.p.terminate()
            # self.p.kill()
            self.p.waitForFinished()
            self.p = None
            self.pid1 = 0
            self.btn.setText("Start mining")
            self.btn.setEnabled(True)
            print("Process 2 finished")
            self.output_text.append("Mining process 2 finished.")

    def stop_process2(self):
        if self.k:
            # os.kill(self.pid2, signal.SIGINT)
            self.k.terminate()
            # self.k.kill()
            self.k.waitForFinished()
            self.k = None
            self.pid2 = 0
            self.btn3.setText("Start mining")
            self.btn3.setEnabled(True)
            print("Process 3 finished")
            self.output_text2.append("Mining 3 process finished.")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create and show the dialog
    dialog = PostgresDialog()
    print(dialog.flag, dialog.show)
    # Use the QProcess version first

    window = MainWindow()
    result = dialog.exec_()
    print(result)
    # Show dialog and handle the result
    if result == QDialog.Accepted:
        # User clicked "Yes" - main window is already shown
        # window = MainWindow(True)
        window.flag = True
        window.connect_post()
        window.show()
        sys.exit(app.exec_())
    elif result == QDialog.Rejected:
        window.flag = False
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit()

    # window = MainWindowSubprocess()

    # window.show()
    app.exec()
