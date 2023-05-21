from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtXml import *
from PyQt5.QtPrintSupport import *

import os
import sys
import math
import time
import random
import xml.etree.ElementTree as ET

from Node import Node
from Branch import Branch
from Command import *
from Config import *


class Graph(QGraphicsScene):
    """ReWrite QGraphicsScene

    Add Node and Branch to Scene

    Signals:
        contentChanged: 节点内容变化信号
        nodeNumChange: 节点数量已更改
        messageShow: 状态栏中显示的消息
        press_close: 按场景关闭子窗口(备注窗口和链接窗口)
    """
    brachDistance = 80
    contentChanged = pyqtSignal()
    nodeNumChange = pyqtSignal(int)
    messageShow = pyqtSignal(str)
    press_close = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(Graph, self).__init__(*args, **kwargs)

        self.center_x = self.sceneRect().x() + self.sceneRect().width() / 2
        self.center_y = self.sceneRect().y() + self.sceneRect().height() / 2
        self.m_activateNode = None

        self.NodeList = []
        self.BranchList = []
        self.m_context = None
        self.m_editingMode = False

        self.addFirstNode()

    # 生成 节点 并且将 节点 与 线 连接
    def nodeFactory(self):
        node = Node()
        node.nodeChanged.connect(self.nodeChanged)
        node.nodeEdited.connect(self.nodeEdited)
        node.nodeSelected.connect(self.nodeSelected)
        node.nodeMoved.connect(self.nodeMoved)
        node.nodeLostFocus.connect(self.nodeLostFocus)
        return node

    def setUndoStack(self, stack):
        self.m_undoStack = stack

    def addFirstNode(self):
        node = self.nodeFactory()
        node.setPos(self.center_x, self.center_y)
        node.setNodeLevel(MainThemeLevel)

        self.setActivateNode(node)

        self.addItem(node)
        self.NodeList.append(node)

    # 添加 分支
    def addBranch(self, srcNode, dstNode):
        branch = Branch()
        branch.srcNode = srcNode
        branch.dstNode = dstNode
        branch.adjust()

        self.addItem(branch)
        self.BranchList.append(branch)

    # 删除 分支
    def removeBranch(self, m_node):
        for branch in self.BranchList:
            if branch.srcNode == m_node or branch.dstNode == m_node:
                self.removeItem(branch)
                self.BranchList.remove(branch)

    # 设置活动节点
    def setActivateNode(self, node):
        if self.m_activateNode is not None:
            self.m_activateNode.setBorder(False)

        self.m_activateNode = node
        self.m_activateNode.setBorder(True)

    # 获得子节点的最大位置
    def getSonNodeMaxPos(self):
        maxY = -float('inf')
        for node in self.getSubTree(self.m_activateNode):
            if node.y > maxY:
                maxY = node.y
        # print('maxY: ', maxY)
        return maxY

    # dfs
    def getSubTree(self, node):
        subTree = []
        if node is None:
            return

        queue = []
        queue.insert(0, node)

        while queue:
            v = queue.pop()
            print('v: {}  center: {} '.format(v, (v.x, v.y)))
            subTree.append(v)
            for sonNode in v.sonNode:
                queue.insert(0, sonNode)

        return subTree

    # 子树分支
    def getSubTreeBranch(self, node):
        subTreeBranch = []
        nodeList = self.getSubTree(node)
        for branch in self.BranchList:
            if branch.dstNode in nodeList:
                subTreeBranch.append(branch)

        return subTreeBranch

    # 移动子树
    def moveTree(self, node, dy):
        subTree = self.getSubTree(node)
        for subNode in subTree:
            subNode.moveBy(0, dy)
            subNode.y += dy

    # 调整父树位置
    def adjustNode(self, parent, son, reverse=False):
        sign = 1 if reverse else -1
        for node in parent.sonNode:
            if node.y < son.y:
                self.moveTree(node, sign * (node.m_margin + node.m_size[1]) / 2)
            elif node.y > son.y:
                self.moveTree(node, -1 * sign * (node.m_margin + node.m_size[1]) / 2)
            else:
                continue

        if parent.parentNode:
            self.adjustNode(parent.parentNode, parent, reverse)

    # adjust branch dfter adjust node position
    def adjustBranch(self):
        for branch in self.BranchList:
            branch.adjust()

    # TODO: Two side node
    def getSonPos(self):
        if len(self.m_activateNode.sonNode) == 0:
            print('my y: {0}, scene y: {1}:'.format(self.m_activateNode.y,
                                                    self.m_activateNode.sceneBoundingRect().y()))
            print('激活节点: ', self.m_activateNode.boundingRect().width())
            return self.m_activateNode.sceneBoundingRect().width() + \
                   self.m_activateNode.sceneBoundingRect().x() + \
                   self.brachDistance, \
                self.m_activateNode.sceneBoundingRect().y()
        else:
            maxY = self.getSonNodeMaxPos()
            return self.m_activateNode.sceneBoundingRect().width() + \
                   self.m_activateNode.sceneBoundingRect().x() + \
                   self.brachDistance, \
                   maxY + self.m_activateNode.m_margin

    # 添加子节点
    def addSonNode(self):
        if not self.m_activateNode:
            print('警告：没有激活节点！')
            self.messageShow.emit('警告：没有激活节点！')
            return

        m_context = Context()  # Context 为局部对象, 不要共享为全局对象, 引用传递会出现错误
        m_context.m_activateNode = self.m_activateNode
        m_context.m_scene = self
        m_context.m_pos = self.getSonPos()

        insertNodeCommand = InsertNodeCommand(m_context)
        self.m_undoStack.push(insertNodeCommand)

        self.contentChanged.emit()
        self.nodeNumChange.emit(len(self.NodeList))
        self.messageShow.emit('提示：添加新节点！')
    #添加分支节点
    def addSiblingNode(self):
        if not self.m_activateNode:
            print('警告：没有激活节点！')
            self.messageShow.emit('警告：没有激活节点！')
            return

        if not self.m_activateNode.parentNode:
            print('警告：默认节点！')
            self.messageShow.emit('警告：默认节点！')
            return

        self.m_activateNode.m_border = False
        self.m_activateNode = self.m_activateNode.parentNode
        self.addSonNode()

    # 删除节点
    def removeNode(self):
        if not self.m_activateNode:
            print('警告：没有激活节点！')
            self.messageShow.emit('警告：没有激活节点！')
            return
        if self.m_activateNode.parentNode is None:
            print('警告：默认节点！')
            self.messageShow.emit('警告：默认节点！')
            return

        m_context = Context()
        m_context.m_activateNode = self.m_activateNode
        m_context.m_scene = self
        m_context.m_nodeList = self.getSubTree(self.m_activateNode)

        removeNodeCommand = RemoveNodeCommand(m_context)
        self.m_undoStack.push(removeNodeCommand)

        self.contentChanged.emit()
        self.nodeNumChange.emit(len(self.NodeList))
        self.messageShow.emit('提示：删除节点！')

    # 节点 移动
    def nodeMoved(self, x, y):
        if not self.m_activateNode:
            print('警告: 没有激活节点！')
            self.messageShow.emit('警告: 没有激活节点！')
            return

        m_context = Context()
        m_context.m_activateNode = self.m_activateNode
        m_context.m_scene = self
        m_context.m_pos = [x, y]
        m_context.m_nodeList = self.getSubTree(self.m_activateNode)

        moveCommand = MoveCommand(m_context)
        self.m_undoStack.push(moveCommand)

        self.messageShow.emit('提示：移动节点！')

    # 节点 选中
    def nodeSelected(self):
        sender = self.sender()
        print('节点选择的发送者: ', sender)
        # print('node number: ', sender.num)
        self.setActivateNode(sender)

    # 节点 文本编辑
    def nodeEdited(self):
        print('节点编辑模式')
        print(self.m_activateNode.toHtml())
        if not self.m_activateNode:
            print('警告: 没有激活节点！')
            self.messageShow.emit('警告: 没有激活节点！')
            return

        self.m_editingMode = True
        self.m_activateNode.setEditable(True)
        self.setFocusItem(self.m_activateNode)

        self.messageShow.emit('提示：编辑节点！')

    def nodeChanged(self):
        # self.adjustBranch()
        self.contentChanged.emit()

        # 递归调整树, 以使 rootNode 在 subtree 中处于中点

    def adjustSubTreeNode(self):
        dx = self.m_activateNode.sceneBoundingRect().width() - self.m_activateNode.width
        dy = self.m_activateNode.sceneBoundingRect().height() - self.m_activateNode.height
        nodeList = self.getSubTree(self.m_activateNode)
        for node in nodeList:
            if node == self.m_activateNode:
                if dy:
                    self.m_activateNode.y -= dy / 2
                    self.m_activateNode.moveBy(0, -dy / 2)
                else:
                    continue
            else:
                node.x += dx
                node.moveBy(dx, 0)

    # Node 失焦事件
    def nodeLostFocus(self):
        print('focusOut')
        if self.m_editingMode:
            self.m_editingMode = False
            print(self.m_activateNode.boundingRect().width())
            self.adjustSubTreeNode()
            self.adjustBranch()
            if self.m_activateNode:
                self.m_activateNode.setEditable(False)

    def moveUp(self):
        if self.m_activateNode.parentNode and \
                len(self.m_activateNode.parentNode.sonNode) > 1:

            activateY = self.m_activateNode.y
            closestY = -float('inf')
            closestNode = None

            for node in self.m_activateNode.parentNode.sonNode:
                if node.y < activateY and closestY < node.y:
                    closestY = node.y
                    closestNode = node
            if closestNode is not None:
                self.setActivateNode(closestNode)

    def moveDown(self):
        if self.m_activateNode.parentNode and \
                len(self.m_activateNode.parentNode.sonNode) > 1:

            activateY = self.m_activateNode.y
            closestY = float('inf')
            closestNode = None

            for node in self.m_activateNode.parentNode.sonNode:
                if node.y > activateY and closestY > node.y:
                    closestY = node.y
                    closestNode = node
            if closestNode is not None:
                self.setActivateNode(closestNode)

    def moveRight(self):
        if self.m_activateNode.sonNode:
            minY = float('inf')
            minNode = None
            for node in self.m_activateNode.sonNode:
                if node.y < minY:
                    minY = node.y
                    minNode = node
            self.setActivateNode(minNode)

    def moveLeft(self):
        if self.m_activateNode.parentNode:
            self.setActivateNode(self.m_activateNode.parentNode)

    # 通过方向键移动 activateNode
    def keyPressEvent(self, e):
        if self.m_activateNode and not self.m_editingMode:

            if e.key() == Qt.Key_Escape:
                self.nodeLostFocus()

            elif e.key() == Qt.Key_Right:
                self.moveRight()

            elif e.key() == Qt.Key_Left:
                self.moveLeft()

            elif e.key() == Qt.Key_Up:
                self.moveUp()

            elif e.key() == Qt.Key_Down:
                self.moveDown()
            else:
                super().keyPressEvent(e)
        else:
            super().keyPressEvent(e)

    # TODO: add into Command, undo and redo
    def cut(self):
        if not self.m_activateNode:
            print('警告: 没有激活节点！')
            self.messageShow.emit('警告: 没有激活节点！')
            return

        self.copy()
        self.removeNode()

    # 复制 subtree
    def copy(self):
        if not self.m_activateNode:
            print('警告: 没有激活节点！')
            self.messageShow.emit('警告: 没有激活节点！')
            return

        subTree = []

        for node in self.getSubTree(self.m_activateNode):
            subTreeNode = {}
            subTreeNode['htmlContent'] = node.toHtml()
            subTreeNode['pos'] = (node.x, node.y)
            son = []
            for sonNode in node.sonNode:
                son.append((sonNode.x, sonNode.y))
            subTreeNode['son'] = son

            subTree.append(subTreeNode)

        clipboard = QApplication.clipboard()
        clipboard.setText(str(subTree))

        self.messageShow.emit('提示：复制成功！')

    # 生成 subtree
    def genSubTree(self, nodeInfo, nodeList):
        if not nodeInfo['son']:
            return

        sorted(nodeInfo['son'], key=lambda a: a[1], reverse=True)
        self.m_activateNode.setHtml(nodeInfo['htmlContent'])
        sonInfo = []
        for pos in nodeInfo['son']:
            for nodeInfo in nodeList:
                if pos == nodeInfo['pos']:
                    sonInfo.append(nodeInfo)

        for info in sonInfo:
            self.addSonNode()
            self.m_activateNode.setHtml(info['htmlContent'])
            self.genSubTree(info, nodeList)
            self.setActivateNode(self.m_activateNode.parentNode)

    # 粘贴 subtree
    def paste(self):
        if not self.m_activateNode:
            print('警告: 没有激活节点！')
            self.messageShow.emit('警告: 没有激活节点！')
            return

        clipboard = QApplication.clipboard()

        if not clipboard.text():
            print('错误：剪贴板上没有文本内容！')
            self.messageShow.emit('错误：剪贴板上没有文本内容！')
            return

        nodeList = eval(clipboard.text())
        self.addSonNode()
        self.genSubTree(nodeList[0], nodeList)

        self.messageShow.emit('提示：粘贴成功！')

    # 修改节点背景颜色
    def nodeColor(self):
        if not self.m_activateNode:
            print('警告: 没有激活节点！')
            self.messageShow.emit('警告: 没有激活节点！')
            return

        dialog = QColorDialog()
        dialog.setWindowTitle('主题颜色')
        dialog.setCurrentColor(self.m_activateNode.m_color)
        if not dialog.exec():
            dialog.exec()

        m_context = Context()
        m_context.m_activateNode = self.m_activateNode
        m_context.m_color = dialog.selectedColor()
        m_context.m_scene = self

        nodeColorCommand = NodeColorCommand(m_context)
        self.m_undoStack.push(nodeColorCommand)

        self.messageShow.emit('更改主题颜色')

    # 修改节点中文本颜色
    def textColor(self):
        if not self.m_activateNode:
            print('警告: 没有激活节点！')
            self.messageShow.emit('警告: 没有激活节点！')
            return

        dialog = QColorDialog()
        dialog.setWindowTitle('文本颜色')
        dialog.setCurrentColor(self.m_activateNode.m_textColor)
        if not dialog.exec():
            return

        m_context = Context()
        m_context.m_activateNode = self.m_activateNode
        m_context.m_textColor = dialog.selectedColor()
        m_context.m_scene = self

        textColorCommand = TextColorCommand(m_context)
        self.m_undoStack.push(textColorCommand)

        self.messageShow.emit('提示：更改文本颜色！')

        # 修改节点中文本样式
    def textFont(self):
        if not self.m_activateNode:
            print('警告: 没有激活节点！')
            self.messageShow.emit('警告: 没有激活节点！')
            return

        dialog = QFontDialog()
        dialog.setWindowTitle('文本样式')
        dialog.setCurrentFont(self.m_activateNode.m_textFont)
        if not dialog.exec():
            return

        m_context = Context()
        m_context.m_activateNode = self.m_activateNode
        m_context.m_textFont = dialog.selectedFont()
        m_context.m_scene = self

        textFontCommand = TextFontCommand(m_context)
        self.m_undoStack.push(textFontCommand)

        self.messageShow.emit('提示：更改文本样式！')

    # rewrite rightclick menu
    # 重写scene右键菜单事件, 区分有无 item 的右键菜单事件
    def contextMenuEvent(self, e):
        selectedItem = self.itemAt(e.scenePos(), QTransform())
        print(selectedItem)

        if selectedItem and not self.m_editingMode:
            rightclick_menu = QMenu()

            # Cut
            cut_action = QAction('剪切', self)
            cut_action.setShortcut('Ctrl+X')
            cut_action.triggered.connect(self.cut)
            rightclick_menu.addAction(cut_action)

            # Copy
            copy_action = QAction('复制', self)
            copy_action.setShortcut('Ctrl+C')
            copy_action.triggered.connect(self.copy)
            rightclick_menu.addAction(copy_action)

            # Paste
            paste_action = QAction('粘贴', self)
            paste_action.setShortcut('Ctrl+V')
            paste_action.triggered.connect(self.paste)
            rightclick_menu.addAction(paste_action)

            # Delete
            delete_action = QAction('删除', self)
            delete_action.setShortcut('Delete')
            delete_action.triggered.connect(self.removeNode)
            rightclick_menu.addAction(delete_action)

            rightclick_menu.addSeparator()

            # Set Color
            set_color_action = QAction('主题颜色', self)
            set_color_action.triggered.connect(self.nodeColor)
            rightclick_menu.addAction(set_color_action)

            # Set Text Color
            set_textColor_action = QAction('文本颜色', self)
            set_textColor_action.triggered.connect(self.textColor)
            rightclick_menu.addAction(set_textColor_action)

            #设置文本样式
            set_font_action = QAction('文本样式', self)
            set_font_action.triggered.connect(self.textFont)
            rightclick_menu.addAction(set_font_action)

            rightclick_menu.exec(QCursor().pos())
        else:
            super().contextMenuEvent(e)

    # 添加自由主题和主题之间的关系
    def buildRelation(self):
        pass

    def node_(self, node, father):
        ET.SubElement(father,
                      'node', {
                          'x': str(node.x),
                          'y': str(node.y),
                          'son_num': str(len(node.sonNode)),
                          'width': str(node.width),
                          'm_color_red': str(node.m_color.red()),
                          'm_color_green': str(node.m_color.green()),
                          'm_color_blue': str(node.m_color.blue()),
                          'm_level': str(node.m_level),
                          'm_textColor_red': str(node.m_textColor.red()),
                          'm_textColor_green': str(node.m_textColor.green()),
                          'm_textColor_blue': str(node.m_textColor.blue()),
                          'm_note': node.m_note,
                          'm_link': node.m_link,
                          'htmlContent': node.toHtml()
                      })

    # 将 scene 中的信息写入文件中
    def writeContentToXmlFile(self, filename):
        # 最外层节点标签为'data',没有任何属性
        root = ET.Element('data')
        tree = self.getSubTree(self.NodeList[0])
        # 树中的所有节点在xml中均以'data'为根节点，为并列结构
        for v in tree:
            self.node_(v, root)
        whole_tree = ET.ElementTree(root)
        whole_tree.write(filename, encoding='utf-8')

    # 将 scene 中信息写入 PNG 图片
    def writeContentToPngFile(self, filename):
        img = QImage(self.sceneRect().width(), self.sceneRect().height(), QImage.Format_ARGB32_Premultiplied)

        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor(Qt.white))
        self.render(p)
        p.setBackground(QColor(Qt.white))
        p.end()

        img.save(filename)

    # 将 scene 中信息写入 PDF 文件
    def writeContentToPdfFile(self, filename):
        # 生成 Printer 对象
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        printer.setOrientation(QPrinter.Portrait)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)

        # 将 scene 中信息 render 到 painter上
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor(Qt.white))
        self.render(painter)
        painter.setBackground(QColor(Qt.white))
        painter.end()

    # 从 XML 文件中读取 scene 信息
    def readContentFromXmlFile(self, filename):
        tree = ET.ElementTree()
        try:
            tree.parse(filename)
        except:
            print('错误：树形分析错误！')
            return False
        root = tree.getroot()
        print('root: ', root)
        node_list = []
        attr_list = []
        for node_attr in root:
            node = self.nodeFactory()

            attr = node_attr.attrib
            print(attr)
            # 将xml中的数据存入节点中
            node.x = float(attr['x'])
            node.y = float(attr['y'])
            node.width = float(attr['width'])
            node.m_color = QColor(float(attr['m_color_red']),
                                  float(attr['m_color_green']),
                                  float(attr['m_color_blue']))
            node.m_level = int(attr['m_level'])
            node.m_textColor = QColor(float(attr['m_textColor_red']),
                                      float(attr['m_textColor_green']),
                                      float(attr['m_textColor_blue']))
            node.m_note = attr['m_note']
            node.m_link = attr['m_link']
            if node.m_link != 'https://':
                node.hasLink = True
            node.setHtml(attr['htmlContent'])

            node.setPos(node.x, node.y)
            self.addItem(node)
            self.NodeList.append(node)

            attr_list.append(attr)
            node_list.append(node)

        # 由于写xml文件中节点是根据深度优先遍历的结果进行排序的
        # xml中的第一个节点一定是根节点
        node_scan_head = 1
        for m in range(len(node_list)):
            node_scan_tail = node_scan_head + int(attr_list[m]['son_num'])
            for n in range(node_scan_head, node_scan_tail):
                node_list[m].sonNode.append(node_list[n])
                node_list[n].parentNode = node_list[m]
                self.addBranch(node_list[m], node_list[n])
            node_scan_head = node_scan_tail

        return True

    # 删除 scene 中所有 node
    def removeAllNodes(self):
        for node in self.NodeList:
            self.removeItem(node)

        self.NodeList.clear()

    # 删除 scene 中所有 branch
    def removeAllBranches(self):
        for branch in self.BranchList:
            self.removeItem(branch)

        self.BranchList.clear()

    # 插入图片并且调整节点位置
    def insertPicture(self, image):
        if not self.m_activateNode:
            print('警告: 没有激活节点！')
            self.messageShow.emit('警告: 没有激活节点！')
            return
        self.m_activateNode.insertPicture(image)
        self.contentChanged.emit()
        self.adjustSubTreeNode()
        self.adjustBranch()

    def mousePressEvent(self, e):
        self.press_close.emit()
        super().mousePressEvent(e)