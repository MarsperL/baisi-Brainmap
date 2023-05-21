from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import sys


class Branch(QGraphicsLineItem):
    """Rewrite QGraphicsLineItem"""
    def __init__(self, *args, **kwargs):
        super(Branch, self).__init__(*args, **kwargs)

        self.srcNode = None
        self.dstNode = None
        self.width = 2
        self.color = Qt.darkBlue
        self.offsetScale = 0.4
        self.setZValue(-1)

    def adjust(self):#调整连接两个节点的连线位置

        # 创建适应于深色和浅色模式的线条颜色
        adaptive_color = QColor.fromCmykF(0.7, 0.4, 0.0, 0.0).toRgb()
        pen = QPen(adaptive_color)
        self.setPen(pen)

        offset = self.offsetScale * self.srcNode.sceneBoundingRect().width()
        p1_x = self.srcNode.sceneBoundingRect().center().x() + offset
        p1_y = self.srcNode.sceneBoundingRect().center().y()
        p1 = QPointF(p1_x, p1_y)#p1的坐标

        p2_x = self.dstNode.sceneBoundingRect().x()
        p2_y = self.dstNode.sceneBoundingRect().center().y()
        p2 = QPointF(p2_x, p2_y)#p2的坐标

        self.setLine(QLineF(p1, p2))#将两点用线相连