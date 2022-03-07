
#
# Copyright 2015-2017 Eric Thivierge
#

import json

from PySide2.QtCore import QPointF, QPoint, Qt
from PySide2.QtWidgets import QMenu
from qtpy import QtGui, QtWidgets, QtCore


class PortLabel(QtWidgets.QGraphicsWidget):
    __font = QtGui.QFont('Decorative', 12)
    __smallFont = QtGui.QFont('Decorative', 8)
    __fontMetrics = QtGui.QFontMetrics(__font)

    def __init__(self, port, text, hOffset, color, highlightColor):
        super(PortLabel, self).__init__(port)
        self.__port = port
        self.__text = text
        self.__textItem = QtWidgets.QGraphicsTextItem(text, self)
        self._labelColor = color
        self.__highlightColor = highlightColor
        self.__textItem.setDefaultTextColor(self._labelColor)
        self.__textItem.setFont(self.__font)
        self.__textItem.transform().translate(0, self.__font.pointSizeF() * -0.5)
        option = self.__textItem.document().defaultTextOption()
        option.setWrapMode(QtGui.QTextOption.NoWrap)
        self.__textItem.document().setDefaultTextOption(option)
        self.__textItem.document().setDocumentMargin(0)
        self.__textItem.adjustSize()

        self.setPreferredSize(self.textSize())
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.setWindowFrameMargins(0, 0, 0, 0)
        self.setHOffset(hOffset)

        self.setAcceptHoverEvents(True)
        self.__mouseDownPos = None

    def text(self):
        return self.__text


    def setHOffset(self, hOffset):
        self.transform().translate(hOffset, 0)


    def setColor(self, color):
        self.__textItem.setDefaultTextColor(color)
        self.update()


    def textSize(self):
        return QtCore.QSizeF(
            self.__fontMetrics.width(self.__text),
            self.__fontMetrics.height()
            )


    def getPort(self):
        return self.__port


    def highlight(self):
        self.setColor(self.__highlightColor)


    def unhighlight(self):
        self.setColor(self._labelColor)


    def hoverEnterEvent(self, event):
        self.highlight()
        super(PortLabel, self).hoverEnterEvent(event)


    def hoverLeaveEvent(self, event):
        self.unhighlight()
        super(PortLabel, self).hoverLeaveEvent(event)


    def mousePressEvent(self, event):
        print("port press")
        self.__mousDownPos = self.mapToScene(event.pos())


    def mouseMoveEvent(self, event):
        self.unhighlight()
        scenePos = self.mapToScene(event.pos())

        # When clicking on an UI port label, it is ambigous which connection point should be activated.
        # We let the user drag the mouse in either direction to select the conneciton point to activate.
        delta = scenePos - self.__mousDownPos
        if delta.x() < 0:
            if self.__port.inCircle() is not None:
                self.__port.inCircle().mousePressEvent(event)
        else:
            if self.__port.outCircle() is not None:
                self.__port.outCircle().mousePressEvent(event)

    # def paint(self, painter, option, widget):
    #     super(PortLabel, self).paint(painter, option, widget)
    #     painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 255)))
    #     painter.drawRect(self.windowFrameRect())


