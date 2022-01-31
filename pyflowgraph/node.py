
#
# Copyright 2015-2017 Eric Thivierge
#

import math
import json

from PySide2.QtCore import QPointF
from qtpy import QtGui, QtWidgets, QtCore
from .port import InputPort, OutputPort, GlandPort
from .port import BasePort

class NodeTitle(QtWidgets.QGraphicsWidget):

    __color = QtGui.QColor(25, 25, 25)
    __font = QtGui.QFont('Decorative', 12)
    __font.setLetterSpacing(QtGui.QFont.PercentageSpacing, 115)
    __labelBottomSpacing = 12

    def __init__(self, text, parent=None):
        super(NodeTitle, self).__init__(parent)

        #self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)

        self.__textItem = QtWidgets.QGraphicsTextItem(text, self)
        self.__textItem.setDefaultTextColor(self.__color)
        self.__textItem.setFont(self.__font)
        self.__textItem.setPos(QPointF(0, -2))
        option = self.__textItem.document().defaultTextOption()
        option.setWrapMode(QtGui.QTextOption.NoWrap)
        self.__textItem.document().setDefaultTextOption(option)
        self.__textItem.adjustSize()

        self.setPreferredSize(self.textSize())



    def setText(self, text):
        self.__textItem.setPlainText(text)
        self.__textItem.adjustSize()
        self.setPreferredSize(self.textSize())

    def textSize(self):
        return QtCore.QSizeF(
            self.__textItem.textWidth(),
            self.__font.pointSizeF() + self.__labelBottomSpacing
            )

    # def paint(self, painter, option, widget):
    #     super(NodeTitle, self).paint(painter, option, widget)
    #     painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 0)))
    #     painter.drawRect(self.windowFrameRect())


class NodeHeader(QtWidgets.QGraphicsWidget):

    def __init__(self, text, parent=None):
        super(NodeHeader, self).__init__(parent)

        #self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)

        layout = QtWidgets.QGraphicsLinearLayout(QtCore.Qt.Vertical, self)   #QtWidgets.QGraphicsLayoutItem.parentLayoutItem(parent))

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        layout.setOrientation(QtCore.Qt.Vertical)
        #self.setLayout(layout)

        #layout = QtWidgets.QGraphicsSimpleTextItem(NodeTitle(text, self))
        #layout.setX(0)
        #layout.setY(-100)
        self._titleWidget = NodeTitle(text, self)

        layout.addItem(self._titleWidget)
        layout.setAlignment(self._titleWidget, QtCore.Qt.AlignCenter)   # | QtCore.Qt.AlignTop)

        self.setLayout(layout)
        #self.adjustSize()


    def setText(self, text):
        self._titleWidget.setText(text)


    # def paint(self, painter, option, widget):
    #     super(NodeHeader, self).paint(painter, option, widget)
    #     painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 100)))
    #     painter.drawRect(self.windowFrameRect())


class PortList(QtWidgets.QGraphicsWidget):
    def __init__(self, parent):
        super(PortList, self).__init__(parent)
        layout = QtWidgets.QGraphicsLinearLayout(None, None)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        layout.setOrientation(QtCore.Qt.Vertical)
        self.setLayout(layout)
        #self.__maxX = 20
        #self.__maxY = 20


    def addPort(self, port, alignment, x=0, y=0):
        layout = self.layout()
        print("addPort : ", x, y)
        layout.addItem(port.setPos(x, y))
        layout.setAlignment(port, alignment)
        #self.adjustSize()
        port.__x = x
        port.__y = y

        return port

    # def paint(self, painter, option, widget):
    #     super(PortList, self).paint(painter, option, widget)
    #     painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 0)))
    #     painter.drawRect(self.windowFrameRect())

