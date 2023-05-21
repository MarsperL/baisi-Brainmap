import os
import sys
import time

import cv2
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QMouseEvent

from mainwindow import MainWindow
from PyQt5.QtWidgets import QFrame, QMainWindow, QApplication, QMessageBox
from loguru import logger
from playhouse.shortcuts import model_to_dict
from login.models.user import User
from login.ui.login_form import Ui_Frame as ui_form
from login.win.mysql_form import mysql_form
from login.win.register_form import register_form

class login_form(ui_form, QFrame):
    def __init__(self, parent: QMainWindow = None):
        super(login_form, self).__init__()
        self.root = parent
        self.root.hide()  # 隐藏主窗体
        self.setupUi(self)
        self.root.tray_icon.hide()  # 先隐藏托盘图标

        # 加载字体
        QtGui.QFontDatabase.addApplicationFont("res/otf/Social Media Circled.otf")

        # 隐藏原始的框
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # 按钮事件绑定
        self.close_pushButton.clicked.connect(self.close_event)
        self.min_pushButton.clicked.connect(self.showMinimized)

        self.login_pushButton.clicked.connect(self.login_pushButton_event)
        self.password_lineEdit.returnPressed.connect(self.login_pushButton_event)#按回车登录
        self.forget_password_pushButton.clicked.connect(self.forget_password_pushButton_event)
        self.register_pushButton.clicked.connect(self.register_pushButton_event)

        # self.mysql_pushButton.clicked.connect(self.mysql_pushButton_event)

        # 底部按钮
        self.github_pushButton.clicked.connect(self.github_pushButton_event)
        self.phone_pushButton.clicked.connect(self.phone_pushButton_event)
        self.email_pushButton.clicked.connect(self.email_pushButton_event)

    # 关闭的逻辑
    def close_event(self):
        logger.info("关闭登录窗口")
        # 退出应用程序
        QApplication.instance().quit()

    # # 数据库
    # def mysql_pushButton_event(self):
    #     logger.info("数据库窗口")
    #     self.mysql_form = mysql_form()
    #     self.mysql_form.show()

    def login_pushButton_event(self):
        logger.info("用户登录")
        # 登录的逻辑写在这里
        user_name = self.user_name_lineEdit.text().strip()
        password = self.password_lineEdit.text().strip()#srtip去除空格,降低输入失误
        #进入管理员模式(数据库)
        if user_name == "admin" or password == "123456":
            QMessageBox.information(self, "登录成功", "你好管理员")
            logger.info("数据库窗口")
            self.mysql_form = mysql_form()
            self.mysql_form.admin_login_pushButton_event()
            self.mysql_form.show()#显示数据库
            self.hide()#将登录界面隐藏
            return
        if user_name == "" or password == "":
            QMessageBox.information(self, "错误提示", "请输入用户名密码")
            return
        info = User.select_from_user_name_and_password(user_name, password)
        if info is not None:
            # 登录成功
            # QMessageBox.information(self, "登录成功", "欢迎用户：\n" + str(info.user_name)
            #                         + "\n" + str(model_to_dict(info)))
            QMessageBox.information(self, "登录成功", "欢迎用户：\n"+ str(info.user_name) )
            self.root.show()  # 显示主窗体
            self.root.tray_icon.show()  # 显示托盘图标
            self.hide()
        else:
            QMessageBox.information(self, "错误提示", "用户名密码错误，请重试")

    def forget_password_pushButton_event(self):
        logger.info("忘记密码")
        QMessageBox.information(self, "忘记密码", "请联系管理员admin")

    def register_pushButton_event(self):
        global hasRun
        logger.info("用户注册")
        self.register_form = register_form()
        self.register_form.show()#显示注册

    def github_pushButton_event(self):
        logger.info("跳转到github网站")
        QMessageBox.information(self, "GitHub", "MarsperL")
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/MarsperL"))

    def phone_pushButton_event(self):
        logger.info("手机号")
        QMessageBox.information(self, "手机号", "手机号\n秘密(～￣▽￣)～")

    def email_pushButton_event(self):
        logger.info("邮箱")
        QMessageBox.information(self, "邮箱", "邮箱\n2107944510@qq.com")

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._isTracking = True
            self._startPos = QPoint(e.x(), e.y())

    def mouseMoveEvent(self, e: QMouseEvent):  # 重写移动事件
        self._endPos = e.pos() - self._startPos
        self.move(self.pos() + self._endPos)

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._isTracking = False
            self._startPos = None
            self._endPos = None

    def open_Main(self):
       self.new_main = MainWindow()
       self.new_main.show()
       self.close()

if __name__ == '__main__':
    login_form()
