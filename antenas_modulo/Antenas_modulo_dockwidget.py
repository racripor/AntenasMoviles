# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AntenasMovilesDockWidget
                                 A QGIS plugin
 Representa antenas moviles y localiza la mas cercana a posicion
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-04-28
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Rafael Criado Portero
        email                : idu15398@usal.es
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import sys

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsProject, QgsVectorLayer,QgsField, QgsFeature, QgsGeometry,QgsPointXY
from PyQt5.QtCore import QVariant
import math

from PyQt5.QtWidgets import QApplication, QDialog, QGraphicsPixmapItem, QGraphicsScene
from PyQt5.QtGui import QPixmap


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Antenas_modulo_dockwidget_base.ui'))


class AntenasMovilesDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(AntenasMovilesDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.qfw_selector.setFilter("Archivos csv(*.csv)")
        self.btn_cargar.clicked.connect(self.cargar_datos)
        self.btn_crearcapa.clicked.connect(self.crear_capa)
        self.btn_cercana.clicked.connect(self.calcular_cercana)

    def cargar_datos(self, event):
        ruta = str(self.qfw_selector.filePath())
        x = float(self.txt_x.text())
        y = float(self.txt_y.text())
        rx = 0
        ry = 0
        with open(ruta, 'r') as leer_csv:  # abro el archivo para leer
            lineas = leer_csv.read().splitlines()  # Separo por lineas
            contar = 0
            for linea in lineas:
                if contar > 0:
                    campos = linea.split(';')
                    rx = float(campos[4]) - x
                    ry = float(campos[3]) - y
                    dist = math.sqrt(rx * rx + ry * ry) #Calculo la distancia a la antena
                    self.qtw_tabla.insertRow(self.qtw_tabla.rowCount())
                    self.qtw_tabla.setItem(self.qtw_tabla.rowCount() - 1, 0, QtWidgets.QTableWidgetItem((campos[0])))
                    self.qtw_tabla.setItem(self.qtw_tabla.rowCount() - 1, 1, QtWidgets.QTableWidgetItem((campos[1])))
                    self.qtw_tabla.setItem(self.qtw_tabla.rowCount() - 1, 2, QtWidgets.QTableWidgetItem((campos[4])))
                    self.qtw_tabla.setItem(self.qtw_tabla.rowCount() - 1, 3, QtWidgets.QTableWidgetItem((campos[3])))
                    self.qtw_tabla.setItem(self.qtw_tabla.rowCount() - 1, 4, QtWidgets.QTableWidgetItem(str(dist)))
                contar = contar + 1

    def crear_capa(self, event):
        vlayer = QgsVectorLayer('Point?crs=EPSG:4326', 'Antenas Moviles', 'memory')
        provider = vlayer.dataProvider()
        provider.addAttributes([QgsField('Codigo_Antena', QVariant.String), QgsField('Nombre_Antena', QVariant.String)])
        vlayer.updateFields()
        for fila in range(0, self.qtw_tabla.rowCount() ):
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(self.qtw_tabla.item(fila, 2).text()), float(self.qtw_tabla.item(fila, 3).text()))))
            f.setAttributes([self.qtw_tabla.item(fila, 0).text(), self.qtw_tabla.item(fila, 1).text()])
            provider.addFeature(f)
        vlayer.updateExtents()
        QgsProject.instance().addMapLayer(vlayer)

    def calcular_cercana(self, event):

        #defino los valores del punto de situacion
        x = float(self.txt_x.text())
        y = float(self.txt_y.text())

        #asigno la distancia del primer elemento como mínima, a la espera de comprobar el resto
        cercana=float(self.qtw_tabla.item(0, 4).text())
        fila_cercana=0
        for fila in range(0, self.qtw_tabla.rowCount()):
            dist_act=float(self.qtw_tabla.item(fila, 4).text())
            if dist_act<cercana:
                #Si es el punto de menor distancia, actualizo el minimo y grabo la fila correspondiente
                cercana=dist_act
                fila_cercana=fila
        #relleno los valores de la antena mas cercana
        self.txt_distancia.setText(str(cercana))
        self.txt_codigo.setText(self.qtw_tabla.item(fila_cercana, 0).text())
        self.txt_nombre.setText(self.qtw_tabla.item(fila_cercana, 1).text())

        # Mostramos la imagen de la antena más cercana
        ruta_plugin = os.path.dirname(__file__)
        self.lbl_foto.setPixmap(QtGui.QPixmap(ruta_plugin + "/datos/" + self.qtw_tabla.item(fila_cercana, 0).text() + ".jpg"))

        # Creamos una capa con la linea que une la posicion con la antena mas cercana
        dlayer = QgsVectorLayer('Linestring?crs=EPSG:4326', 'Linea de distancia', 'memory')

        x_antena_cercana=float(self.qtw_tabla.item(fila_cercana, 2).text())
        y_antena_cercana = float(self.qtw_tabla.item(fila_cercana, 3).text())
        points = []
        pt = QgsPointXY(x, y)#Coordenadas indicadas
        points.append(pt)
        pt = QgsPointXY(x_antena_cercana, y_antena_cercana)
        points.append(pt)
        fields = dlayer.dataProvider().fields()
        f2 = QgsFeature()
        f2.setGeometry(QgsGeometry.fromPolylineXY(points))
        f2.setFields(fields)

        dlayer.dataProvider().addFeature(f2)

        dlayer.updateExtents()
        QgsProject.instance().addMapLayer(dlayer)



    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