class Node(QtWidgets.QGraphicsWidget):

    nameChanged = QtCore.Signal(str, str)

    __defaultColor = QtGui.QColor(154, 205, 50, 255)
    __unselectedColor = QtGui.QColor(25, 25, 25)
    __selectedColor = QtGui.QColor(255, 0, 0, 255)

    __unselectedPen = QtGui.QPen(__unselectedColor, 1.6)
    __selectedPen = QtGui.QPen(__selectedColor, 3.6)
    __linePen = QtGui.QPen(QtGui.QColor(25, 25, 25, 255), 1.25)

    def __init__(self, graph, name, xSize=80, ySize=20):
        super(Node, self).__init__(None)

        self.__name = name
        self.__graph = graph
        self.__color = self.__defaultColor

        self.setMinimumWidth(xSize)
        self.setMinimumHeight(ySize)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #self.setSizePolicy(QtWidgets.QSizePolicy(QtWidget


        layout = QtWidgets.QGraphicsLinearLayout(None, None)
        layout.setContentsMargins(5, 0, 5, 7)
        layout.setSpacing(7)
        layout.setOrientation(QtCore.Qt.Vertical)
        #self.setLayout(layout)


        self.__headerItem = NodeHeader(self.__name, self)
        layout.addItem(self.__headerItem)
        layout.setAlignment(self.__headerItem, QtCore.Qt.AlignTop)    #QtCore.Qt.AlignCenter |

        self.__ports = []
        self.__inputPortsHolder = PortList(self)
        self.__ioPortsHolder = PortList(self)
        self.__outputPortsHolder = PortList(self)

        layout.addItem(self.__inputPortsHolder)
        layout.addItem(self.__ioPortsHolder)
        layout.addItem(self.__outputPortsHolder)

        self.setWindowFlags(QtCore.Qt.SubWindow)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #self.setWindowFlags(QtCore.Qt.SubWindow)
        #self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        p = GlandPort(self, self.__graph, "Gland", self.__defaultColor, "Gland", -200, -20)
        self.addPort(p, -150, 20)
        self.nextInPort = 40



        p = GlandPort(self, self.__graph, "Gland", self.__defaultColor, "Gland", 200, -20)
        self.addPort(p,xSize + 150, 20)
        self.nextOutPort = 40

        self.__selected = False
        self.__dragging = False

        #self.adjustSize()

    # =====
    # Name
    # =====

    def getNode(self, name):
        for n in self.__graph.__nodes:
            if n.__name == name:
                return n

    def setWidth(self, width):
        self.setMinimumWidth(width)
        self.setMaximumWidth(width)

    def setHeight(self, height):
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)

    def getWidth(self):
        return self.minimumWidth()

    def getName(self):
        return self.__name

    def setName(self, name):
        if name != self.__name:
            origName = self.__name
            self.__name = name
            self.__headerItem.setText(self.__name)

            # Emit an event, so that the graph can update itsself.
            self.nameChanged.emit(origName, name)

            # Update the node so that the size is computed.
            #self.adjustSize()

    # =======
    # Colors
    # =======
    def getColor(self):
        return self.__color

    def setColor(self, color):
        self.__color = color
        self.update()


    def getUnselectedColor(self):
        return self.__unselectedColor

    def setUnselectedColor(self, color):
        self.__unselectedColor = color
        self.__unselectedPen.setColor(self.__unselectedColor)
        self.update()


    def getSelectedColor(self):
        return self.__selectedColor

    def setSelectedColor(self, color):
        self.__selectedColor = color
        self.__selectedPen.setColor(self.__selectedColor)
        self.update()

    # =============
    # Misc Methods
    # =============
    def getGraph(self):
        return self.__graph


    def getHeader(self):
        return self.__headerItem


    # ==========
    # Selection
    # ==========
    def isSelected(self):
        return self.__selected

    def setSelected(self, selected=True):
        self.setZValue(10.0 if selected else 0.0)
        self.__selected = selected
        self.update()


    #########################
    ## Graph Pos

    def getGraphPos(self):
        transform = self.transform()
        size = self.size()
        return QtCore.QPointF(transform.dx()+(size.width()*0.5), transform.dy()+(size.height()*0.5))


    def setGraphPos(self, graphPos):
        self.prepareConnectionGeometryChange()
        size = self.size()
        self.setTransform(QtGui.QTransform.fromTranslate(graphPos.x()-(size.width()*0.5), graphPos.y()-(size.height()*0.5)), False)


    def translate(self, x, y):
        self.prepareConnectionGeometryChange()
        super(Node, self).moveBy(x, y)


    # Prior to moving the node, we need to tell the connections to prepare for a geometry change.
    # This method must be called preior to moving a node.
    def prepareConnectionGeometryChange(self):
        for port in self.__ports:
            if port.inCircle():
                for connection in port.inCircle().getConnections():
                    connection.prepareGeometryChange()
            if port.outCircle():
                for connection in port.outCircle().getConnections():
                    connection.prepareGeometryChange()

    #########################
    ## Ports

    def addPort(self, port, x, y):
        if isinstance(port, InputPort):
            self.__inputPortsHolder.addPort(port, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter, x, y)
        elif isinstance(port, OutputPort):
            self.__outputPortsHolder.addPort(port, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter, x, y)
        else:
            self.__ioPortsHolder.addPort(port, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter, x, y)
        port.__x = x
        port.__y = y
        self.__ports.append(port)
        self.adjustSize()
        return port


    def getPort(self, name):
        for port in self.__ports:
            print("getPort : name : port ", name, port.getName())
            if port.getName() == name:
                return port
        return None


    def paint(self, painter, option, widget):
        rect = self.windowFrameRect()
        painter.setBrush(self.__color)

        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 0), 0))

        roundingY = 10
        roundingX = 10

        painter.drawRoundedRect(rect, roundingX, roundingY)

        # Title BG
        titleHeight = self.__headerItem.size().height() - 3

        painter.setBrush(self.__color.darker(125))
        roundingY = rect.width() * roundingX / titleHeight
        painter.drawRoundedRect(0, 0, rect.width(), titleHeight, roundingX, roundingY, QtCore.Qt.AbsoluteSize)
        painter.drawRect(0, titleHeight * 0.5 + 2, rect.width(), titleHeight * 0.5)

        painter.setBrush(QtGui.QColor(0, 0, 0, 0))
        if self.__selected:
            painter.setPen(self.__selectedPen)
        else:
            painter.setPen(self.__unselectedPen)

        roundingY = 10
        roundingX = 10

        painter.drawRoundedRect(rect, roundingX, roundingY, QtCore.Qt.AbsoluteSize)


    #########################
    ## Events

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:

            modifiers = event.modifiers()
            if modifiers == QtCore.Qt.ControlModifier:
                if not self.isSelected():
                    self.__graph.selectNode(self, clearSelection=False)
                else:
                    self.__graph.deselectNode(self)

            elif modifiers == QtCore.Qt.ShiftModifier:
                if not self.isSelected():
                    self.__graph.selectNode(self, clearSelection=False)
            else:
                if not self.isSelected():
                    self.__graph.selectNode(self, clearSelection=True)

                self.__dragging = True
                self._mouseDownPoint = self.mapToScene(event.pos())
                self._mouseDelta = self._mouseDownPoint - self.getGraphPos()
                self._lastDragPoint = self._mouseDownPoint
                self._nodesMoved = False

        else:
            super(Node, self).mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if self.__dragging:
            newPos = self.mapToScene(event.pos())

            graph = self.getGraph()
            if graph.getSnapToGrid() is True:
                gridSize = graph.getGridSize()

                newNodePos = newPos - self._mouseDelta

                snapPosX = math.floor(newNodePos.x() / gridSize) * gridSize;
                snapPosY = math.floor(newNodePos.y() / gridSize) * gridSize;
                snapPos = QtCore.QPointF(snapPosX, snapPosY)

                newPosOffset = snapPos - newNodePos

                newPos = newPos + newPosOffset

            delta = newPos - self._lastDragPoint
            self.__graph.moveSelectedNodes(delta)
            self._lastDragPoint = newPos
            self._nodesMoved = True
        else:
            super(Node, self).mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        if self.__dragging:
            if self._nodesMoved:

                newPos = self.mapToScene(event.pos())

                delta = newPos - self._mouseDownPoint
                self.__graph.endMoveSelectedNodes(delta)

            self.setCursor(QtCore.Qt.ArrowCursor)
            self.__dragging = False
        else:
            super(Node, self).mouseReleaseEvent(event)


    #########################
    ## shut down

    def disconnectAllPorts(self):
        # gather all the connections into a list, and then remove them from the graph.
        # This is because we can't remove connections from ports while
        # iterating over the set.
        connections = []

        for port in self.__ports:
            if port.inCircle():
                for connection in port.inCircle().getConnections():
                    connections.append(connection)
            if port.outCircle():
                for connection in port.outCircle().getConnections():
                    connections.append(connection)

        for connection in connections:
            self.__graph.removeConnection(connection)
