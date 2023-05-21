from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import sys
from mainwindow import MainWindow
from Component import *

def main_map():
    app = QApplication(sys.argv)
    app.setApplicationName('百思脑图')

    settings = QSettings(SETTINGS_PATH, QSettings.IniFormat)
    if not settings.value('lastpath'):
        settings.setValue('lastpath', [])  # 写入数据
    window = MainWindow(settings)
    NoteWindow = Note()
    LinkWindow = Link()

    window.addNote.connect(NoteWindow.handle_addnote)
    window.close_signal.connect(NoteWindow.handle_close)
    window.scene.press_close.connect(NoteWindow.handle_close)

    NoteWindow.note.connect(window.getNote)
    NoteWindow.noteChange.connect(window.contentChanged)

    window.addLink.connect(LinkWindow.handle_addLink)
    window.close_signal.connect(LinkWindow.handle_close)
    window.scene.press_close.connect(LinkWindow.handle_close)

    LinkWindow.link.connect(window.getLink)
    LinkWindow.linkChange.connect(window.contentChanged)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main_map()
