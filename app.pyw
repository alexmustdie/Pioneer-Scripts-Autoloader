#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pytz

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from datetime import datetime

from logic.loader import Loader
from logic.mySerial import MySerial

current_path = os.getcwd().replace('\\', '/')


class MainWindow(QWidget):

    title = 'Pioneer Autoloader'

    defaultScriptsDirectoryPath = current_path + '/scripts'
    defaultFileWithParamsPath = current_path + '/params.properties'

    posixGroupBoxStyleSheet = 'QGroupBox{padding-top:20px;margin-top:-20px};'

    started = False

    def getScriptsDirectorySetLayout(self):

        self.currentScriptsDirectoryLabel = QLineEdit()
        self.currentScriptsDirectoryLabel.setReadOnly(True)

        self.selectScriptsDirectoryButton = QPushButton('Обзор...')
        self.selectScriptsDirectoryButton.clicked.connect(self.openScriptsDirectoryDialog)

        scriptsDirectorySetLayout = QHBoxLayout()
        scriptsDirectorySetLayout.addWidget(self.currentScriptsDirectoryLabel)
        scriptsDirectorySetLayout.addWidget(self.selectScriptsDirectoryButton)

        return scriptsDirectorySetLayout

    def getScriptsPrefixLayout(self):

        self.scriptsPrefix = QLineEdit('P')
        self.scriptsPrefix.setFixedWidth(50)

        scriptsPrefixLayout = QHBoxLayout()
        scriptsPrefixLayout.addWidget(QLabel('Префикс скриптов'))
        scriptsPrefixLayout.addWidget(self.scriptsPrefix)
        scriptsPrefixLayout.addStretch()

        return scriptsPrefixLayout

    def getScriptsLoadOptionsLayout(self):

        scriptsDirectorySetGroupBox = QGroupBox('Директория со скриптами')
        scriptsDirectorySetGroupBox.setLayout(self.getScriptsDirectorySetLayout())

        scriptsPrefixGroupBox = QGroupBox()
        scriptsPrefixGroupBox.setLayout(self.getScriptsPrefixLayout())

        if os.name == 'posix':
            scriptsPrefixGroupBox.setStyleSheet(self.posixGroupBoxStyleSheet)

        scriptsLoadOptionsLayout = QVBoxLayout()
        scriptsLoadOptionsLayout.setSpacing(10)

        scriptsLoadOptionsLayout.addWidget(scriptsDirectorySetGroupBox)
        scriptsLoadOptionsLayout.addWidget(scriptsPrefixGroupBox)

        return scriptsLoadOptionsLayout

    def getBoardNumberSetLayout(self):

        self.boardNumber = QLineEdit('0')
        self.boardNumber.setFixedWidth(50)
        self.boardNumber.setValidator(QRegExpValidator(QRegExp('0|[1-9][0-9]*')))

        boardNumberSetLayout = QHBoxLayout()
        boardNumberSetLayout.addWidget(QLabel('Текущий номер'))
        boardNumberSetLayout.addWidget(self.boardNumber)
        boardNumberSetLayout.addStretch()

        return boardNumberSetLayout

    def getFileWithParamsLayout(self):

        self.currentFileWithParamsLabel = QLineEdit()
        self.currentFileWithParamsLabel.setReadOnly(True)

        self.selectFileWithParamsButton = QPushButton('Обзор...')
        self.selectFileWithParamsButton.clicked.connect(self.openFileWithParamsDialog)

        fileWithParamsLayout = QHBoxLayout()
        fileWithParamsLayout.addWidget(self.currentFileWithParamsLabel)
        fileWithParamsLayout.addWidget(self.selectFileWithParamsButton)

        return fileWithParamsLayout

    def getParamsLoadOptionsLayout(self):

        self.boardNumberSetGroupBox = QGroupBox('Установка номеров')
        self.boardNumberSetGroupBox.setCheckable(True)
        self.boardNumberSetGroupBox.toggled.connect(self.boardNumberSetGroupBoxToggled)
        self.boardNumberSetGroupBox.setLayout(self.getBoardNumberSetLayout())

        self.fileWithParamsGroupBox = QGroupBox('Запись параметров из файла')
        self.fileWithParamsGroupBox.setCheckable(True)
        self.fileWithParamsGroupBox.toggled.connect(self.fileWithParamsGroupBoxToggled)
        self.fileWithParamsGroupBox.setLayout(self.getFileWithParamsLayout())

        paramsLoadOptionsLayout = QGridLayout()
        paramsLoadOptionsLayout.setSpacing(10)
        paramsLoadOptionsLayout.addWidget(self.boardNumberSetGroupBox)
        paramsLoadOptionsLayout.addWidget(self.fileWithParamsGroupBox)

        return paramsLoadOptionsLayout

    def getBottomLayout(self):

        self.serial = QComboBox()
        self.serial.setFixedWidth(120)
        serialPorts = MySerial.getSerialPorts()
        self.serial.addItems(serialPorts)

        self.startButton = QPushButton('Запуск загрузки')
        self.startButton.clicked.connect(self.start)
        self.startButton.setFixedWidth(150)
        self.startButton.setEnabled(len(serialPorts))

        bottomLayout = QHBoxLayout()
        bottomLayout.addWidget(QLabel('Устройство COM-порта'))
        bottomLayout.addWidget(self.serial)
        bottomLayout.addStretch()
        bottomLayout.addWidget(self.startButton)

        return bottomLayout

    def __init__(self):

        super().__init__()

        self.scriptsLoadGroupBox = QGroupBox('Загрузка скриптов')
        self.scriptsLoadGroupBox.setCheckable(True)
        self.scriptsLoadGroupBox.toggled.connect(self.scriptsLoadGroupBoxToggled)
        self.scriptsLoadGroupBox.setLayout(self.getScriptsLoadOptionsLayout())

        self.paramsLoadGroupBox = QGroupBox('Загрузка параметров')
        self.paramsLoadGroupBox.setCheckable(True)
        self.paramsLoadGroupBox.toggled.connect(self.paramsLoadGroupBoxToggled)
        self.paramsLoadGroupBox.setLayout(self.getParamsLoadOptionsLayout())

        bottomGroupBox = QGroupBox()
        bottomGroupBox.setLayout(self.getBottomLayout())

        if os.name == 'posix':
            bottomGroupBox.setStyleSheet(self.posixGroupBoxStyleSheet)

        self.statusField = QTextBrowser()
        self.statusField.setFixedSize(680, 120)
        self.statusField.setStyleSheet('padding:5;color:white;background-color:#29272A;')
        self.statusField.verticalScrollBar().setVisible(False)

        mainLayout = QGridLayout()
        mainLayout.setSpacing(10)

        mainLayout.addWidget(self.scriptsLoadGroupBox, 0, 0)
        mainLayout.addWidget(self.paramsLoadGroupBox, 0, 1)
        mainLayout.addWidget(bottomGroupBox, 1, 0, 1, 0)
        mainLayout.addWidget(self.statusField, 2, 0, 1, 0)

        try:
            self.setCompiler()
            self.setDefaultScriptsDirectory()
            self.setDefaultFileWithParamsPath()
        except Exception as e:
            print('Ошибка запуска: ' + str(e))
            sys.exit()

        self.appendToStatusField('В ожидании начала работы')
        self.setLayout(mainLayout)
        self.setFixedSize(700, 400)
        self.setWindowTitle(self.title)

        self.initLoader()
        self.runSerialPortsChecker()

    def setCompiler(self):

        if os.name == 'posix':
            self.compiler = './compilers/luac'
        elif os.name == 'nt':
            self.compiler = 'compilers/luac.exe'
        else:
            raise Exception('Ваша операционная система не поддерживается')

        if not os.path.isfile(self.compiler):
            raise Exception('Компилятор Lua не найден')

    def scriptsLoadGroupBoxToggled(self, state):

        if not state:
            self.loader.scriptsDirectoryPath = None
            self.loader.scriptsPrefix = None

        if not self.started:
            self.startButton.setEnabled(state or self.paramsLoadGroupBox.isChecked())

    def setDefaultScriptsDirectory(self):

        if not os.path.isdir(self.defaultScriptsDirectoryPath):
            raise Exception('Папка %s не найдена' % self.defaultScriptsDirectoryPath)

        self.scriptsDirectoryPath = self.defaultScriptsDirectoryPath
        self.currentScriptsDirectoryLabel.setText(self.scriptsDirectoryPath)

    def openScriptsDirectoryDialog(self):

        scriptsDirectory = QFileDialog.getExistingDirectory(self, 'Выброр директории со скриптами')

        if scriptsDirectory:
            self.scriptsDirectoryPath = scriptsDirectory
            self.currentScriptsDirectoryLabel.setText(self.scriptsDirectoryPath)
            self.appendToStatusField('Выбрана папка со скриптами: %s' % self.scriptsDirectoryPath)

    def paramsLoadGroupBoxToggled(self, state):

        if not state:
            self.loader.boardNumber = None
            self.loader.fileWithParamsPath = None

        if not self.started:
            self.startButton.setEnabled(state or self.scriptsLoadGroupBox.isChecked())

    def boardNumberSetGroupBoxToggled(self, state):

        if not state:
            self.loader.boardNumber = None

        self.paramsLoadGroupBox.setChecked(state or self.fileWithParamsGroupBox.isChecked())

    def fileWithParamsGroupBoxToggled(self, state):

        if not state:
            self.loader.fileWithParamsPath = None

        self.paramsLoadGroupBox.setChecked(state or self.boardNumberSetGroupBox.isChecked())

    def setDefaultFileWithParamsPath(self):

        if not os.path.isfile(self.defaultFileWithParamsPath):
            raise Exception('Файл %s не найден' % self.defaultFileWithParamsPath)

        self.fileWithParamsPath = self.defaultFileWithParamsPath
        self.currentFileWithParamsLabel.setText(self.fileWithParamsPath)

    def openFileWithParamsDialog(self):

        fileWithParamsPath = QFileDialog.getOpenFileName(self, 'Выбор файла с параметрами', current_path, '*.properties')

        if fileWithParamsPath:
            self.fileWithParamsPath = fileWithParamsPath[0]
            self.currentFileWithParamsLabel.setText(self.fileWithParamsPath)
            self.appendToStatusField('Выбран файл с параметрами: %s' % self.fileWithParamsPath)

    def runSerialPortsChecker(self):
        self.serialPortsChecker = MySerial.Checker()
        self.serialPortsChecker.ports.connect(self.updateSerialPortsComboBox)
        self.serialPortsChecker.start()

    def updateSerialPortsComboBox(self, serialPorts):

        oldSerialPortsCount = self.serial.count()

        self.serial.clear()
        self.serial.addItems(serialPorts)

        if len(serialPorts) == 0:
            self.startButton.setEnabled(False)
        elif len(serialPorts) > oldSerialPortsCount:
            self.startButton.setEnabled(True)
            self.suggestSerialPort(serialPorts[-1])

    def suggestSerialPort(self, detectedSerialPort):

        question = QMessageBox.question(self,
                                        '',
                                        'Обнаружен новый COM-порт: %s\nРаботать с ним?' % detectedSerialPort,
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)

        if question == QMessageBox.Yes:
            self.serial.setCurrentIndex(self.serial.count() - 1)
            self.appendToStatusField('Выбран COM-порт: %s' % detectedSerialPort)
            self.start()

    def appendToStatusField(self, status):
        dt = datetime.now().replace(tzinfo=pytz.utc)
        self.statusField.append('[%s] %s' % (dt.strftime('%H:%M:%S'), status))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and self.startButton.isEnabled():
            self.start()

    def initLoader(self):
        self.loader = Loader(self.compiler)
        self.loader.status.connect(self.appendToStatusField)
        self.loader.fail.connect(self.onFail)
        self.loader.success.connect(self.onSuccess)

    def onFail(self, e):
        QMessageBox.critical(self, 'Ошибка', str(e))
        self.appendToStatusField('Возникла ошибка: "%s"' % str(e))
        self.finish()

    def onSuccess(self):
        if self.paramsLoadGroupBox.isChecked() and self.boardNumberSetGroupBox.isChecked():
            self.boardNumber.setText(str(int(self.boardNumber.text()) + 1))
        self.finish()

    def start(self):

        self.started = True
        self.startButton.setEnabled(False)

        try:
            if self.scriptsLoadGroupBox.isChecked():
                self.loader.setScriptsDirectoryPath(self.scriptsDirectoryPath)
                self.loader.setScriptsPrefix(self.scriptsPrefix.text())

            if self.paramsLoadGroupBox.isChecked():

                if self.boardNumberSetGroupBox.isChecked():
                    self.loader.setBoardNumber(self.boardNumber.text())

                if self.fileWithParamsGroupBox.isChecked():
                    self.loader.setFileWithParamsPath(self.fileWithParamsPath)

            self.loader.setSerial(self.serial.currentText())
            self.loader.start()

        except Exception as e:
            self.onFail(e)

    def finish(self):
        self.started = False
        self.startButton.setEnabled(True)
        self.loader.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
