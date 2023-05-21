from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import re
import sys
from Config import *


class Node(QGraphicsTextItem):
    """ReWrite QGraphicsTextItem

    Signals:
        nodeChanged: 节点内容更改
        nodeMoved: 节点移动
        nodeEdited: 双击编辑节点
        nodeSelected: 单击选择节点
        nodeLostFocus: 节点失去焦点
    """
    nodeChanged = pyqtSignal()
    nodeMoved = pyqtSignal(int, int)
    nodeEdited = pyqtSignal()
    nodeSelected = pyqtSignal()
    nodeLostFocus = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(Node, self).__init__(*args, **kwargs)

        self.parentNode = None
        self.sonNode = []
        self.x = 0
        self.y = 0
        self.width = 0
        # self.num = 0

        self.m_defaultText = ''
        self.m_note = ''
        self.m_link = 'https://'
        self.hasLink = False
        self.m_size = (60, 30)
        self.m_margin = 30
        self.m_border = False
        self.m_color = QColor(Qt.white)
        self.m_level = -1
        self.m_textColor = QColor(Qt.black)
        self.m_textFont = QFont("楷体")
        self.m_editable = False

        self.setOpenExternalLinks(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)

    def setBorder(self, hasBorder):
        self.m_border = hasBorder
        self.update()

    def setColor(self, color):
        self.m_color = color
        self.update()

    def setTextColor(self, textColor):
        self.m_textColor = textColor
        self.update()

    def setTextFont(self, textFont):
        self.m_textFont = textFont
        self.update()

    def setMargin(self, margin):
        self.margin = margin
        self.update()

    def setEditable(self, editable):
        if not editable:
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            self.setTextInteractionFlags(Qt.TextBrowserInteraction)
            return
        
        self.setTextInteractionFlags(Qt.TextEditorInteraction)

    def setNodeLevel(self, level):
        self.m_level = level

        if level == MainThemeLevel:
            self.setMargin((5, 4))
            self.setColor(QColor(Qt.red))
            self.setTextColor(QColor(Qt.white))
            self.setPlainText('中心主题')
        elif level == SecondThemeLevel:
            self.setMargin((3, 2))
            self.setColor(QColor(162,181,205))
            self.setTextColor(QColor(Qt.black))
            self.setPlainText('分支主题')
        elif level == ThirdThemeLevel:
            self.setMargin((2, 1))
            self.setColor(QColor(255,239,219))
            self.setTextColor(QColor(Qt.black))
            self.setPlainText('子主题')
        elif level == FreeThemeLevel:
            self.setColor(QColor(Qt.gray))
            self.setTextColor(QColor(Qt.blue))
            self.setPlainText('自由主题')

    def insertPicture(self, image):
        self.width = self.boundingRect().width()
        self.height = self.boundingRect().height()

        c = self.textCursor()
        c.setPosition(0)
        self.setTextCursor(c)

        print(image)
        c.insertHtml('<img src="{}" width=15 height=15></img>'.format(image))

    def insertLink(self, link):
        self.width = self.boundingRect().width()
        self.height = self.boundingRect().height()

        c = self.textCursor()
        print(c)

        print(c.document())

        c.setPosition(len(c.document().toPlainText()))
        self.setTextCursor(c)

        c.insertHtml('<a href="{}">'
                        '<img src="./images/link.svg" width=15 height=15></img></a>'.format(link))
    def updateLink(self, link):
        res_url = r"(?<=href=\").+?(?=\")|(?<=href=\').+?(?=\')"
        print(re.sub(res_url, link, self.toHtml(), 1))
        self.setHtml(re.sub(res_url, link, self.toHtml(), 1))

    def paint(self, painter, option, w):
        if self.m_border:
            painter.setPen(QPen(QBrush(Qt.black), 1))
        # else:
        #     painter.setPen(Qt.transparent)

        painter.setBrush(self.m_color)
        painter.drawRoundedRect(self.boundingRect(), 10.0, 5.0)#节点圆角

        painter.setBrush(Qt.NoBrush)
        self.setDefaultTextColor(self.m_textColor)#设置节点内字体颜色
        self.setFont(self.m_textFont)#设置节点内字体样式
        super().paint(painter, option, w)


    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            self.nodeChanged.emit()

        return super().itemChange(change, value)

    def mousePressEvent(self, e):
        self.nodeSelected.emit()
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):
        self.width = self.boundingRect().width()
        self.height = self.boundingRect().height()
        self.nodeEdited.emit()

    def mouseMoveEvent(self, e):
        if not self.parentNode:
            diff = QPointF(e.scenePos() - e.lastScenePos())
            self.nodeMoved.emit(diff.x(), diff.y())

    def focusOutEvent(self, e):
        self.nodeLostFocus.emit()

