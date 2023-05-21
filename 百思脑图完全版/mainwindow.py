# -*- coding: utf-8 -*-
import time

from IPython.external.qt_for_kernel import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *
from loguru import logger
from matplotlib import pyplot as plt
from pyqt5_plugins.examplebutton import QtWidgets
from pyqt5_plugins.examplebuttonplugin import QtGui


from Timer import run_timer
from login.core.MySystemTrayIcon import MySystemTrayIcon
from login.win.close_dialog import close_dialog
import os
import tkinter
import sys
import Node
from Graph import Graph
from Component import *
from Config import *
from threading import Thread

#显示任务栏图标
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")

class MainWindow(QMainWindow):
    """Main Window
    显示应用程序的主窗口
    Signals:
        addNote: (int, int, str) -> (pos_x, pos_y, note_text)
        addLink: (int, int, str) -> (pos_x, pos_y, link_text)
        close_signal: MainWindow close signal
    """
    addNote = pyqtSignal(int, int, str)
    addLink = pyqtSignal(int, int, str)
    close_signal = pyqtSignal()

    def __init__(self, settings=QSettings(SETTINGS_PATH, QSettings.IniFormat)):
        super().__init__()
        # self.path = None
        self.root = QFileInfo(__file__).absolutePath()
        self.m_contentChanged = False
        self.m_filename = None
        self.m_undoStack = None
        self.m_dockShow = True
        self.m_settings = settings
        self.timer = QTimer()
        self.timer.timeout.connect(self.file_autoSave)
        # self.setWindowFlags(Qt.FramelessWindowHint)  # 设置窗口标志：隐藏窗口边
        self.setWindowIcon(QIcon(self.root + '/icons/baisi.png'))
        print(self.root)
        self.scene = Graph()
        self.scene.contentChanged.connect(self.contentChanged)
        self.scene.nodeNumChange.connect(self.nodeNumChange)
        self.scene.messageShow.connect(self.messageShow)
        self.setStyleSheet("QMenuBar::item:selected {\n "
                            " background-color:#E6E6E6;"
                            "color:#0033FF;\n"
                            "border-radius:6px;\n"
                                "}\n"
                            "QMenu::item:selected {\n "
                           " background-color:#E6E6E6;"
                           "color:#0033FF;\n"
                           "}\n"
                           "QToolButton:hover{\n "
                           "background-color:#E6E6E6;\n"
                           "border-radius:10px;\n"
                            "color:#0033FF;\n"
                           "}\n"
                           "QWidget{\n "
                           "background-color: #FAFAFA;\n"
                           "font-family:宋体;\n"
                           "font-size:20px;\n"
                           "}\n")
        self.view = QGraphicsView()
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        # view.setContextMenuPolicy(Qt.CustomContextMenu)
        # view.setInteractive(False)
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)
        self.view.show()

        # 程序托盘图标
        self.show_tray_icon = close_dialog(parent=self)
        self.tray_icon = MySystemTrayIcon()
        self.tray_icon.init(self)  # 将自己传进去
        self.tray_icon.show()

        self.initUI()

    def initUI(self):
        self.setUpDockWidget()
        self.setUpMenuBar()
        self.setUpToolBar()
        self.setUpStatusBar()
        self.setUpIconToolBar()
        self.update_title()
        self.resize(1200, 800)
        self.center()

        self.show()
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def update_title(self):
        self.setWindowTitle('%s - 百思脑图' % (os.path.basename(self.m_filename) if self.m_filename else '未命名'))

    def setUpDockWidget(self):
        """Dock Widget Show Hot Key Help"""

        self.dock = QDockWidget('快捷键说明', self)
        self.dock.setAllowedAreas(Qt.RightDockWidgetArea)
        hotkeyList = QListWidget(self)
        hotkeyList.addItems(['Alt+Z  主题','Alt+K  子主题','Ctrl+F 全屏专注','Esc    退出全屏','Ctrl+X 剪切',
                             'Ctrl+C 复制','Ctrl+N 新建','Ctrl+O 打开','Ctrl+S 保存',
                             'Ctrl+Shift+S 另存为','Ctrl+P 打印','Ctrl+Q 退出','Ctrl+Z 撤销','Ctrl+Y 重做',
                             'Ctrl+V 粘贴','Delete 删除'])
        self.dock.setWidget(hotkeyList)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.hide()

    ###########################################################################
    #
    #  菜单栏
    #
    ###########################################################################
    def setUpMenuBar(self):
        self.m_undoStack = QUndoStack(self)
        # self.m_undoView = QUndoView(self.m_undoStack, self)
        ###########################################################################
        # file menu
        ###########################################################################
        file_menu = self.menuBar().addMenu('文件')

        # new file
        new_file_action = QAction('新建', self)
        new_file_action.setShortcut('Ctrl+N')
        new_file_action.triggered.connect(self.file_new)
        file_menu.addAction(new_file_action)

        # open file
        open_file_action = QAction('打开', self)
        open_file_action.setShortcut('Ctrl+O')
        open_file_action.triggered.connect(self.file_open)
        file_menu.addAction(open_file_action)

        # last open file
        self.last_open_file_menu = QMenu('最近打开', self)
        self.file_last_open()
        file_menu.addMenu(self.last_open_file_menu)

        file_menu.addSeparator()

        # save file
        self.save_file_action = QAction('保存', self)
        self.save_file_action.setShortcut('Ctrl+S')
        self.save_file_action.triggered.connect(self.file_save)
        file_menu.addAction(self.save_file_action)

        # 另存为
        saveas_file_action = QAction('另存为', self)
        saveas_file_action.setShortcut('Ctrl+Shift+S')
        saveas_file_action.triggered.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)

        file_menu.addSeparator()

        # export as 
        exportas_menu = QMenu('导出', self)
        # TODO: function bind with action
        exportas_png_action = QAction('PNG', self)
        exportas_png_action.triggered.connect(self.exportas_png)
        exportas_menu.addAction(exportas_png_action)

        exportas_pdf_action = QAction('PDF', self)
        exportas_pdf_action.triggered.connect(self.exportas_pdf)
        exportas_menu.addAction(exportas_pdf_action)

        file_menu.addMenu(exportas_menu)

        file_menu.addSeparator()

        # print file
        print_action = QAction('打印', self)
        print_action.setShortcut('Ctrl+P')
        print_action.triggered.connect(self.file_print)
        file_menu.addAction(print_action)

        file_menu.addSeparator()

        # quit
        quit_action = QAction('退出', self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.triggered.connect(self.quit)
        file_menu.addAction(quit_action)

        #############################################################################
        # Edit menu
        #############################################################################
        edit_menu = self.menuBar().addMenu('编辑')

        # undo
        self.undo_action = self.m_undoStack.createUndoAction(self, '撤销')
        self.undo_action.setShortcut('Ctrl+Z')
        edit_menu.addAction(self.undo_action)

        # Redo
        self.redo_action = self.m_undoStack.createRedoAction(self, '重做')
        self.redo_action.setShortcut('Ctrl+Y')
        edit_menu.addAction(self.redo_action)

        edit_menu.addSeparator()

        # Cut
        cut_action = QAction('剪切', self)
        cut_action.setShortcut('Ctrl+X')
        cut_action.triggered.connect(self.scene.cut)
        edit_menu.addAction(cut_action)

        # Copy
        copy_action = QAction('复制', self)
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(self.scene.copy)
        edit_menu.addAction(copy_action)

        # Paste
        paste_action = QAction('粘贴', self)
        paste_action.setShortcut('Ctrl+V')
        paste_action.triggered.connect(self.scene.paste)
        edit_menu.addAction(paste_action)

        # Delete
        delete_action = QAction('删除', self)
        delete_action.setShortcut('Delete')
        delete_action.triggered.connect(self.scene.removeNode)
        edit_menu.addAction(delete_action)

        edit_menu.addSeparator()

        ##########################################################################
        # Insert menu
        ##########################################################################
        insert_menu = self.menuBar().addMenu('插入')

        add_notes_action = QAction('笔记', self)
        add_notes_action.triggered.connect(self.add_notes)
        insert_menu.addAction(add_notes_action)

        add_link_action = QAction('链接', self)
        add_link_action.triggered.connect(self.add_link)
        insert_menu.addAction(add_link_action)

        add_icon_action = QAction('图标', self)
        add_icon_action.triggered.connect(self.add_icon)
        insert_menu.addAction(add_icon_action)

        ##########################################################################
        # 全局主题
        ##########################################################################
        theme_menu = self.menuBar().addMenu('全局主题')

        frist_theme_action = QAction('纯净皎白', self)
        frist_theme_action.triggered.connect(self.frist_theme)
        theme_menu.addAction(frist_theme_action)

        second_theme_action = QAction('幽蓝', self)
        second_theme_action.triggered.connect(self.second_theme)
        theme_menu.addAction(second_theme_action)

        third_theme_action = QAction('宇宙尘', self)
        third_theme_action.triggered.connect(self.third_theme)
        theme_menu.addAction(third_theme_action)

        fourth_theme_action = QAction('晨雾', self)
        fourth_theme_action.triggered.connect(self.fourth_theme)
        theme_menu.addAction(fourth_theme_action)

        fifth_theme_action = QAction('蓝海', self)
        fifth_theme_action.triggered.connect(self.fifth_theme)
        theme_menu.addAction(fifth_theme_action)

        sixth_theme_action = QAction('月光', self)
        sixth_theme_action.triggered.connect(self.sixth_theme)
        theme_menu.addAction(sixth_theme_action)

        seventh_theme_action = QAction('海岛', self)
        seventh_theme_action.triggered.connect(self.seventh_theme)
        theme_menu.addAction(seventh_theme_action)

        eighth_theme_action = QAction('夜之轨迹', self)
        eighth_theme_action.triggered.connect(self.eighth_theme)
        theme_menu.addAction(eighth_theme_action)

        ninth_theme_action = QAction('未解之缘', self)
        ninth_theme_action.triggered.connect(self.ninth_theme)
        theme_menu.addAction(ninth_theme_action)
        ##########################################################################
        # Help menu
        ##########################################################################
        help_menu = self.menuBar().addMenu('帮助')

        about_action = QAction('关于', self)
        about_action.triggered.connect(self.about)
        help_menu.addAction(about_action)

        hotKey_help_action = QAction('快捷键说明', self)
        hotKey_help_action.triggered.connect(self.hot_key)
        help_menu.addAction(hotKey_help_action)

        feature_identify_action = QAction('手势控制说明', self)
        feature_identify_action.triggered.connect(self.feature_identify)
        help_menu.addAction(feature_identify_action)

        icon_help_action = QAction('图标工具栏', self)
        icon_help_action.triggered.connect(self.add_icon)
        help_menu.addAction(icon_help_action)

    ###########################################################################
    #
    #  ToolBar
    #
    ############################################################################
    def setUpToolBar(self):
        self.toolbar = self.addToolBar('工具栏')
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        ###########################################################################
        #  New File
        ###########################################################################
        new_file_action = QAction(QIcon(self.root + '/images/filenew.png'), '新建', self)
        new_file_action.triggered.connect(self.file_new)
        self.toolbar.addAction(new_file_action)
        ###########################################################################
        #  Save File
        ###########################################################################
        save_file_action = QAction(QIcon(self.root + '/images/filesave.png'), '保存', self)
        save_file_action.triggered.connect(self.file_save)
        self.toolbar.addAction(save_file_action)
        ###########################################################################
        #  Open File
        ###########################################################################
        open_file_action = QAction(QIcon(self.root + '/images/fileopen.png'), '打开', self)
        open_file_action.triggered.connect(self.file_open)
        self.toolbar.addAction(open_file_action)
        ###########################################################################
        self.toolbar.addSeparator()#分隔符
        #  新建节点
        ###########################################################################
        new_siblingNode_action = QAction(QIcon(self.root + '/images/topicafter.svg'), '主题', self)
        new_siblingNode_action.setShortcut('Alt+Z')
        new_siblingNode_action.triggered.connect(self.scene.addSiblingNode)
        self.toolbar.addAction(new_siblingNode_action)
        ############################################################################
        #  新建子节点
        ############################################################################
        new_sonNode_action = QAction(QIcon(self.root + '/images/subtopic.svg'), '子主题', self)
        new_sonNode_action.setShortcut('Alt+K')
        new_sonNode_action.triggered.connect(self.scene.addSonNode)
        self.toolbar.addAction(new_sonNode_action)
        ############################################################################
        #  Add Branch
        ############################################################################
        # add_branch_action = QAction(QIcon(self.root + '/images/relationship.svg'), '联系', self)
        # add_branch_action.triggered.connect(self.scene.buildRelation)
        # self.toolbar.addAction(add_branch_action)

        ############################################################################
        #  Add Notes
        ############################################################################
        add_notes_action = QAction(QIcon(self.root + '/images/notes.svg'), '笔记', self)
        add_notes_action.triggered.connect(self.add_notes)
        self.toolbar.addAction(add_notes_action)
        ############################################################################
        self.toolbar.addSeparator()  # 分隔符
        #  浅色模式
        ############################################################################
        add_day_action = QAction(QIcon(self.root + '/icons/太阳_sun.svg'), '浅色模式', self)
        add_day_action.triggered.connect(self.add_day)
        self.toolbar.addAction(add_day_action)

        ############################################################################
        #  深色模式
        ############################################################################
        add_dark_action = QAction(QIcon(self.root + '/icons/月亮_moon.svg'), '深色模式', self)
        add_dark_action.triggered.connect(self.add_dark)
        self.toolbar.addAction(add_dark_action)
        ############################################################################
        #  专注记时
        ############################################################################
        time_clock_action = QAction(QIcon(self.root + '/icons/clock.svg'), '专注计时', self)
        time_clock_action.triggered.connect(self.time_clock)
        self.toolbar.addAction(time_clock_action)
        ############################################################################
        #  全屏专注模式
        ############################################################################
        full_screen_action = QAction(QIcon(self.root + '/icons/全局放大1_full-screen-one.svg'), '全屏专注', self)
        full_screen_action.setShortcut('Ctrl+F')
        full_screen_action.triggered.connect(self.full_screen)
        self.toolbar.addAction(full_screen_action)

        ############################################################################

        #  退出全屏模式
        ############################################################################
        normal_screen_action = QAction(QIcon(self.root + '/icons/全局缩小1_off-screen-one.svg'), '退出全屏', self)
        normal_screen_action.setShortcut('Esc')
        normal_screen_action.triggered.connect(self.normal_screen)
        self.toolbar.addAction(normal_screen_action)
        ############################################################################
        self.toolbar.addSeparator()  # 分隔符
        #  Delete
        ############################################################################
        addBranch_action = QAction(QIcon(self.root + '/images/delete.png'), '删除', self)
        addBranch_action.triggered.connect(self.scene.removeNode)
        self.toolbar.addAction(addBranch_action)

        ############################################################################
        #  undo
        #############################################################################
        self.undo_action.setIcon(QIcon(self.root + '/images/undo.png'))
        self.toolbar.addAction(self.undo_action)

        ##############################################################################
        #  redo
        ##############################################################################
        self.redo_action.setIcon(QIcon(self.root + '/images/redo.png'))
        self.toolbar.addAction(self.redo_action)

        self.scene.setUndoStack(self.m_undoStack)

    def setUpIconToolBar(self):
        self.icontoolbar = QToolBar('图标工具栏', self)

        m_signalMapper = QSignalMapper(self)

        # application-system
        application_system_action = QAction(QIcon(self.root + '/icons/applications-system.svg'), '系统应用', self)
        application_system_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(application_system_action, self.root + '/icons/applications-system.svg')

        # trash icon
        trash_action = QAction(QIcon(self.root + '/icons/user-trash-full.svg'), '垃圾', self)
        trash_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(trash_action, self.root + '/icons/user-trash-full.svg')

        # mail icon
        mail_action = QAction(QIcon(self.root + '/icons/mail-attachment.svg'), '邮件', self)
        mail_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(mail_action, self.root + '/icons/mail-attachment.svg')

        # warn icon
        warn_action = QAction(QIcon(self.root + '/icons/dialog-warning.svg'), '警告', self)
        warn_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(warn_action, self.root + '/icons/dialog-warning.svg')

        # how icon
        help_action = QAction(QIcon(self.root + '/icons/help-browser.svg'), '帮助', self)
        help_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(help_action, self.root + '/icons/help-browser.svg')

        # calendar icon
        calendar_action = QAction(QIcon(self.root + '/icons/x-office-calendar.svg'), '日历', self)
        calendar_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(calendar_action, self.root + '/icons/x-office-calendar.svg')

        # system_users icon
        system_users_action = QAction(QIcon(self.root + '/icons/system-users.svg'), '系统用户', self)
        system_users_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(system_users_action, self.root + '/icons/system-users.svg')

        # info icon
        info_action = QAction(QIcon(self.root + '/icons/dialog-information.svg'), '信息', self)
        info_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(info_action, self.root + '/icons/dialog-information.svg')

        m_signalMapper.mapped[str].connect(self.scene.insertPicture)

        self.icontoolbar.addAction(application_system_action)
        self.icontoolbar.addAction(trash_action)
        self.icontoolbar.addAction(mail_action)
        self.icontoolbar.addAction(warn_action)
        self.icontoolbar.addAction(help_action)
        self.icontoolbar.addAction(calendar_action)
        self.icontoolbar.addAction(system_users_action)
        self.icontoolbar.addAction(info_action)

        self.addToolBar(Qt.LeftToolBarArea, self.icontoolbar)
        self.icontoolbar.hide()

    def setUpStatusBar(self):
        zoomSlider = MySlider(self.view, Qt.Horizontal)
        zoomSlider.setMaximumWidth(200)
        zoomSlider.setRange(1, 200)
        zoomSlider.setSingleStep(10)
        zoomSlider.setValue(100)

        self.label1 = QLabel('100%')
        self.label2 = QLabel('节点总数: 1')
        self.label3 = QLabel('欢迎使用百思脑图！')

        widget = QWidget(self)
        hbox = QHBoxLayout()

        hbox.addWidget(self.label2)
        hbox.addWidget(zoomSlider)
        hbox.addWidget(self.label1)
        hbox.addWidget(self.label3)

        widget.setLayout(hbox)

        zoomSlider.valueChanged.connect(self.labelShow)

        self.statusBar().addWidget(widget, 5)

    def nodeNumChange(self, v):
        self.label2.setText('节点总数: ' + str(v))

    def labelShow(self, v):
        self.label1.setText(str(v) + '%')

    def messageShow(self, text):
            self.label3.setText(text)


    def contentChanged(self, changed=True):
        print(self.m_contentChanged)
        if not self.m_contentChanged and changed:
            self.timer.start(AUTOSAVE_TIME)
            self.setWindowTitle('*' + self.windowTitle())
            self.m_contentChanged = True

            fileinfo = QFileInfo(self.m_filename)
            if '未命名' not in self.windowTitle() and fileinfo.isWritable():
                self.save_file_action.setEnabled(True)

        elif self.m_contentChanged and not changed:
            self.timer.stop()
            self.setWindowTitle(self.windowTitle()[1:])
            self.m_contentChanged = False
            self.save_file_action.setEnabled(False)

    # TODO: scene center move
    def file_new(self):
        if not self.close_file():
            return

        self.m_filename = None
        self.scene.addFirstNode()
        self.update_title()

    # TODO: 确保文件有效 !
    def file_open(self, filename=''):
        if not self.close_file():
            return

        cur_filename = self.m_filename
        if not filename:
            if self.sender().text() in self.m_settings.value('lastpath'):
                self.m_filename = self.root + '/files/' + self.sender().text()
                print(self.m_filename)
            else:
                dialog = QFileDialog(self, '打开', self.root + '/files', 'MindMap(*.mm)')
                dialog.setAcceptMode(QFileDialog.AcceptOpen)
                dialog.setDefaultSuffix('mm')

                if not dialog.exec():
                    return
                self.m_filename = dialog.selectedFiles()[0]
        else:
            self.m_filename = filename

        fileInfo = QFileInfo(self.m_filename)
        if not fileInfo.isWritable():
            print('只读文件！')

        if not self.scene.readContentFromXmlFile(self.m_filename):
            self.m_filename = cur_filename
            return

        lastpath = self.m_settings.value('lastpath')
        if os.path.basename(self.m_filename) not in lastpath:
            lastpath.append(os.path.basename(self.m_filename))
            self.m_settings.setValue('lastpath', lastpath)
            self.file_last_open()

        self.update_title()

    def file_last_open(self):
        lastpath = self.m_settings.value('lastpath')

        if not lastpath:
            last_open_action = QAction('无最近打开文件', self)
            self.last_open_file_menu.addAction(last_open_action)
        else:
            self.last_open_file_menu.clear()
            for filename in lastpath:
                last_open_action = QAction(filename, self)
                last_open_action.triggered.connect(self.file_open)
                self.last_open_file_menu.addAction(last_open_action)

    def file_save(self, checkIfReadOnly=True):
        fileinfo = QFileInfo(self.m_filename)
        if checkIfReadOnly and not fileinfo.isWritable():
            self.messageShow('错误：该文件为只读文件！')
            return

        print(self.m_filename)
        self.scene.writeContentToXmlFile(self.m_filename)
        self.contentChanged(False)
        self.m_undoStack.clear()

    def file_autoSave(self):
        fileInfo = QFileInfo(self.m_filename)
        if self.windowTitle() != '未命名' and fileInfo.isWritable():
            self.file_save()

    def file_saveas(self):
        dialog = QFileDialog(self, '将思维导图另存为', self.root + '/files', 'MindMap(*.mm)')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('mm')

        if not dialog.exec():
            return False

        self.m_filename = dialog.selectedFiles()[0]
        print(dialog.selectedFiles())
        self.file_save(False)
        self.update_title()

    def file_print(self):
        printer = QPrinter(QPrinter.HighResolution)
        if QPrintDialog(printer).exec() == QDialog.Accepted:
            painter = QPainter(printer)
            painter.setRenderHint(QPainter.Antialiasing)
            self.scene.render(painter)
            painter.end()

    def close_file(self):
        if self.m_contentChanged:
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle('保存思维导图')
            msgBox.setText('思维导图已修改！')
            msgBox.setInformativeText('是否要保存此文件？')
            msgBox.addButton(QMessageBox.Save).setText('保存')
            msgBox.addButton(QMessageBox.Cancel).setText('取消')
            msgBox.addButton(QMessageBox.Discard).setText('直接退出')
            msgBox.setDefaultButton(QMessageBox.Save)
            ret = msgBox.exec()

            if ret == QMessageBox.Save:
                if '未命名' in self.windowTitle():
                    if not self.file_saveas():
                        return False
                else:
                    self.file_save()
            elif ret == QMessageBox.Cancel:
                return False

        self.m_contentChanged = False
        self.scene.removeAllNodes()
        self.scene.removeAllBranches()
        self.m_undoStack.clear()
        return True

    def exportas_png(self):
        dialog = QFileDialog(self, '将思维导图导出为', self.root + '/files', 'MindMap(*.png)')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('png')

        if not dialog.exec():
            return False

        png_filename = dialog.selectedFiles()[0]
        print(dialog.selectedFiles())
        self.scene.writeContentToPngFile(png_filename)

    def exportas_pdf(self):
        dialog = QFileDialog(self, '将思维导图导出为', self.root + '/files', 'MindMap(*.pdf)')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('pdf')

        if not dialog.exec():
            return False

        pdf_filename = dialog.selectedFiles()[0]
        print(dialog.selectedFiles())
        self.scene.writeContentToPdfFile(pdf_filename)

    def quit(self):
        self.close_signal.emit()
        if self.m_contentChanged and not self.close_file():
            return
        qApp.quit()

    def close_Event(self, e):
        self.close_signal.emit()
        if self.m_contentChanged and not self.close_file():
            e.ignore()
        else:
            e.accept()

    def getPos(self, size):
        p = QPointF(self.scene.m_activateNode.boundingRect().center().x(),
                    self.scene.m_activateNode.boundingRect().bottomRight().y())
        sceneP = self.scene.m_activateNode.mapToScene(p)
        viewP = self.view.mapFromScene(sceneP)
        pos = self.view.viewport().mapToGlobal(viewP)
        x = pos.x() - size[0] / 2
        y = pos.y()
        return x, y

    def add_notes(self):
        x, y = self.getPos(NOTE_SIZE)
        print(x, y)
        self.addNote.emit(x, y, self.scene.m_activateNode.m_note)

    def getNote(self, note):
        self.scene.m_activateNode.m_note = note

    #浅色模式
    def add_day(self):
        self.setStyleSheet("QMenuBar::item:selected {\n "
                            " background-color:#E6E6E6;"
                             "color:#0033FF;\n"
                            "border-radius:6px;\n"
                                "}\n"
                            "QMenu::item:selected {\n "
                           " background-color:#E6E6E6;"
                           "color:#0033FF;\n"
                           "}\n"
                           "QToolButton:hover{\n "
                           "background-color:#E6E6E6;\n"
                           "border-radius:10px;\n"
                            "color:#0033FF;\n"
                           "}\n"
                            "QWidget{\n "
                           "background-color: #FAFAFA;\n"
                           "font-family:宋体;\n"
                           "font-size:20px;\n"
                           "}\n")
        self.messageShow('浅色模式已启动')

    # 深色模式
    def add_dark(self):
        self.setStyleSheet("QMenuBar::item:selected {\n "
                           " background-color:#3399ff;"
                           "border-radius:6px;\n"
                           "}\n"
                            "QMenu::item:selected {\n "
                           " background-color:#3399ff;"
                           "}\n"
                            "QToolButton:hover{\n "
                           " background-color:#3399ff;"
                           "border-radius:10px;\n"
                           "}\n"
                            "QWidget{\n "
                           "background-color:rgb(30,43,59);\n"
                           "font-family:宋体;\n"
                           "color:rgb(2,255,232);\n"
                           "font-size:20px;\n"
                           "border-radius:0px;\n"
                           "}\n")
        self.messageShow('深色模式已启动')
    #专注记时
    def time_clock(self):
        run_timer()
    #全屏
    def full_screen(self):
        self.showFullScreen()
        self.messageShow('开启全屏专注')
    #退出全屏
    def normal_screen(self):
        self.showNormal()
        self.messageShow('已退出全屏')

    #全局主题
    #纯净皎白
    def frist_theme(self):
        self.setStyleSheet( "QMenu,QToolButton{\n "
                           "font-family:宋体;\n"
                           "font-size:20px;\n"
                            "}\n"
                             "QMenuBar::item:selected {\n "
                                " background-color:#3399ff;"
                                "border-radius:6px;\n"
                                "}\n"
                                "QMenu::item:selected {\n "
                                " background-color:#3399ff;"
                                "}\n"
                             "QToolButton:hover{\n "
                            " background-color:rgb(204,232,255);"
                             "border-radius:10px;\n"
                            "}\n"
                            "QWidget{\n "
                           "background-color: #FFFFFF;\n"
                           "font-family:宋体;\n"
                           "font-size:20px;\n"
                           "border-radius:0px;\n"
                           "}\n")
        self.messageShow('正使用纯净皎白主题')
    # 幽蓝
    def second_theme(self):
        color = QColor(30, 43, 59)
        if color.isValid():
            self.setStyleSheet( "QMenu,QToolButton{\n "
                                "font-family:宋体;\n"
                                "font-size:20px;\n"
                                 "border-radius:10px;\n"
                                 "}\n"
                                "QMenuBar::item:selected {\n "
                                " background-color:#3399ff;"
                                "}\n"
                                "QMenu::item:selected {\n "
                                " background-color:#3399ff;"
                                "}\n"
                                "QToolButton{\n "
                            " color:#FFFFFF;"
                            " border-radius:10px;\n"
                            "}\n"
                                "QToolButton:hover{\n "
                            " background-color:#3399ff;"
                            "}\n"
                                "QToolBar,QMenuBar,QDockWidget,QFrame,QMainWindow"
                               "{ background-color: %s;"
                               "color:#FFFFFF; "
                               "font-family:宋体;"
                                " border-radius:10px;\n"
                               "font-size:20px;"
                               "}" % color.name())
            self.messageShow('正使用幽蓝主题')
    # 宇宙尘
    def third_theme(self):
        self.setStyleSheet("QMenuBar::item:selected {\n "
                           " background-color:#3399ff;"
                            " border-radius:8px;\n"
                           "}\n"
                            "QMenu::item:selected {\n "
                           " background-color:#3399ff;"
                            " border-radius:8px;\n"
                           "}\n"
                            "QToolButton:hover{\n "
                           " background-color:#3399ff;"
                            " border-radius:10px;\n"
                           "}\n"
                            "QWidget{\n "
                           "background-color:rgb(34,36,37);\n"
                           "font-family:宋体;\n"
                           "color:#FFFFFF;\n"
                            " border-radius:10px;\n"
                           "font-size:20px;\n"
                           "}\n")
        self.messageShow('正使用宇宙尘主题')
    # 晨雾
    def fourth_theme(self):
        self.setStyleSheet("QMenu,QToolButton{\n "
                           "font-family:宋体;\n"
                           "font-size:20px;\n"
                            "}\n"
                            "QFrame{\n "
                           "background-color: #ffffff;\n"
                           "font-family:宋体;\n"
                           "font-size:20px;\n"
                           "}\n"
                            "QToolBar,QMenuBar,QDockWidget{\n"
                           "background-color: #FAFAFA;\n"
                           "font-family:宋体;\n"
                           "font-size:20px;\n"
                           "}\n")
        self.messageShow('正使用晨雾主题')
    # 蓝海
    def fifth_theme(self):
        self.setStyleSheet(
                            "QMenuBar::item:selected{\n "
                           " background-color:rgb(204,232,255);"
                            " border-radius:6px;\n"
                           "}\n"
                           "QMenu::item:selected {\n "
                           " background-color:rgb(204,232,255);"
                           "}\n"
                           "QToolButton:hover{\n "
                           " background-color:rgb(204,232,255);"
                            " border-radius:10px;\n"
                           "}\n"
                           "QWidget{\n "
                           "font-family:宋体;\n"
                           "color:#000000;\n"
                           " background-color:#FFFFFF;"
                            " border-radius:1px;\n"
                           "font-size:20px;\n"
                           "}\n"
                            "QMenuBar{\n "
                            " background-color:rgb(0,120,215);"
                            "}\n")
        self.messageShow('正使用蓝海主题')
    #月光
    def sixth_theme(self):
        self.setStyleSheet("QMenuBar::item:selected {\n "
                           " background-color:#3399ff;"
                           " border-radius:6px;\n"
                           "}\n"
                           "QMenu::item:selected {\n "
                           " background-color:#3399ff;"
                           "}\n"
                           "QToolButton:hover{\n "
                           " background-color:#3399ff;"
                           "}\n"
                           "QWidget{\n "
                           "background-color:#0C4C7D;\n"
                           "font-family:宋体;\n"
                           "color:#FFFFFF;\n"
                           " border-radius:6px;\n"
                           "font-size:20px;\n"
                           "}\n")
        self.messageShow('正使用月光主题')

        # 海岛
    def seventh_theme(self):
        self.setStyleSheet("QMenu,QToolButton{\n "
                           "font-family:宋体;\n"
                           "font-size:20px;\n"
                           "background-color:#20dfdf;"
                           "color:#8020df;"
                           "}\n"
                           "QMenuBar::item:selected {\n "
                           " background-color:#3399ff;"
                           " border-radius:5px;\n"
                           "}\n"
                           "QMenu::item:selected {\n "
                           " background-color:#3399ff;"
                           "}\n"
                           "QToolButton{\n "
                           "color:#8020df;"
                           "}\n"
                           "QToolButton:hover{\n "
                           " background-color:#3399ff;"
                           " border-radius:10px;\n"
                           "}\n"
                           "QToolBar,QMenuBar,QDockWidget,QFrame,QMainWindow"
                           "{ background-color:#20dfdf;"
                           "color:#8020df; "
                           " border-radius:6px;\n"
                           "font-family:宋体;"
                           "font-size:20px;"
                           "}")
        self.messageShow('正使用海岛主题')

    # 夜之轨迹
    def eighth_theme(self):
        self.setStyleSheet("QMenuBar::item:selected {\n "
                           " background-color:rgb(204,232,255);"
                           " border-radius:6px;\n"
                           "}\n"
                           "QMenu::item:selected {\n "
                           " background-color:rgb(204,232,255);"
                           "}\n"
                           "QToolButton:hover{\n "
                           " background-color:rgb(204,232,255);"
                           "}\n"
                           "QWidget{\n "
                           "background-color:#364259;\n"
                           "font-family:宋体;\n"
                           "color:#579C8E;\n"
                           "font-size:20px;\n"
                            "font-weight:bold;"
                           " border-radius:10px;\n"
                           "}\n")
        self.messageShow('正使用夜之轨迹主题')
    # 未解之缘
    def ninth_theme(self):
        self.setStyleSheet("QMenuBar::item:selected {\n "
                            " background-color:rgb(204,232,255);"
                           " border-radius:6px;\n"
                            "}\n"
                            "QMenu::item:selected {\n "
                            " background-color:rgb(204,232,255);"
                            "}\n"
                            "QToolButton:hover{\n "
                            " background-color:rgb(204,232,255);"
                            "}\n"
                            "QWidget{\n "
                            "background-color:#2C2B58;\n"
                            "font-family:宋体;\n"
                            "color:#5F79FD;\n"
                            "font-size:20px;\n"
                           " border-radius:10px;\n"
                            "}\n"  )
        self.messageShow('正使用未解之缘主题')
    def add_link(self):
        x, y = self.getPos(LINK_SIZE)
        print(x, y)
        self.addLink.emit(x, y, self.scene.m_activateNode.m_link)

    def getLink(self, link):
        self.scene.m_activateNode.m_link = link
        if not self.scene.m_activateNode.hasLink and link != 'https://':
            self.scene.m_activateNode.hasLink = True
            self.scene.m_activateNode.insertLink(link)
            self.scene.adjustSubTreeNode()
            self.scene.adjustBranch()
        elif self.scene.m_activateNode.hasLink:
            self.scene.m_activateNode.updateLink(link)

    def about(self):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle('关于百思脑图')
        msgBox.setText('基于手势控制的思维导图')
        msgBox.setTextFormat(Qt.RichText)
        msgBox.setInformativeText('源自: \n MarsperL')
        pic = QPixmap(self.root + '/icons/baisi.png')
        msgBox.setIconPixmap(pic.scaled(30, 30))
        msgBox.exec()

    def hot_key(self):
        if self.dock.isVisible():
            self.dock.hide()
        else:
            self.dock.show()

    def feature_identify(self):
        os.startfile(r"手势控制说明.pdf")
    def add_icon(self):
        if self.icontoolbar.isVisible():
            self.icontoolbar.hide()
        else:
            self.icontoolbar.show()
    def closeEvent(self, event):
        logger.info("是否关闭主窗口")
        event.ignore()
        self.show_tray_icon.show()
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     app.setApplicationName('百思脑图')
#
#     window = MainWindow()
#     NoteWindow = Note()
#     LinkWindow = Link()
#
#     window.addNote.connect(NoteWindow.handle_addnote)
#     window.close_signal.connect(NoteWindow.handle_close)
#     window.scene.press_close.connect(NoteWindow.handle_close)
#
#     NoteWindow.note.connect(window.getNote)
#     NoteWindow.noteChange.connect(window.contentChanged)
#
#     window.addLink.connect(LinkWindow.handle_addLink)
#     window.close_signal.connect(LinkWindow.handle_close)
#     window.scene.press_close.connect(LinkWindow.handle_close)
#
#     LinkWindow.link.connect(window.getLink)
#     LinkWindow.linkChange.connect(window.contentChanged)
#
#     sys.exit(app.exec_())


