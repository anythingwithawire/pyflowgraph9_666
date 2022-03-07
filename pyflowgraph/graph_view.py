
#
# Copyright 2015-2017 Eric Thivierge
#

import copy
import json
import re

import dicttoxml as dicttoxml
from PySide2.QtCore import QRectF, QPoint, QPointF
from PySide2.QtWidgets import QMenu, QFileDialog
from future.utils import iteritems
from past.builtins import basestring

from qtpy import QtGui, QtWidgets, QtCore, PYQT5

import pyflowgraph
#from .graph_view_widget import GraphViewWidget
from .node import Node
from .connection import Connection
from .port import InputPort, OutputPort

from .selection_rect import SelectionRect

MANIP_MODE_NONE = 0
MANIP_MODE_SELECT = 1
MANIP_MODE_PAN = 2
MANIP_MODE_MOVE = 3
MANIP_MODE_ZOOM = 4


class GraphView(QtWidgets.QGraphicsView):

    nodeAdded = QtCore.Signal(Node)
    nodeRemoved = QtCore.Signal(Node)
    nodeNameChanged = QtCore.Signal(str, str)
    beginDeleteSelection = QtCore.Signal()
    endDeleteSelection = QtCore.Signal()

    beginConnectionManipulation = QtCore.Signal()
    endConnectionManipulation = QtCore.Signal()
    connectionAdded = QtCore.Signal(Connection)
    connectionRemoved = QtCore.Signal(Connection)

    beginNodeSelection = QtCore.Signal()
    endNodeSelection = QtCore.Signal()
    selectionChanged = QtCore.Signal(list, list)

    # During the movement of the nodes, this signal is emitted with the incremental delta.
    selectionMoved = QtCore.Signal(set, QtCore.QPointF)

    # After moving the nodes interactively, this signal is emitted with the final delta.
    endSelectionMoved = QtCore.Signal(set, QtCore.QPointF)



    _clipboardData = None

    _backgroundColor = QtGui.QColor(50, 50, 50)
    _gridPenS = QtGui.QPen(QtGui.QColor(25, 44, 44, 255), 0.5)
    _gridPenL = QtGui.QPen(QtGui.QColor(25, 40, 240, 255), 1.0)
    _gridSizeFine = 30
    _gridSizeCourse = 300

    _mouseWheelZoomRate = 0.0005

    _snapToGrid = False

    def __init__(self, parent=None):
        super(GraphView, self).__init__(parent)
        self.setObjectName('graphView')

        self.__graphViewWidget = parent

        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setRenderHint(QtGui.QPainter.TextAntialiasing)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Explicitly set the scene rect. This ensures all view parameters will be explicitly controlled
        # in the event handlers of this class.
        size = QtCore.QSize(600, 400)
        self.resize(size)
        self.setSceneRect(QRectF(-size.width() * 0.5, -size.height() * 0.5, size.width(), size.height()))

        self.setAcceptDrops(True)
        self.reset()                    #set GraphicsScene in here



    def getGraphViewWidget(self):
        return self.__graphViewWidget


    ################################################
    ## Graph
    def reset(self):
        self.setScene(QtWidgets.QGraphicsScene())

        self.__connections = set()
        self.__nodes = {}
        self.__selection = set()

        self._manipulationMode = MANIP_MODE_NONE
        self._selectionRect = None

    def getGridSize(self):
        """Gets the size of the grid of the graph.

        Returns:
            int: Size of the grid.

        """

        return self._gridSizeFine

    def getSnapToGrid(self):
        """Gets the snap to grid value.

        Returns:
            Boolean: Whether snap to grid is active or not.
QMouseEvent
        """

        return self._snapToGrid

    def setSnapToGrid(self, snap):
        """Sets the snap to grid value.

        Args:
            snap (Boolean): True to snap to grid, false not to.

        """

        self._snapToGrid = snap


    ################################################
    ## Nodes

    def addNode(self, node, emitSignal=True):
        self.scene().addItem(node)
        self.__nodes[node.getName()] = node
        node.nameChanged.connect(self._onNodeNameChanged)

        if emitSignal:
            self.nodeAdded.emit(node)

        return node

    def removeNode(self, node, emitSignal=True):

        del self.__nodes[node.getName()]
        self.scene().removeItem(node)
        node.nameChanged.disconnect(self._onNodeNameChanged)

        if emitSignal:
            self.nodeRemoved.emit(node)


    def hasNode(self, name):
        return name in self.__nodes

    def getNode(self, name):
        if name in self.__nodes:
            return self.__nodes[name]
        return None

    def getNodes(self):
        return self.__nodes

    def _onNodeNameChanged(self, origName, newName ):
        if newName in self.__nodes and self.__nodes[origName] != self.__nodes[newName]:
            raise Exception("New name collides with existing node.")
        node = self.__nodes[origName]
        self.__nodes[newName] = node
        del self.__nodes[origName]
        self.nodeNameChanged.emit( origName, newName )


    def clearSelection(self, emitSignal=True):

        prevSelection = []
        if emitSignal:
            for node in self.__selection:
                prevSelection.append(node)

        for node in self.__selection:
            node.setSelected(False)
        self.__selection.clear()

        if emitSignal and len(prevSelection) != 0:
            self.selectionChanged.emit(prevSelection, [])

    def selectNode(self, node, clearSelection=False, emitSignal=True):
        prevSelection = []
        if emitSignal:
            for n in self.__selection:
                prevSelection.append(n)

        if clearSelection is True:
            self.clearSelection(emitSignal=False)

        if node in self.__selection:
            raise IndexError("Node is already in selection!")

        node.setSelected(True)
        self.__selection.add(node)

        if emitSignal:

            newSelection = []
            for n in self.__selection:
                newSelection.append(n)

            self.selectionChanged.emit(prevSelection, newSelection)


    def deselectNode(self, node, emitSignal=True):

        if node not in self.__selection:
            raise IndexError("Node is not in selection!")

        prevSelection = []
        if emitSignal:
            for n in self.__selection:
                prevSelection.append(n)

        node.setSelected(False)
        self.__selection.remove(node)

        if emitSignal:
            newSelection = []
            for n in self.__selection:
                newSelection.append(n)

            self.selectionChanged.emit(prevSelection, newSelection)

    def getSelectedNodes(self):
        return self.__selection


    def deleteSelectedNodes(self):
        self.beginDeleteSelection.emit()

        selectedNodes = self.getSelectedNodes()
        names = ""
        for node in selectedNodes:
            node.disconnectAllPorts()
            self.removeNode(node)

        self.endDeleteSelection.emit()


    def frameNodes(self, nodes):
        if len(nodes) == 0:
            return

        def computeWindowFrame():
            windowRect = self.rect()
            windowRect.setLeft(windowRect.left() + 16)
            windowRect.setRight(windowRect.right() - 16)
            windowRect.setTop(windowRect.top() + 16)
            windowRect.setBottom(windowRect.bottom() - 16)
            return windowRect

        nodesRect = None
        for node in nodes:
            nodeRectF = node.transform().mapRect(node.rect())
            nodeRect = QtCore.QRect(nodeRectF.x(), nodeRectF.y(), nodeRectF.width(), nodeRectF.height())
            if nodesRect is None:
                nodesRect = nodeRect
            else:
                nodesRect = nodesRect.united(nodeRect)


        windowRect = computeWindowFrame()

        scaleX = float(windowRect.width()) / float(nodesRect.width())
        scaleY = float(windowRect.height()) / float(nodesRect.height())
        if scaleY > scaleX:
            scale = scaleX
        else:
            scale = scaleY

        if scale < 1.0:
            self.setTransform(QtGui.QTransform.fromScale(scale, scale))
        else:
            self.setTransform(QtGui.QTransform())

        sceneRect = self.sceneRect()
        pan = sceneRect.center() - nodesRect.center()
        sceneRect.translate(-pan.x(), -pan.y())
        self.setSceneRect(sceneRect)

        # Update the main panel when reframing.
        self.update()


    def frameSelectedNodes(self):
        self.frameNodes(self.getSelectedNodes())

    def frameAllNodes(self):
        allnodes = []
        for name, node in iteritems(self.__nodes):
            allnodes.append(node)
        self.frameNodes(allnodes)

    def getSelectedNodesCentroid(self):
        selectedNodes = self.getSelectedNodes()

        leftMostNode = None
        topMostNode = None
        for node in selectedNodes:
            nodePos = node.getGraphPos()

            if leftMostNode is None:
                leftMostNode = node
            else:
                if nodePos.x() < leftMostNode.getGraphPos().x():
                    leftMostNode = node

            if topMostNode is None:
                topMostNode = node
            else:
                if nodePos.y() < topMostNode.getGraphPos().y():
                    topMostNode = node

        xPos = leftMostNode.getGraphPos().x()
        yPos = topMostNode.getGraphPos().y()
        pos = QtCore.QPoint(xPos, yPos)

        return pos


    def moveSelectedNodes(self, delta, emitSignal=True):
        for node in self.__selection:
            node.translate(delta.x(), delta.y())

        if emitSignal:
            self.selectionMoved.emit(self.__selection, delta)

    # After moving the nodes interactively, this signal is emitted with the final delta.
    def endMoveSelectedNodes(self, delta):
        self.endSelectionMoved.emit(self.__selection, delta)

    ################################################
    ## Connections

    def emitBeginConnectionManipulationSignal(self):
        self.beginConnectionManipulation.emit()


    def emitEndConnectionManipulationSignal(self):
        self.printConnections()
        self.endConnectionManipulation.emit()


    def addConnection(self, connection, emitSignal=True):

        self.__connections.add(connection)
        self.scene().addItem(connection)
        if emitSignal:
            self.connectionAdded.emit(connection)
        return connection

    def removeConnection(self, connection, emitSignal=True):
        connection.disconnect()
        if connection in self.__connections:
            self.__connections.remove(connection)
        self.scene().removeItem(connection)
        if emitSignal:
            self.connectionRemoved.emit(connection)

    def printConnections(self):
        print("===Connections===")
        for c in self.__connections:
            nodeFrom = c._Connection__srcPortCircle._PortCircle__port._node.getName()
            nodeTo = c._Connection__dstPortCircle._PortCircle__port._node.getName()
            termFrom = c._Connection__srcPortCircle._PortCircle__port._name
            termTo = c._Connection__dstPortCircle._PortCircle__port._name
            print(nodeFrom, termFrom, nodeTo, termTo)

            #print(c, c._Connection__srcPortCircle._connectionPointType, c._Connection__dstPortCircle._connectionPointType, c._Connection__srcPortCircle._PortCircle__connections, c._Connection__dstPortCircle._PortCircle__connections )
        print("=================")

    def connectPorts(self, srcNode, outputName, tgtNode, inputName) -> object:
        connection = None
        if isinstance(srcNode, Node):
            sourceNode = srcNode
        elif isinstance(srcNode, basestring):
            sourceNode = self.getNode(srcNode)
            if not sourceNode:
                raise Exception("Node not found:" + str(srcNode))
        else:
            raise Exception("Invalid srcNode:" + str(srcNode))


        sourcePort = sourceNode.getPort(outputName)
        if not sourcePort:
            raise Exception("Node '" + sourceNode.getName() + "' does not have output:" + outputName)


        if isinstance(tgtNode, Node):
            targetNode = tgtNode
        elif isinstance(tgtNode, basestring):
            targetNode = self.getNode(tgtNode)
            if not targetNode:
                raise Exception("Node not found:" + str(tgtNode))
        else:
            raise Exception("Invalid tgtNode:" + str(tgtNode))

        targetPort = targetNode.getPort(inputName)
        if not targetPort:
            raise Exception("Node '" + targetNode.getName() + "' does not have input:" + inputName)

        srcPC = None
        if sourcePort._inCircle:
            srcPC = sourcePort._inCircle
        if sourcePort._outCircle:
            srcPC = sourcePort._outCircle

        dstPC = None
        if targetPort._inCircle:
            dstPC = targetPort._inCircle
        if targetPort._outCircle:
            dstPC = targetPort._outCircle

        if srcPC and dstPC:
            connection = Connection(self, srcPC, dstPC)
            self.addConnection(connection, emitSignal=False)

        return connection
    #########################
    ## Context Menu
    def contextMenuEvent2(self, event):
        contextMenu2 = QMenu(self)
        copyAct = contextMenu2.addAction("Copy")
        pasteAct = contextMenu2.addAction("Paste")
        saveAct = contextMenu2.addAction("Save All")
        loadAct = contextMenu2.addAction("Load")
        newAct = contextMenu2.addAction("New")
        addNode = contextMenu2.addAction("Blank Node")
        #loadAct = contextMenu.addAction("Load")
        #nodeAct = contextMenu.addAction("New Node")
        p1 = event.screenPos()
        ps = QPoint(p1.x(), p1.y())
        action = contextMenu2.exec_(ps)
        if action == copyAct:
            nodesS = self.getSelectedNodes()
            nodes = {}
            for n in nodesS:
                k = n.getName()
                nodes[k] = n
            self.saveNodesCopy(nodes, 'copyBuf.json')

        if action == pasteAct:
            pastePos = QPointF(event.pos())
            self.loadNodes('copyBuf.json', pastePos)

        if action == addNode:
            node = Node(self, "blank", xSize=50, ySize=100)
            node.setPos(QPointF(event.x(), event.y()))
            self.addNode(node)

        if action == newAct:
            self.reset()

        if action == saveAct:
            nodesD = self.getNodes()
            file, check = QFileDialog.getSaveFileName(None, "QFileDialog.getSaveFileName()", "", "Json Files (*.json)")
            if check:
                self.saveNodes(nodesD, file)

        if action == loadAct:
            file, check = QFileDialog.getOpenFileName(None, "QFileDialog.getOpenFileName()", "", "Json Files (*.json)")
            if check:
                self.loadNodes(file, QPointF(0, 0))

    ################################################
    ## Events

    def loadNodes(self, fileName, offsetPos):
        from pyflowgraph.graph_view_widget import GraphViewWidget
        graph = GraphViewWidget.getGraphView(GraphViewWidget.clsSelf[0])
        in_file = open(fileName, 'r')
        graphD = json.load(in_file)
        print(graphD)
        allConnections = []
        allConnections.clear()
        # self.prepareConnectionGeometryChange()

        names = []
        for node in graphD['nodes']:        #rename any of the nodes that need it here
            nameUpdate = {}
            node['oldName'] = None          #and keep a list so we can update connections
            name = str(node['name'])
            print("name", name)
            newName = name[:]               #make sure to actually geta copy of the var
            seqNum = 1
            while self.getNode(newName):                  #name already exists, keep trying until newName is new
                if name[-1:].isdigit() and name[-2:-1].isdigit() and name[-3:-2] == '_':
                    blkNum = int(name[-2:]) + 1
                    newName = name[:-3] + '_' + str(blkNum).zfill(2)
                else:
                    newName = name + '_' + str(seqNum).zfill(2)
                    seqNum = seqNum+1
                print("newName", newName)
                #node['oldName'] = name
                node['name'] = str(newName)
            nameUpdate['oldName'] = name
            nameUpdate['name'] = newName
            names.append(nameUpdate)

        for node in graphD['nodes']:
            # node.prepareConnectionGeometryChange()

            node1 = Node(graph, node['name'], xSize=float(node['width']), ySize=float(node['height']))
            for p in node['ports']:
                if p['connectionPointType'] == 'In':
                    node1.addPort(InputPort(node1, graph, p['name'],
                                            QtGui.QColor.fromRgbF(float(p['colorR']), float(p['colorB']),
                                                                  float(p['colorG']), float(p['colorT'])),
                                            dataType=p['dataType']), x=float(p['x']), y=float(p['y']))
                if p['connectionPointType'] == 'Out':
                    node1.addPort(OutputPort(node1, graph, p['name'],
                                             QtGui.QColor.fromRgbF(float(p['colorR']), float(p['colorB']),
                                                                   float(p['colorG']), float(p['colorT'])),
                                             dataType=p['dataType']),
                                  x=float(p['x']), y=float(p['y']))
                d = p['connections']
                if d:
                    allConnections.append(d)
            graph.addNode(node1)
            node1.setPos(float(node['x'] + offsetPos.x()), float(node['y'] + offsetPos.y()))
        print("names==>", names)

        print("allConnections==>", allConnections)
        print("\n\n")
        for portConnections in allConnections:
            for checkName in names:  # replace old block names with new
                if portConnections[0]['nodeFrom'] in checkName['oldName']:
                    portConnections[0]['nodeFrom'] = checkName['name']
                if portConnections[0]['nodeTo'] in checkName['oldName']:
                    portConnections[0]['nodeTo'] = checkName['name']

        print("allConnections==>", allConnections)

        for cc in allConnections:
            c = cc[0]
            self.connectPorts(c['nodeFrom'], c['termFrom'], c['nodeTo'], c['termTo'])
            # connection = Connection(graph, graph.getNode(c['nodeFrom']).getPort(c['termFrom']), graph.getNode(c['nodeTo']).getPort(c['termTo']))
            # graph.__connections.add(connection)
            # self.connectPorts(self.getNode(c['nodeFrom']), c['termFrom'], self.getNode(c['nodeTo']), c['termTo'])

    def saveNodes(self, nodes, fileName):
        graphD = {}
        graphD = {'nodes': []}
        for n in nodes.values():
            nodeD = {}
            c1 = str(re.findall(r'\(.*?\)', str(n.getColor())))
            c2 = c1[3:-4]
            c3 = c2.split(',')  # TODO dodgy
            nodeD = {
                'width': str(n.getWidth()),
                'height': str(n.getHeight()),
                'x': n.pos().x(),
                'y': n.pos().y(),
                'name': str(n.getName()),
                'colorR': c3[0],  # extract the color from inside the brackets
                'colorG': c3[1],  # extract the color from inside the brackets
                'colorB': c3[2],  # extract the color from inside the brackets
                'colorT': c3[3],  # extract the color from inside the brackets
                'ports': []
            }
            for p in n.getPorts():
                portD = {}
                c1 = str(re.findall(r'\(.*?\)', str(p.getColor())))
                c2 = c1[3:-4]
                c3 = c2.split(',')  # TODO another super dodgy
                portD = {
                    'x': str(p.pos().x()),
                    'y': str(p.pos().y()),
                    'connectionPointType': str(p.connectionPointType()),
                    'dataType': str(p.getDataType()),
                    'colorR': c3[0],  # extract the color from inside the brackets
                    'colorG': c3[1],  # extract the color from inside the brackets
                    'colorB': c3[2],  # extract the color from inside the brackets
                    'colorT': c3[3],  # extract the color from inside the brackets
                    'name': str(p.getName()),
                    'connections': []
                }
                connectionsD = {}
                if p._inCircle:
                    cc = p._inCircle.getConnections()
                if p._outCircle:
                    cc = p._outCircle.getConnections()
                if cc:
                    for c in cc:
                        nodeFrom = c._Connection__srcPortCircle._PortCircle__port._node.getName()
                        nodeTo = c._Connection__dstPortCircle._PortCircle__port._node.getName()
                        termFrom = c._Connection__srcPortCircle.getPort().getName(),
                        termTo = c._Connection__dstPortCircle.getPort().getName()
                        connectionsD = {
                            'nodeFrom': str(nodeFrom),
                            'nodeTo': str(nodeTo),
                            'termFrom': str(termFrom[0]),
                            'termTo': str(termTo),  # TODO TODO mega dodgy
                            'srcPortCircle': str(c._Connection__srcPortCircle.getPort()),
                            'dstPortCircle': str(c._Connection__dstPortCircle.getPort()),
                            'node': []
                        }
                    portD['connections'].append(connectionsD)
                nodeD['ports'].append(portD)
            graphD['nodes'].append(nodeD)

        #fileName = 'graph.json'
        out_file = open(fileName, 'w')
        json.dump(graphD, out_file, indent=6)

        #fileName = 'graph.xml'
        #xml = dicttoxml.dicttoxml(graphD)
        #with open(fileName, 'w') as file_object:
        #    file_object.write(str(xml))

    def saveNodesCopy(self, nodes, fileName):
        graphD = {}
        graphD = {'nodes': []}
        copyNodes = nodes.values()
        for n in copyNodes:
            nodeD = {}
            c1 = str(re.findall(r'\(.*?\)', str(n.getColor())))
            c2 = c1[3:-4]
            c3 = c2.split(',')  # TODO dodgy
            nodeD = {
                'width': str(n.getWidth()),
                'height': str(n.getHeight()),
                'x': n.pos().x(),
                'y': n.pos().y(),
                'name': str(n.getName()),
                'colorR': c3[0],  # extract the color from inside the brackets
                'colorG': c3[1],  # extract the color from inside the brackets
                'colorB': c3[2],  # extract the color from inside the brackets
                'colorT': c3[3],  # extract the color from inside the brackets
                'ports': []
            }
            for p in n.getPorts():
                portD = {}
                c1 = str(re.findall(r'\(.*?\)', str(p.getColor())))
                c2 = c1[3:-4]
                c3 = c2.split(',')  # TODO another super dodgy
                portD = {
                    'x': str(p.pos().x()),
                    'y': str(p.pos().y()),
                    'connectionPointType': str(p.connectionPointType()),
                    'dataType': str(p.getDataType()),
                    'colorR': c3[0],  # extract the color from inside the brackets
                    'colorG': c3[1],  # extract the color from inside the brackets
                    'colorB': c3[2],  # extract the color from inside the brackets
                    'colorT': c3[3],  # extract the color from inside the brackets
                    'name': str(p.getName()),
                    'connections': []
                }
                connectionsD = {}
                connections = None                              #TODO a bunch of getters to avoid accessing protected
                if p._inCircle:                                 #this assumes a port can only be in or out type
                    connections = p._inCircle.getConnections()
                if p._outCircle:
                    connections = p._outCircle.getConnections()
                for c in connections:
                    nodeFromNode = c._Connection__srcPortCircle._PortCircle__port._node
                    nodeToNode = c._Connection__dstPortCircle._PortCircle__port._node
                    if nodeFromNode in copyNodes and nodeToNode in copyNodes:
                        nodeFrom = c._Connection__srcPortCircle._PortCircle__port._node.getName()
                        nodeTo = c._Connection__dstPortCircle._PortCircle__port._node.getName()
                        termFrom = c._Connection__srcPortCircle.getPort().getName(),
                        termTo = c._Connection__dstPortCircle.getPort().getName()
                        connectionsD = {
                            'nodeFrom': str(nodeFrom),
                            'nodeTo': str(nodeTo),
                            'termFrom': str(termFrom[0]),
                            'termTo': str(termTo),  # TODO TODO mega dodgy
                            'srcPortCircle': str(c._Connection__srcPortCircle.getPort()),
                            'dstPortCircle': str(c._Connection__dstPortCircle.getPort()),
                            'node': []
                        }
                        portD['connections'].append(connectionsD)
                nodeD['ports'].append(portD)
            graphD['nodes'].append(nodeD)

        #fileName = 'graph.json'
        out_file = open(fileName, 'w')
        json.dump(graphD, out_file, indent=6)

        #fileName = 'graph.xml'
        #xml = dicttoxml.dicttoxml(graphD)
        #with open(fileName, 'w') as file_object:
        #    file_object.write(str(xml))

    def mousePressEvent(self, event):

        if event.button() == QtCore.Qt.LeftButton and self.itemAt(event.pos()) is None:
            self.beginNodeSelection.emit()
            self._manipulationMode = MANIP_MODE_SELECT
            self._mouseDownSelection = copy.copy(self.getSelectedNodes())
            self.clearSelection(emitSignal=False)
            self._selectionRect = SelectionRect(graph=self, mouseDownPos=self.mapToScene(event.pos()))

        if event.button() == QtCore.Qt.MidButton or event.button() == QtCore.Qt.MiddleButton and self.itemAt(event.pos()) is None:
            self.setCursor(QtCore.Qt.OpenHandCursor)
            self._manipulationMode = MANIP_MODE_PAN
            self._lastPanPoint = self.mapToScene(event.pos())

        if event.button() == QtCore.Qt.RightButton and self.itemAt(event.pos()) is None:
            self.setCursor(QtCore.Qt.SizeHorCursor)
            #self._manipulationMode = MANIP_MODE_ZOOM
            self._lastMousePos = event.pos()
            self._lastTransform = QtGui.QTransform(self.transform())
            self._lastSceneRect = self.sceneRect()
            self._lastSceneCenter = self._lastSceneRect.center()
            self._lastScenePos = self.mapToScene(event.pos())
            self._lastOffsetFromSceneCenter = self._lastScenePos - self._lastSceneCenter
            self.contextMenuEvent2(event)

        super(GraphView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if self._manipulationMode == MANIP_MODE_SELECT:
            dragPoint = self.mapToScene(event.pos())
            self._selectionRect.setDragPoint(dragPoint)

            # This logic allows users to use ctrl and shift with rectangle
            # select to add / remove nodes.
            if modifiers == QtCore.Qt.ControlModifier:
                for name, node in iteritems(self.__nodes):

                    if node in self._mouseDownSelection:
                        if node.isSelected() and self._selectionRect.collidesWithItem(node):
                            self.deselectNode(node, emitSignal=False)
                        elif not node.isSelected() and not self._selectionRect.collidesWithItem(node):
                            self.selectNode(node, emitSignal=False)
                    else:
                        if not node.isSelected() and self._selectionRect.collidesWithItem(node):
                            self.selectNode(node, emitSignal=False)
                        elif node.isSelected() and not self._selectionRect.collidesWithItem(node):
                            if node not in self._mouseDownSelection:
                                self.deselectNode(node, emitSignal=False)

            elif modifiers == QtCore.Qt.ShiftModifier:
                for name, node in iteritems(self.__nodes):
                    if not node.isSelected() and self._selectionRect.collidesWithItem(node):
                        self.selectNode(node, emitSignal=False)
                    elif node.isSelected() and not self._selectionRect.collidesWithItem(node):
                        if node not in self._mouseDownSelection:
                            self.deselectNode(node, emitSignal=False)

            else:
                self.clearSelection(emitSignal=False)

                for name, node in iteritems(self.__nodes):
                    if not node.isSelected() and self._selectionRect.collidesWithItem(node):
                        self.selectNode(node, emitSignal=False)
                    elif node.isSelected() and not self._selectionRect.collidesWithItem(node):
                        self.deselectNode(node, emitSignal=False)

        elif self._manipulationMode == MANIP_MODE_PAN:
            delta = self.mapToScene(event.pos()) - self._lastPanPoint

            rect = self.sceneRect()
            rect.translate(-delta.x(), -delta.y())
            self.setSceneRect(rect)

            self._lastPanPoint = self.mapToScene(event.pos())

        elif self._manipulationMode == MANIP_MODE_MOVE:

            newPos = self.mapToScene(event.pos())
            delta = newPos - self._lastDragPoint
            self._lastDragPoint = newPos

            selectedNodes = self.getSelectedNodes()

            # Apply the delta to each selected node
            for node in selectedNodes:
                node.translate(delta.x(), delta.y())

        elif self._manipulationMode == MANIP_MODE_ZOOM:

           # How much
            delta = event.pos() - self._lastMousePos
            zoomFactor = 1.0
            if delta.x() > 0:
                zoomFactor = 1.0 + delta.x() / 100.0
            else:
                zoomFactor = 1.0 / (1.0 + abs(delta.x()) / 100.0)

            # Limit zoom to 3x
            if self._lastTransform.m22() * zoomFactor >= 2.0:
                return

            # Reset to when we mouse pressed
            self.setSceneRect(self._lastSceneRect)
            self.setTransform(self._lastTransform)

            # Center scene around mouse down
            rect = self.sceneRect()
            rect.translate(self._lastOffsetFromSceneCenter)
            self.setSceneRect(rect)

            # Zoom in (QGraphicsView auto-centers!)
            self.scale(zoomFactor, zoomFactor)

            newSceneCenter = self.sceneRect().center()
            newScenePos = self.mapToScene(self._lastMousePos)
            newOffsetFromSceneCenter = newScenePos - newSceneCenter

            # Put mouse down back where is was on screen
            rect = self.sceneRect()
            rect.translate(-1 * newOffsetFromSceneCenter)
            self.setSceneRect(rect)

            # Call udpate to redraw background
            self.update()


        else:
            super(GraphView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._manipulationMode == MANIP_MODE_SELECT:

            # If users simply clicks in the empty space, clear selection.
            if self.mapToScene(event.pos()) == self._selectionRect.pos():
                self.clearSelection(emitSignal=False)

            self._selectionRect.destroy()
            self._selectionRect = None
            self._manipulationMode = MANIP_MODE_NONE

            selection = self.getSelectedNodes()

            deselectedNodes = []
            selectedNodes = []

            for node in self._mouseDownSelection:
                if node not in selection:
                    deselectedNodes.append(node)

            for node in selection:
                if node not in self._mouseDownSelection:
                    selectedNodes.append(node)

            if selectedNodes != deselectedNodes:
                self.selectionChanged.emit(deselectedNodes, selectedNodes)

            self.endNodeSelection.emit()

        elif self._manipulationMode == MANIP_MODE_PAN:
            self.setCursor(QtCore.Qt.ArrowCursor)
            self._manipulationMode = MANIP_MODE_NONE

        elif self._manipulationMode == MANIP_MODE_ZOOM:
            self.setCursor(QtCore.Qt.ArrowCursor)
            self._manipulationMode = MANIP_MODE_NONE
            #self.setTransformationAnchor(self._lastAnchor)

        else:
            super(GraphView, self).mouseReleaseEvent(event)

    def wheelEvent(self, event):

        (xfo, invRes) = self.transform().inverted()
        topLeft = xfo.map(self.rect().topLeft())
        bottomRight = xfo.map(self.rect().bottomRight())
        center = ( topLeft + bottomRight ) * 0.5

        if PYQT5:
            zoomFactor = 1.0 + event.angleDelta().y() * self._mouseWheelZoomRate
        else:
             zoomFactor = 1.0 + event.delta() * self._mouseWheelZoomRate

        transform = self.transform()

        # Limit zoom to 3x
        if transform.m22() * zoomFactor >= 2.0:
            return

        self.scale(zoomFactor, zoomFactor)

        # Call udpate to redraw background
        self.update()


    ################################################
    ## Painting

    def drawBackground(self, painter, rect):

        oldTransform = painter.transform()
        painter.fillRect(rect, self._backgroundColor)

        left = int(rect.left()) - (int(rect.left()) % self._gridSizeFine)
        top = int(rect.top()) - (int(rect.top()) % self._gridSizeFine)

        # Draw horizontal fine lines
        gridLines = []
        painter.setPen(self._gridPenS)
        y = float(top)
        while y < float(rect.bottom()):
            gridLines.append(QtCore.QLineF( rect.left(), y, rect.right(), y ))
            y += self._gridSizeFine
        painter.drawLines(gridLines)

        # Draw vertical fine lines
        gridLines = []
        painter.setPen(self._gridPenS)
        x = float(left)
        while x < float(rect.right()):
            gridLines.append(QtCore.QLineF( x, rect.top(), x, rect.bottom()))
            x += self._gridSizeFine
        painter.drawLines(gridLines)

        # Draw thick grid
        left = int(rect.left()) - (int(rect.left()) % self._gridSizeCourse)
        top = int(rect.top()) - (int(rect.top()) % self._gridSizeCourse)

        # Draw vertical thick lines
        gridLines = []
        painter.setPen(self._gridPenL)
        x = left
        while x < rect.right():
            gridLines.append(QtCore.QLineF( x, rect.top(), x, rect.bottom() ))
            x += self._gridSizeCourse
        painter.drawLines(gridLines)

        # Draw horizontal thick lines
        gridLines = []
        painter.setPen(self._gridPenL)
        y = top
        while y < rect.bottom():
            gridLines.append(QtCore.QLineF( rect.left(), y, rect.right(), y ))
            y += self._gridSizeCourse
        painter.drawLines(gridLines)

        return super(GraphView, self).drawBackground(painter, rect)
