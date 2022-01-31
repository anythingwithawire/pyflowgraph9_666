
#
# Copyright 2015-2017 Eric Thivierge
#
from qtpy.QtCore import QPointF
from qtpy import QtGui, QtWidgets, QtCore


class Connection(QtWidgets.QGraphicsPathItem):
    __defaultPen = QtGui.QPen(QtGui.QColor(168, 134, 3), 1.5)
    __whitePen = QtGui.QPen(QtGui.QColor(255, 255, 255), 0.5)
    __smallFont = QtGui.QFont('Helvetica', 6)
    __medFont = QtGui.QFont('Helvetica', 8)

    def __init__(self, graph, srcPortCircle, dstPortCircle):
        super(Connection, self).__init__()

        self.__graph = graph
        self.__srcPortCircle = srcPortCircle
        self.__dstPortCircle = dstPortCircle
        penStyle = QtCore.Qt.DashLine

        self.__connectionColor = QtGui.QColor(0, 0, 0)
        self.__connectionColor.setRgbF(*self.__srcPortCircle.getColor().getRgbF())
        self.__connectionColor.setAlpha(125)

        self.__defaultPen = QtGui.QPen(self.__connectionColor, 1.5, style=penStyle)
        self.__defaultPen.setDashPattern([1, 2, 2, 1])

        self.__connectionHoverColor = QtGui.QColor(0, 0, 0)
        self.__connectionHoverColor.setRgbF(*self.__srcPortCircle.getColor().getRgbF())
        self.__connectionHoverColor.setAlpha(255)

        self.__hoverPen = QtGui.QPen(self.__connectionHoverColor, 1.5, style=penStyle)
        self.__hoverPen.setDashPattern([1, 2, 2, 1])

        self.setPen(self.__defaultPen)
        self.setZValue(-1)

        self.setAcceptHoverEvents(True)
        self.connect()


    def setPenStyle(self, penStyle):
        self.__defaultPen.setStyle(penStyle)
        self.__hoverPen.setStyle(penStyle)
        self.setPen(self.__defaultPen) # Force a redraw


    def setPenWidth(self, width):
        self.__defaultPen.setWidthF(width)
        self.__hoverPen.setWidthF(width)
        self.setPen(self.__defaultPen) # Force a redraw


    def getSrcPortCircle(self):
        return self.__srcPortCircle


    def getDstPortCircle(self):
        return self.__dstPortCircle


    def getSrcPort(self):
        return self.__srcPortCircle.getPort()


    def getDstPort(self):
        return self.__dstPortCircle.getPort()


    def boundingRect(self):
        srcPoint = self.mapFromScene(self.__srcPortCircle.centerInSceneCoords())
        dstPoint = self.mapFromScene(self.__dstPortCircle.centerInSceneCoords())
        #penWidth = self.__defaultPen.width()
        penWidth = 20

        return QtCore.QRectF(
            min(srcPoint.x(), dstPoint.x()),
            min(srcPoint.y(), dstPoint.y()),
            abs(dstPoint.x() - srcPoint.x()),
            abs(dstPoint.y() - srcPoint.y()),
            ).adjusted(-penWidth/2, -penWidth/2, +penWidth/2, +penWidth/2)


    def paint(self, painter, option, widget):
        srcPoint = self.mapFromScene(self.__srcPortCircle.centerInSceneCoords())
        dstPoint = self.mapFromScene(self.__dstPortCircle.centerInSceneCoords())

        dist_between = dstPoint - srcPoint

        #self.painter = QtGui.QPainter()

        srcPort = self.__srcPortCircle.getPort()
        dstPort = self.__dstPortCircle.getPort()

        self.__path = QtGui.QPainterPath()
        self.setPen(self.__defaultPen)
        self.__path.moveTo(srcPoint)

        if dstPort and srcPort:
            if dstPort._connectionPointType == "Gland" and srcPort._connectionPointType == 'Gland':
                self.__path.lineTo((dstPoint.x()+srcPoint.x())/2, srcPoint.y())
                self.__path.lineTo((dstPoint.x() + srcPoint.x()) / 2, dstPoint.y())
                self.__path.lineTo(dstPoint.x(), dstPoint.y())
            else:
                self.__path.lineTo(dstPoint.x(), srcPoint.y())
                self.__path.lineTo(dstPoint.x(), dstPoint.y())

        else:
            self.__path.lineTo(dstPoint.x(), srcPoint.y())
            self.__path.lineTo(dstPoint.x(), dstPoint.y())

        #self.__path.quadTo(
        #    dstPoint - QtCore.QPointF(dist_between.x() * 0.3, 0),
        #    dstPoint)

        #self.__path.lineTo(dstPoint - QtCore.QPointF(dist_between.x() * 0.0),dstPoint)


        self.setPen(self.__whitePen)
        textPoint1 = QPointF(srcPoint.x() + 10, srcPoint.y() - 1)
        textPoint2 = QPointF(srcPoint.x() + 10, srcPoint.y() - 1)

        if dstPort and srcPort:
            if dstPort._connectionPointType == "Gland" and srcPort._connectionPointType == 'Out':
                textPoint1 = QPointF(srcPoint.x()+10, srcPoint.y()-1)
        if dstPort and srcPort:
            if dstPort._connectionPointType == "Gland" and srcPort._connectionPointType == 'In':
                textPoint1 = QPointF(srcPoint.x()-30, srcPoint.y()-1)
        self.__path.addText(textPoint1,self.__smallFont, "0001")

        if dstPort and srcPort:
            if dstPort._connectionPointType == "Gland" and srcPort._connectionPointType == 'Out':
                textPoint2 = QPointF(srcPoint.x()+40, srcPoint.y()-1)
        if dstPort and srcPort:
            if dstPort._connectionPointType == "Gland" and srcPort._connectionPointType == 'In':
                textPoint2 = QPointF(srcPoint.x()-90, srcPoint.y()-1)
        self.__path.addText(textPoint2, self.__medFont, "WireMark")

        self.setPath(self.__path)


        #self.painter.drawPath(self.__path)

        #self.addPath(self.__text)


        super(Connection, self).paint(painter, option, widget)


    def hoverEnterEvent(self, event):
        self.setPen(self.__hoverPen)
        super(Connection, self).hoverEnterEvent(event)


    def hoverLeaveEvent(self, event):
        self.setPen(self.__defaultPen)
        super(Connection, self).hoverLeaveEvent(event)


    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.__dragging = True
            self._lastDragPoint = self.mapToScene(event.pos())
            event.accept()
        else:
            super(Connection, self).mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if self.__dragging:
            pos = self.mapToScene(event.pos())
            delta = pos - self._lastDragPoint
            if delta.x() != 0:

                self.__graph.removeConnection(self)

                from . import mouse_grabber
                if delta.x() < 0:
                    mouse_grabber.MouseGrabber(self.__graph, pos, self.__srcPortCircle, 'In')
                else:
                    mouse_grabber.MouseGrabber(self.__graph, pos, self.__dstPortCircle, 'Out')

        else:
            super(Connection, self).mouseMoveEvent(event)


    def disconnect(self):
        self.__srcPortCircle.removeConnection(self)
        self.__dstPortCircle.removeConnection(self)


    def connect(self):
        self.__srcPortCircle.addConnection(self)
        self.__dstPortCircle.addConnection(self)