class PortCircle(QtWidgets.QGraphicsWidget):

    __radius = 6                         #was 4.5
    __diameter = 2 * __radius              #was 2

    def __init__(self, port, graph, hOffset, color, connectionPointType):
        super(PortCircle, self).__init__(port)

        self.__port = port
        self._graph = graph
        self._connectionPointType = connectionPointType
        self.__connections = set()
        self._supportsOnlySingleConnections = False #connectionPointType == 'In'

        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        size = QtCore.QSizeF(self.__diameter, self.__diameter)
        self.setPreferredSize(size)
        self.setWindowFrameMargins(0, 0, 0, 0)

        self.transform().translate(self.__radius * hOffset, 0)

        self.__defaultPen = QtGui.QPen(QtGui.QColor(25, 25, 25), 1.0)
        self.__hoverPen = QtGui.QPen(QtGui.QColor(255, 255, 100), 1.5)
        self.__movePen = QtGui.QPen(QtGui.QColor(255, 0, 0), 1.5)

        self._ellipseItem = QtWidgets.QGraphicsRectItem(self)
        self._ellipseItem.setPen(self.__defaultPen)
        self._ellipseItem.setPos(size.width()/2 - self.__radius/4 + 1, size.height()/2)
        self._ellipseItem.setRect(
            -self.__radius,
            -self.__radius,
            self.__diameter,
            self.__diameter,
            )
        #if connectionPointType == 'In':
        #    self._ellipseItem.setStartAngle(270 * 16)
        #    self._ellipseItem.setSpanAngle(180 * 16)

        self.setColor(color)
        self.setAcceptHoverEvents(True)
        self.mousePos = QPointF(0,0)
        self.portMove = None

    def getPort(self):
        return self.__port


    def getColor(self):
        return self.getPort().getColor()


    def centerInSceneCoords(self):
        return self._ellipseItem.mapToScene(0, 0)


    def setColor(self, color):
        self._color = color
        self._ellipseItem.setBrush(QtGui.QBrush(self._color))


    def setDefaultPen(self, pen):
        self.__defaultPen = pen
        self._ellipseItem.setPen(self.__defaultPen)


    def setHoverPen(self, pen):
        self.__hoverPen = pen


    def highlight(self):
        self._ellipseItem.setBrush(QtGui.QBrush(self._color.lighter()))
        # make the port bigger to highlight it can accept the connection.
        self._ellipseItem.setRect(
            -self.__radius * 1.3,
            -self.__radius * 1.3,
            self.__diameter * 1.3,
            self.__diameter * 1.3,
            )

    def highlight2(self):
        self._ellipseItem.setBrush(QtGui.QBrush(QtGui.QColor(255,0,0)))
        # make the port bigger to highlight it can accept the connection.
        self._ellipseItem.setRect(
            -self.__radius * 1.3,
            -self.__radius * 1.3,
            self.__diameter * 1.3,
            self.__diameter * 1.3,
            )
    def unhighlight(self):
        self._ellipseItem.setBrush(QtGui.QBrush(self._color))
        self._ellipseItem.setRect(
            -self.__radius,
            -self.__radius,
            self.__diameter,
            self.__diameter,
            )


    # ===================
    # Connection Methods
    # ===================
    def connectionPointType(self):
        return self._connectionPointType

    def isInConnectionPoint(self):
        return self._connectionPointType == 'In'

    def isOutConnectionPoint(self):
        return self._connectionPointType == 'Out'

    def isGlandConnectionPoint(self):
        return self._connectionPointType == 'Gland'

    def supportsOnlySingleConnections(self):
        return self._supportsOnlySingleConnections

    def setSupportsOnlySingleConnections(self, value):
        self._supportsOnlySingleConnections = value

    def canConnectTo(self, otherPortCircle):

        if self.connectionPointType() == otherPortCircle.connectionPointType():
            return False

        if self.getPort().getDataType() != otherPortCircle.getPort().getDataType():
            return False

        # Check if you're trying to connect to a port on the same node.
        # TODO: Do propper cycle checking..
        otherPort = otherPortCircle.getPort()
        port = self.getPort()
        if otherPort.getNode() == port.getNode():
            return False

        return True

    def addConnection(self, connection):
        """Adds a connection to the list.
        Arguments:
        connection -- connection, new connection to add.
        Return:
        True if successful.
        """

        if self._supportsOnlySingleConnections and len(self.__connections) != 0:
            # gather all the connections into a list, and then remove them from the graph.
            # This is because we can't remove connections from ports while
            # iterating over the set.
            connections = []
            for c in self.__connections:
                connections.append(c)
            for c in connections:
                self._graph.removeConnection(c)

        self.__connections.add(connection)

        return True

    def removeConnection(self, connection):
        """Removes a connection to the list.
        Arguments:
        connection -- connection, connection to remove.
        Return:
        True if successful.
        """

        self.__connections.remove(connection)

        return True

    def getConnections(self):
        """Gets the ports connections list.
        Return:
        List, connections to this port.
        """

        return self.__connections

    # ======
    # Events
    # ======
    def hoverEnterEvent(self, event):
        self.highlight()
        if self.portMove:
            self.highlight2()
        super(PortCircle, self).hoverEnterEvent(event)


    def hoverLeaveEvent(self, event):
        if not self.portMove:
            self.unhighlight()
        super(PortCircle, self).hoverLeaveEvent(event)

    #########################
    ## Context Menu
    def contextMenuEvent2(self, event):
        contextMenu2 = QMenu()
        listConn = contextMenu2.addAction("List Connections")
        movePort = contextMenu2.addAction("Move Port")
        hidePort = contextMenu2.addAction("Hide Port")
        # loadAct = contextMenu.addAction("Load")
        # nodeAct = contextMenu.addAction("New Node")
        p1 = event.screenPos()
        ps = QPoint(p1.x(), p1.y())
        action = contextMenu2.exec_(ps)
        if action == listConn:
            print("===Connections===")
            for c in self.__connections:
                nodeFrom = c._Connection__srcPortCircle._PortCircle__port._node.getName()
                nodeTo = c._Connection__dstPortCircle._PortCircle__port._node.getName()
                termFrom = c._Connection__srcPortCircle._PortCircle__port._name
                termTo = c._Connection__dstPortCircle._PortCircle__port._name
                if c._Connection__srcPortCircle is self or c._Connection__dstPortCircle is self:
                    print(nodeFrom, termFrom, nodeTo, termTo)
            print("=================")

        if action == movePort:
            #self.setSelected(True)
            self.portMove = self
            self.highlight2()

        if action == hidePort:
            self.setVisible(False)

    def mousePressEvent(self, event):

        if event.button() == QtCore.Qt.LeftButton:

            if self.portMove is not None:
                pass
                #self.setPos(QPointF(self.mousePos))
            else:
                self.unhighlight()

                scenePos = self.mapToScene(event.pos())

                from .mouse_grabber import MouseGrabber
                if self.isInConnectionPoint():
                    MouseGrabber(self._graph, scenePos, self, 'Out')
                elif self.isOutConnectionPoint():
                    MouseGrabber(self._graph, scenePos, self, 'In')
                elif self.isGlandConnectionPoint():
                    MouseGrabber(self._graph, scenePos, self, 'Gland')

        if event.button() == QtCore.Qt.RightButton:
            self.contextMenuEvent2(event)

    #super(PortCircle, self).mousePressEvent(event)
    # def paint(self, painter, option, widget):
    #     super(PortCircle, self).paint(painter, option, widget)
    #     painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 0)))
    #     painter.drawRect(self.windowFrameRect())

    def mouseMoveEvent(self, event):
        self.mousePos = self.mapToItem(self.parentItem(), event.pos())
        if self.portMove is not None:
            self.highlight2()
            self.setPos(QPointF(self.mousePos))



    def mouseReleaseEvent(self,event):
        if self.portMove:
            self.portMove.unhighlight()
            self.portMove = None
            #self.portMove.setSelected(False)

