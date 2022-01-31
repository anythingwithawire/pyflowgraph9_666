#
# Copyright 2015-2017 Eric Thivierge
#
import sys
from random import random

from PySide2.QtCore import Qt, QByteArray, QDataStream, QIODevice, QMimeData, QRect, QRectF
# from PySide2.Qt import QString
from PySide2.QtGui import QKeySequence, QFont

from PySide2.QtWidgets import QMainWindow, QApplication, QLineEdit, QTableWidget, QTableWidgetItem, QAbstractItemView, \
    QMenu
from qtpy import QtGui, QtWidgets, QtCore

from pyflowgraph.connection import Connection
from pyflowgraph.graph_view_widget import GraphViewWidget
from pyflowgraph.graph_view import GraphView
from pyflowgraph.graph_view_widget import GraphViewWidget
from pyflowgraph.node import Node
from pyflowgraph.port import InputPort, OutputPort, IOPort
# Add the pyflowgraph module to the current environment if it does not already exist

import os, sys



class H3TableHandler:
    def __init__(self, parent=None):
        self.parent = parent
    def right_click(self):
        # bar = self.parent.menuBar()
        top_menu = QMenu(self.parent)

        menu = top_menu.addMenu("Menu")
        config = menu.addMenu("Configuration ...")

        _load = config.addAction("&Load ...")
        _save = config.addAction("&Save ...")

        config.addSeparator()

        config1 = config.addAction("Config1")
        config2 = config.addAction("Config2")
        config3 = config.addAction("Config3")

        action = menu.exec_(QtGui.QCursor.pos())

        if action == _load:
            # do this
            pass
        elif action == _save:
            # do this
            pass
        elif action == config1:
            # do this
            pass
        elif action == config2:
            # do this
            pass
        elif action == config3:
            # do this
            pass


import pyperclip

class TableWidgetCustom(QTableWidget, QTableWidgetItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clipboard = QApplication.clipboard()
        self.mime_data = self.clipboard.mimeData()
        self.pc = pyperclip
        self.text_clip = ""

        self.__node_counter = 0

        self.setWindowTitle("FlowGraph Main")
        self.setGeometry(2000, 0, 200, 200)

        #min graph window here



    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Save):
            self.save()
        if event.matches(QKeySequence.Open):
            self.restore()
        if event.matches(QKeySequence.Delete):
            self.delete()
        if event.matches(QKeySequence.Copy):
            self.copy()
        if event.matches(QKeySequence.Paste):
            self.paste()
        QTableWidget.keyPressEvent(self, event)

    def delete(self):
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item.isSelected():
                    item = QTableWidgetItem()
                    item.setText(str(""))
                    self.setItem(row, col, item)


    def copy(self):
        #self.clipboard.clear(mode=self.clipboard.Clipboard)
        clip = ""
        i=0
        print(self.rowCount(), self.columnCount())
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item.isSelected():
                    i = i + 1
                    item = QTableWidgetItem()
                    item = self.item(row, col)
                    clip = clip + str(item.text())+str(",")
            clip = clip + str("\n")
        encoded_clip = clip.encode()
        self.text_clip = clip
        clip_bytearray = bytearray(encoded_clip)
        #self.mime_data.setData("xls", clip_bytearray)
        #self.clipboard.setMimeData(self.mime_data)
        self.pc.init_qt_clipboard()
        self.pc.set_clipboard("qt")
        self.pc.lazy_load_stub_copy(clip)
        print("selected ", i, "\n", clip)

    def paste(self):
        #self.clipboard.clear(mode=self.clipboard.Clipboard)
        clip = ""
        i = 0
        print(self.rowCount(), self.columnCount())
        l = self.text_clip.split(",")
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item.isSelected():
                    item = QTableWidgetItem()
                    item = self.item(row, col)
                    item.setText(l[i].strip())
                    self.setItem(row, col, item)
                    i = i + 1
                    if i >= len(l)-1:
                        i=0

    def save(self):
        print("saving")
        # using findChildren is for simplicity, it's probably better to create
        # your own list of widgets to cycle through
        f = open(str(self.windowTitle())+"_data", "wt")
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    txt = item.text()
                else:
                    txt = 'x'
                f.write(txt)
                f.write(",")
            f.write("\n")
        f.close()

    def restore(self):
        print("restore")
        f = open(str(self.windowTitle())+"_data", "rt")
        i = 0
        for row in range(self.rowCount()):
            l = f.readline()
            d = l.split(",")
            for col in range(self.columnCount()):
                item = QTableWidgetItem()
                if col >= len(d):
                    item.setText("")
                else:
                    item.setText(str(d[col]))
                i = i + 1
                self.setItem(row, col, item)
                item.setTextAlignment(Qt.AlignHCenter)

        f.close()

    def h3_table_right_click(self, position):
        o_h3_table = H3TableHandler(parent=self)
        o_h3_table.right_click()


