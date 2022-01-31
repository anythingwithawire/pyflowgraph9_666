
#
# Copyright 2015-2017 Eric Thivierge
#

from qtpy import QtGui, QtCore
from .port import PortCircle, PortLabel
from .connection import Connection

from .port import OutputPort, InputPort

class MouseGrabber(PortCircle):
    """docstring for MouseGrabber"""

    def __init__(self, graph, pos, otherPortCircle, connectionPointType):
        super(MouseGrabber, self).__init__(None, graph, 0, otherPortCircle.getPort().getColor(), connectionPointType)

        #super(MouseGrabber, self).__init__(None, graph, 0, otherPortCircle.getPort().getColor()''', connectionPointType)

        self._ellipseItem.setPos(0, 0)
        #self._ellipseItem.setStartAngle(0)
        #self._ellipseItem.setSpanAngle(360 * 16)

        self.__otherPortItem = otherPortCircle

        self._graph.scene().addItem(self)


        self.setZValue(-1)
        self.setTransform(QtGui.QTransform.fromTranslate(pos.x(), pos.y()), False)
        self.grabMouse()

        # import .connection as connection
        self.setConnectionPointType = 'xx'  #while it is unconnected at one end
        self.__connection = Connection(self._graph, self, otherPortCircle)
        # Do not emit a notification for this temporary connection.
        self._graph.addConnection(self.__connection, emitSignal=False)
        self.__mouseOverPortCircle = None
        self._graph.emitBeginConnectionManipulationSignal()


    def getColor(self):
        return self.__otherPortItem.getPort().getColor()


    def mouseMoveEvent(self, event):
        scenePos = self.mapToScene(event.pos())

        for connection in self.getConnections():
            connection.prepareGeometryChange()

        self.setTransform(QtGui.QTransform.fromTranslate(scenePos.x(), scenePos.y()), False)


        collidingItems = self.collidingItems(QtCore.Qt.IntersectsItemBoundingRect)
        collidingPortCircleItems = list(filter(lambda item: isinstance(item, PortCircle), collidingItems))


        #def canConnect(item):
        #if isinstance(item, PortCircle):
        #    mouseOverPortCircle = item
        if len(collidingPortCircleItems) == 1:
            self.setMouseOverPortCircle(collidingPortCircleItems[0])
            if self != collidingPortCircleItems[0]:
                if collidingPortCircleItems[0].getPort().outCircle():
                    self.__mouseOverPortCircle = collidingPortCircleItems[0]
                    return True

                if collidingPortCircleItems[0].getPort().inCircle():
                    self.__mouseOverPortCircle = collidingPortCircleItems[0]
                    return True

                return True


            """
            else:
                if self.connectionPointType() in ['In', 'GlandOut']:
                    mouseOverPortCircle = item.getPort().inCircle()
                else:
                    mouseOverPortCircle = item.getPort().outCircle()

                if self.connectionPointType() == ['Out', 'GlandIn']:
                    mouseOverPortCircle = item.getPort().outCircle()
                else:
                    mouseOverPortCircle = item.getPort().inCircle()


                if mouseOverPortCircle == None:
                    return False

            return mouseOverPortCircle.canConnectTo(self.__otherPortItem)


        collidingPortItems = list(filter(lambda port: canConnect(port), collidingPortItems))
        if len(collidingPortItems) > 0:

            if isinstance(collidingPortItems[0], PortCircle):
                self.setMouseOverPortCircle(collidingPortItems[0])
            else:
                if self.connectionPointType() in ['In', 'GlandIn']:
                    self.setMouseOverPortCircle(collidingPortItems[0].getPort().inCircle())
                else:
                    self.setMouseOverPortCircle(collidingPortItems[0].getPort().outCircle())

        elif self.__mouseOverPortCircle != None:
            self.setMouseOverPortCircle(None)
        """

    def mouseReleaseEvent(self, event):

        # Destroy the temporary connection.
        self._graph.removeConnection(self.__connection, emitSignal=False)
        sourcePortCircle = self.__otherPortItem
        targetPortCircle = self.__mouseOverPortCircle

        self.__connection = None

        if self.__mouseOverPortCircle is not None:
            connection = Connection(self._graph, sourcePortCircle, targetPortCircle)

            '''
            #try:
            if self.connectionPointType() in ['In', 'GlandIn']:
                sourcePortCircle = self.__otherPortItem
                targetPortCircle = self.__mouseOverPortCircle
            elif self.connectionPointType() in ['Out', 'GlandOut']:
                sourcePortCircle = self.__mouseOverPortCircle
                targetPortCircle = self.__otherPortItem

            connection = Connection(self._graph, sourcePortCircle, targetPortCircle)


            ####
            #### glanding
            ####
            item = sourcePortCircle.parentWidget().parentWidget().parentWidget()
            nName = item.getName()
            nNode = self._graph.getNode(nName)
            nGland = nNode.getPort("GlandIn")
            if not nGland:
                connection.__srcGlandPort = nNode.addPort(
                    OutputPort(nNode, self._graph, "GlandOut", QtGui.QColor(128, 170, 170, 255), 'GlandOut'), x=100,
                    y=30)
                connection.__srcGlandPoint = connection.mapFromScene(sourcePortCircle.centerInSceneCoords())
                print("Src Added Gland Port")
            else:
                connection.__srcGlandPoint = connection.mapFromScene(sourcePortCircle.centerInSceneCoords())
                print("Src Gland port already there")

            if targetPortCircle.parentWidget():
                item = targetPortCircle.parentWidget().parentWidget().parentWidget()
                nName = item.getName()
                nNode = self._graph.getNode(nName)
                nGland = nNode.getPort("GlandIn")
                if not nGland:
                    connection.__dstGlandPort = nNode.addPort(
                        OutputPort(nNode, self._graph, "GlandIn", QtGui.QColor(128, 170, 170, 255), 'GlandIn'), x=-100,
                        y=30)
                    connection.__dstGlandPoint = connection.mapFromScene(targetPortCircle.centerInSceneCoords())
                    print("Dst Added Gland Port")
                else:
                    connection.__dstGlandPoint = connection.mapFromScene(targetPortCircle.centerInSceneCoords())
                    print("Dst Gland port already there")

            '''
            self._graph.addConnection(connection)
            self._graph.emitEndConnectionManipulationSignal()

            #except Exception as e:
            #    print("Exception in MouseGrabber.mouseReleaseEvent: " + str(e))

            self.setMouseOverPortCircle(None)

        self.destroy()


    def setMouseOverPortCircle(self, portCircle):

        if self.__mouseOverPortCircle != portCircle:
            if self.__mouseOverPortCircle != None:
                self.__mouseOverPortCircle.unhighlight()
                self.__mouseOverPortCircle.getPort().labelItem().unhighlight()

            self.__mouseOverPortCircle = portCircle

            if self.__mouseOverPortCircle != None:
                self.__mouseOverPortCircle.highlight()
                self.__mouseOverPortCircle.getPort().labelItem().highlight()

    # def paint(self, painter, option, widget):
    #     super(MouseGrabber, self).paint(painter, option, widget)
    #     painter.setPen(QtGui.QPen(self.getColor()))
    #     painter.drawRect(self.windowFrameRect())

    def destroy(self):
        self.ungrabMouse()
        scene = self.scene()
        if self.__connection is not None:
            self._graph.removeConnection(self.__connection, emitSignal=False)
        # Destroy the grabber.
        scene.removeItem(self)