class ItemHolder(QtWidgets.QGraphicsWidget):
    """docstring for ItemHolder"""
    def __init__(self, parent):
        super(ItemHolder, self).__init__(parent)

        layout = QtWidgets.QGraphicsLinearLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def setItem(self, item):
        item.setParentItem(self)
        self.layout().addItem(item)

    # def paint(self, painter, option, widget):
    #     super(ItemHolder, self).paint(painter, option, widget)
    #     painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 0)))
    #     painter.drawRect(self.windowFrameRect())



class BasePort(QtWidgets.QGraphicsWidget):

    _labelColor = QtGui.QColor(25, 25, 25)
    _labelHighlightColor = QtGui.QColor(225, 225, 225, 255)

    def __init__(self, parent, graph, name, color, dataType, connectionPointType, x=0, y=0):
        super(BasePort, self).__init__(parent)

        self._node = parent
        self._graph = graph
        self._name = name
        self._dataType = dataType
        self._connectionPointType = connectionPointType

        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))

        layout = QtWidgets.QGraphicsLinearLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._color = color

        self.setAcceptedMouseButtons(QtCore.Qt.RightButton)

        self._inCircle = None
        self._outCircle = None
        self._labelItem = None

        self._inCircleHolder = ItemHolder(self)
        self._outCircleHolder = ItemHolder(self)
        self._labelItemHolder = ItemHolder(self)

        self.layout().addItem(self._inCircleHolder)
        self.layout().setAlignment(self._inCircleHolder, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.layout().addItem(self._labelItemHolder)
        self.layout().setAlignment(self._labelItemHolder, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.layout().addItem(self._outCircleHolder)
        self.layout().setAlignment(self._outCircleHolder, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)


    def getName(self):
        return self._name


    def getDataType(self):
        return self._dataType


    def getNode(self):
        return self._node


    def getGraph(self):
        return self._graph


    def getColor(self):
        return self._color


    def setColor(self, color):
        if self._inCircle is not None:
            self._inCircle.setColor(color)
        if self._outCircle is not None:
            self._outCircle.setColor(color)
        self._color = color


    def inCircle(self):
        return self._inCircle


    def setInCircle(self, inCircle):
        self._inCircleHolder.setItem(inCircle)
        self._inCircle = inCircle
        self.layout().insertStretch(2, 2)
        self.updatecontentMargins()

    def outCircle(self):
        return self._outCircle


    def setOutCircle(self, outCircle):
        self._outCircleHolder.setItem(outCircle)
        self._outCircle = outCircle
        self.layout().insertStretch(1, 2)
        self.updatecontentMargins()

    def updatecontentMargins(self):
        left = 0
        right = 0
        if self._inCircle is None:
            left = 30
        if self._outCircle is None:
            right = 30
        self.layout().setContentsMargins(left, 0, right, 0)


    def labelItem(self):
        return self._labelItem


    def setLabelItem(self, labelItem):
        self._labelItemHolder.setItem(labelItem)
        self._labelItem = labelItem


    # ===================
    # Connection Methods
    # ===================
    def connectionPointType(self):
        return self._connectionPointType

    # def paint(self, painter, option, widget):
    #     super(BasePort, self).paint(painter, option, widget)
    #     painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 0)))
    #     painter.drawRect(self.windowFrameRect())


class InputPort(BasePort):

    def __init__(self, parent, graph, name, color, dataType="default", x=0, y=0):
        super(InputPort, self).__init__(parent, graph, name, color, dataType, 'In')

        self.setInCircle(PortCircle(self, graph, -2, color, 'In'))
        self.setLabelItem(PortLabel(self, name, -10, self._labelColor, self._labelHighlightColor))
        self.setAcceptedMouseButtons(QtCore.Qt.RightButton)
        self._supportsOnlySingleConnections = False

    def addConnection(self, connection):
        """Adds a connection to the list.
        Arguments:
        connection -- connection, new connection to add.
        Return:
        True if successful.
        """

        if self._supportsOnlySingleConnections and len(self.__connections) != 0:
            # gather all the connections into a list, and then remove them from the graph.
            # This is because we can't remove connections from ports while
            # iterating over the set.
            connections = []
            for c in self.__connections:
                connections.append(c)
            for c in connections:
                self._graph.removeConnection(c)

        PortCircle.__connections.add(connection)

        return True

    #########################
    ## Context Menu
    def contextMenuEvent2(self, event):
        contextMenu2 = QMenu(self.parentItem())
        portAct = contextMenu2.addAction("PortPortPort")
        #loadAct = contextMenu.addAction("Load")
        #nodeAct = contextMenu.addAction("New Node")
        p1 = event.screenPos()
        ps = QPoint(p1.x(), p1.y())
        action = contextMenu2.exec_(ps)
        if action == portAct:
            print("port context")

    def mousePressEvent(self, event):
        super(BasePort, self).mousePressEvent(event)

class OutputPort(BasePort):

    def __init__(self, parent, graph, name, color, dataType, x=0, y=0):
        super(OutputPort, self).__init__(parent, graph, name, color, dataType, 'Out')

        self.setLabelItem(PortLabel(self, self._name, 10, self._labelColor, self._labelHighlightColor))
        self.setOutCircle(PortCircle(self, graph, 2, color, 'Out'))
        self._supportsOnlySingleConnections = False

    def addConnection(self, connection):
        """Adds a connection to the list.
        Arguments:
        connection -- connection, new connection to add.
        Return:
        True if successful.
        """

        if self._supportsOnlySingleConnections and len(self.__connections) != 0:
            # gather all the connections into a list, and then remove them from the graph.
            # This is because we can't remove connections from ports while
            # iterating over the set.
            connections = []
            for c in self.__connections:
                connections.append(c)
            for c in connections:
                self._graph.removeConnection(c)

        PortCircle.__connections.add(connection)

        return True


class IOPort(BasePort):

    def __init__(self, parent, graph, name, color, dataType):
        super(IOPort, self).__init__(parent, graph, name, color, dataType, 'IO')

        self.setInCircle(PortCircle(self, graph, -2, color, 'In'))
        self.setLabelItem(PortLabel(self, self._name, 0, self._labelColor, self._labelHighlightColor))
        self.setOutCircle(PortCircle(self, graph, 2, color, 'Out'))



class GlandPort(BasePort):

    def __init__(self, parent, graph, name, color, dataType, x=0, y=0):
        super(GlandPort, self).__init__(parent, graph, name, color, dataType, 'Gland')

        self.setInCircle(PortCircle(self, graph, -2, color, 'Gland'))
        pl = PortLabel(self, self._name, 0, self._labelColor, self._labelHighlightColor)
        pl.setPos(QPointF(-20, -10))
        self.setLabelItem(pl)


