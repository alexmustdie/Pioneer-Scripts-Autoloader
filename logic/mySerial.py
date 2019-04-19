import serial.tools.list_ports
import re
import time

from PyQt5.QtCore import pyqtSignal, QThread


class MySerial:

    def __init__(self):
        pass

    @staticmethod
    def getSerialPorts():
        return [p.device for p in serial.tools.list_ports.comports() if not re.match('/dev/ttyS[0-3]', p.device)]

    class Checker(QThread):

        ports = pyqtSignal(list)

        def __init__(self):
            QThread.__init__(self)

        def run(self):

            ports = MySerial.getSerialPorts()

            while True:

                newPorts = MySerial.getSerialPorts()

                if len(newPorts) != len(ports):
                    diff = list(set(newPorts) - set(ports))
                    if diff:
                        newPorts.remove(diff[0])
                        newPorts += diff
                    self.ports.emit(newPorts)

                ports = newPorts
                time.sleep(1)
