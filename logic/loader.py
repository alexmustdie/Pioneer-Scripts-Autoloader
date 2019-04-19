from PyQt5.QtCore import pyqtSignal, QThread

import os
import re
import subprocess

from logic import proto


class Loader(QThread):

    status = pyqtSignal(str)
    fail = pyqtSignal(Exception)
    success = pyqtSignal()

    scriptsDirectoryPath = None
    scriptsPrefix = None
    boardNumber = None
    fileWithParamsPath = None
    serial = None

    messenger = None
    stream = None

    paramsIgnore = ['Board_number', 'Offsets_', 'MagOffsets_', 'State_']

    def __init__(self, compiler):
        QThread.__init__(self)
        self.compiler = compiler

    def setScriptsDirectoryPath(self, scriptsDirectory):

        if not scriptsDirectory:
            raise Exception('Не выбрана директория со скриптами')

        self.scriptsDirectoryPath = scriptsDirectory

    def setScriptsPrefix(self, scriptsPrefix):

        if not scriptsPrefix:
            raise Exception('Не установлен префикс скриптов')

        self.scriptsPrefix = scriptsPrefix

    def setSerial(self, serial):

        if not serial:
            raise Exception('Не выбрано устройство COM-порта')

        if serial != self.serial:
            self.isNewSerial = True
            self.serial = serial
        else:
            self.isNewSerial = False

        self.stream = proto.SerialStream(self.serial, '57600')
        self.messenger = proto.Messenger(self.stream, 'cache')

    def setBoardNumber(self, boardNumber):

        if not boardNumber:
            raise Exception('Не установлен номер коптера')

        self.boardNumber = int(boardNumber)

    def setFileWithParamsPath(self, fileWithParams):

        if not fileWithParams:
            raise Exception('Не выбран файл с параметрами')

        self.fileWithParamsPath = fileWithParams

    def getBoardNumber(self):

        boardNumber = None

        for i in range(0, self.messenger.hub.getParamCount()):
            param = self.messenger.hub.getParam(i)
            if param[0] == 'Board_number':
                boardNumber = param[1]
                break

        if boardNumber is None:
            raise Exception('Не удалось получить номер коптера')

        return int(boardNumber)

    def loadScripts(self):

        if self.boardNumber is None:
            self.status.emit('Получаем номер коптера')
            self.boardNumber = self.getBoardNumber()

        self.status.emit('Номер коптера: %d' % self.boardNumber)

        script = '%s/%s_%d.lua' % (self.scriptsDirectoryPath, self.scriptsPrefix, self.boardNumber)

        if os.path.isfile(script):

            lua = self.messenger.hub['LuaScript']

            if lua is not None:

                file = lua.files[0]

                if file is not None:

                    self.status.emit('Компилируем скрипт %s' % script)
                    compiledScript = 'P_%d.out' % self.boardNumber

                    if os.name == 'posix':
                        subprocess.run([self.compiler, '-o', compiledScript, script])
                    elif os.name == 'nt':
                        subprocess.call('{} -o {} "{}"'.format(self.compiler, compiledScript, script),
                                        creationflags=0x08000000)

                    self.status.emit('Компиляция завершилась успешно')
                    self.status.emit('Скомпилированный скрипт: %s' % compiledScript)

                    if os.path.isfile(compiledScript):

                        self.status.emit('Загружаем %s в "File 0"' % compiledScript)

                        try:
                            data = open(compiledScript, 'rb').read()
                            file.writeImpl(data)
                        except:
                            raise Exception('Загрузка в "File 0" не удалась')

                        self.status.emit('Загрузка %s в "File 0" завершилась успешно' % compiledScript)
                        os.remove(compiledScript)

                    else:
                        raise Exception('Ошибка компиляции')
                else:
                    raise Exception('"File 0" не найден')
            else:
                raise Exception('Устройство Lua не найдено')
        else:
            raise Exception('Скрипт %s не найден' % script)

    def loadParams(self):

        if self.boardNumber is not None:
            try:
                self.messenger.hub.setParam(self.boardNumber, 'Board_number')
                self.status.emit('Номер %d успешно установлен' % self.boardNumber)
            except:
                raise Exception('Номер не установлен')

        if self.fileWithParamsPath:
            try:
                fileWithParams = open(self.fileWithParamsPath, 'r')
                self.status.emit('Загружаем параметры из выбранного файла')
                for x in [line.strip().split('=') for line in fileWithParams.readlines()][1:]:
                    if not re.match('(.+)?|'.join(self.paramsIgnore), x[0]):
                        self.setParam(name=x[0], value=float(x[1]))
                self.status.emit('Загрузка параметров завершилась успешно')
            except:
                raise Exception('Загрузка параметров не удалась')

    def setParam(self, name, value):
        try:
            self.messenger.hub.setParam(value, name)
        except Exception as e:
            self.status.emit('В коптере отсутствует параметр %s' % str(e))

    def run(self):
        try:
            self.messenger.connect()
            if self.fileWithParamsPath or self.boardNumber is not None:
                self.loadParams()
            if self.scriptsDirectoryPath:
                self.loadScripts()
            self.success.emit()
        except Exception as e:
            self.fail.emit(e)
        finally:
            self.stop()

    def stop(self):
        if self.stream and os.name == 'nt':
            try:
                self.stream.__del__()
            except:
                pass
        if self.messenger:
            self.messenger.stop()
