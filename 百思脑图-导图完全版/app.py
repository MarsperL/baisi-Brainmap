import subprocess
import sys
import os
import time
from threading import Thread
import functools

import cv2
from PyQt5.QtWidgets import QApplication
from loguru import logger

import mainwindow
from login.models.user import User
from login.utils import global_var as gl, logs
from login.utils.connect_mysql import db
from login.win.login_form import login_form
from login.win.register_form import register_form
from login.win.splash.splash import SplashScreen

# os.chdir(os.path.dirname(__file__))
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.windows = {}

    def run(self, pytest=False):
        logger.info("程序启动 ...")

        splash = SplashScreen()  # 启动界面
        splash.loadProgress()  # 加载界面

        from mainwindow import MainWindow
        self.windows["main"] = MainWindow()
        self.windows["login"] = login_form(self.windows["main"])
        self.windows["login"].show()#显示登录注册界面
        splash.finish(self.windows["main"])
        if not pytest:
            sys.exit(self.exec_())


if __name__ == "__main__":
    logs.setting()  # log 设置
    gl.__init()  # 全局变量
    db.connect() #连接数据库
    App().run()