class MainWindow(QMainWindow, TableWidgetCustom):
    def __init__(self, e=None):
        super().__init__()

        pb1 = QtWidgets.QPushButton('Set Node IP\nFrom Cable', self)
        pb1.resize(90, 32)
        pb1.move(50, 50)
        pb1.clicked.connect(self.pb1_clicked)

        pb2 = QtWidgets.QPushButton('Set Node OP\nFrom Cable', self)
        pb2.resize(90, 32)
        pb2.move(150, 50)
        pb2.clicked.connect(self.pb2_clicked)

        pb3 = QtWidgets.QPushButton('Zoom In', self)
        pb3.resize(90, 32)
        pb3.move(50, 100)
        pb3.clicked.connect(self.pb3_clicked)

        pb4 = QtWidgets.QPushButton('Zoom Out', self)
        pb4.resize(90, 32)
        pb4.move(150, 100)
        pb4.clicked.connect(self.pb4_clicked)

        pb5 = QtWidgets.QPushButton('Node Make', self)
        pb5.resize(90, 32)
        pb5.move(50, 150)
        pb5.clicked.connect(self.pb5_clicked)

        pb6 = QtWidgets.QPushButton('Node Trunk', self)
        pb6.resize(90, 32)
        pb6.move(150, 150)
        pb6.clicked.connect(self.pb6_clicked)

        self.pc = pyperclip

        self.cableInfoWidget = TableWidgetCustom()
        # self.cableInfoWidget.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.cableInfoWidget.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.cableInfoWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.cableInfoWidget.setColumnCount(6)
        self.cableInfoWidget.setRowCount(20)
        self.cableInfoWidget.setGeometry(1000, 0, 400, 600)
        """
            for row in range(self.cableInfoWidget.rowCount()):
            d = ""
            for col in range(self.cableInfoWidget.columnCount()):
                item = QTableWidgetItem(row, col)
                item.setText(d)
                item.setTextAlignment(Qt.AlignHCenter)
        """
        self.cableInfoWidget.setWindowTitle("Cable Termination Map")
        self.cableInfoWidget.setHorizontalHeaderLabels((("FmTermName;FmCoreNum;Cable;ToCoreNum;ToTermName").split(";")))

        self.cableInfoWidget.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.cableInfoWidget.show()
        self.cableInfoWidget.restore()

        self.nodeInfoWidget = TableWidgetCustom()
        # self.nodeInfoWidget.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.nodeInfoWidget.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.nodeInfoWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.nodeInfoWidget.setColumnCount(12)
        self.nodeInfoWidget.setRowCount(20)
        self.nodeInfoWidget.setGeometry(500, 0, 400, 600)
        """
            for row in range(self.nodeInfoWidget.rowCount()):
            d = ""
            for col in range(self.nodeInfoWidget.columnCount()):
                item = QTableWidgetItem(row, col)
                item.setText(d)
                item.setTextAlignment(Qt.AlignHCenter)
        """
        self.nodeInfoWidget.setWindowTitle("Node Termination Map")
        self.nodeInfoWidget.setHorizontalHeaderLabels((("x;y;TermName;TermNum;SeqNum;Node;SeqNum;TermNum;TermName;x;y").split(";")))
        self.nodeInfoWidget.restore()

        # self.restore()
        # self.nodeInfoWidget.cellClicked.connect(self.save)
        self.nodeInfoWidget.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.nodeInfoWidget.show()

        widget = GraphViewWidget()
        graph = GraphView(parent=widget)


        node1 = Node(graph, 'Short1', xSize=200, ySize=200)
        node1.addPort(InputPort(node1, graph, 'InPort1', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=0, y=20)
        node1.addPort(InputPort(node1, graph, 'InPort2', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=0, y=40)
        node1.addPort(InputPort(node1, graph, 'InPort3', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=0, y=60)
        node1.addPort(InputPort(node1, graph, 'InPort4', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=0, y=80)

        node1.addPort(OutputPort(node1, graph, 'OutPort1', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=85, y=20)
        node1.addPort(OutputPort(node1, graph, 'OutPort2', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=85, y=40)
        node1.addPort(OutputPort(node1, graph, 'OutPort3', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=85, y=60)
        node1.addPort(OutputPort(node1, graph, 'OutPort4', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=85, y=80)
        node1.setPos(-400,0)
        graph.addNode(node1)


        node1 = Node(graph, 'Short2', xSize=200, ySize=200)
        node1.addPort(InputPort(node1, graph, 'InPort1', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=0, y=20)
        node1.addPort(InputPort(node1, graph, 'InPort2', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=0, y=40)
        node1.addPort(InputPort(node1, graph, 'InPort3', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=0, y=60)
        node1.addPort(InputPort(node1, graph, 'InPort4', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=0, y=80)

        node1.addPort(OutputPort(node1, graph, 'OutPort1', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=85, y=20)
        node1.addPort(OutputPort(node1, graph, 'OutPort2', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=85, y=40)
        node1.addPort(OutputPort(node1, graph, 'OutPort3', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=85, y=60)
        node1.addPort(OutputPort(node1, graph, 'OutPort4', QtGui.QColor(128, 170, 170, 255), dataType='Terminals'), x=85, y=80)
        node1.setPos(400, 0)
        graph.addNode(node1)


        #node1.addPort(InputPort(node1, graph, 'InPort2', QtGui.QColor(128, 170, 170, 255), 'MyDataX', 0,40))


        #node1.addPort(OutputPort(node1, graph, 'OutPort', QtGui.QColor(32, 255, 32, 255), 'MyDataY',0,60))
        #node1.addPort(IOPort(node1, graph, 'IOPort1', QtGui.QColor(32, 255, 32, 255), 'MyDataY',0,80))
        #node1.addPort(IOPort(node1, graph, 'IOPort2', QtGui.QColor(32, 255, 32, 255), 'MyDataY', 0,100))
        #node1.setGraphPos(QtCore.QPointF(-100, 0))



        '''node2 = Node(graph, 'ReallyLongLabel')
        node2.addPort(InputPort(node2, graph, 'InPort1', QtGui.QColor(128, 170, 170, 255), 'MyDataY'), 0,20)
        node2.addPort(InputPort(node2, graph, 'InPort2', QtGui.QColor(128, 170, 170, 255), 'MyDataX'), 0, 40)
        node2.addPort(OutputPort(node2, graph, 'OutPort', QtGui.QColor(32, 255, 32, 255), 'MyDataY'), 0 , 60)
        node2.addPort(IOPort(node2, graph, 'IOPort1', QtGui.QColor(32, 255, 32, 255), 'MyDataY'), 0 , 80)
        node2.addPort(IOPort(node2, graph, 'IOPort2', QtGui.QColor(32, 255, 32, 255), 'MyDataY'), 0 ,100)
        node2.setGraphPos(QtCore.QPointF(100, 0))

        graph.addNode(node2)
        graph.connectPorts(node1, 'OutPort', node2, 'InPort1')'''


        widget.setGraphView(graph)
        widget.setGeometry(QRect(100,100,1500,1000))
        widget.show()


    def pb1_clicked(self):
        pass

    def pb2_clicked(self):
        pass

    def pb3_clicked(self):
        self.graph.scale(1.5, 1.5)

    def pb4_clicked(self):
        self.graph.scale(0.5, 0.5)

    def pb5_clicked(self):
        pass

    def pb6_clicked(self):
        pass




if __name__ == "__main__":
    app = QApplication(sys.argv)

    w = MainWindow()
    w.resize(500, 500)
    w.setWindowTitle("FlowGraph")
    w.show()
    sys.exit(app.exec_())
