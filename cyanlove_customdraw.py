import csv
import os
import pathlib
import sqlite3
import threading
from datetime import datetime

import chardet
import pandas as pd
from PyQt5.QtCore import QThread

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt import QtWidgets, uic, QtCore
from qgis.PyQt.QtCore import pyqtSignal
import re
from qgis._core import QgsProject, QgsVectorLayer, QgsPointXY, QgsGeometry, QgsFeature, QgsFillSymbol, \
    QgsSingleSymbolRenderer, QgsField, QgsRendererCategory, \
    QgsCategorizedSymbolRenderer, QgsFields, QgsPoint, QgsPolygon, QgsLineString
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'cyanlove_customdraw.base.ui'))


class cyanlove_customdraw(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(cyanlove_customdraw, self).__init__(parent)
        self.export_thread = None
        self.setupUi(self)
        self.pushButton_2.clicked.connect(self.drawpoint)
        self.pushButton_3.clicked.connect(self.drawLineString)
        self.pushButton.clicked.connect(self.drawPolygon)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def drawpoint(self):
        points = self.textEdit.toPlainText()
        # 使用splitlines()按行分割文本
        points_list = points.splitlines()
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        layname = 'SSJ_Cretepoint_' + timestamp
        layers = QgsProject.instance().mapLayersByName(layname)
        if layers:
            for layer in layers:
                QgsProject.instance().removeMapLayer(layer.id())

        layer = QgsVectorLayer("Point?crs=EPSG:4326", layname, "memory")
        provider = layer.dataProvider()  # 获取图层的数据提供者
        # 输出
        for index, point in enumerate(points_list):
            geom = QgsGeometry.fromWkt(point)  # 从 WKT 转换为几何对象
            # 检查几何对象的有效性
            if geom.isGeosValid():
                feature = QgsFeature()  # 创建新特征
                feature.setGeometry(geom)  # 设置几何对象
                provider.addFeatures([feature])  # 将特征添加到数据提供者
            else:

                try:
                    # 替换中文逗号为英文逗号
                    output_string = point.replace("，", ",")
                    lon, lat = map(float, output_string.split(','))  # 转换为浮点数

                    point1 = QgsPointXY(lon, lat)
                    geom = QgsGeometry.fromPointXY(point1)
                    if geom.isGeosValid():  # 检查几何对象的有效性
                        feature = QgsFeature()  # 创建新特征
                        feature.setGeometry(geom)  # 设置几何对象
                        provider.addFeatures([feature])  # 将特征添加到数据提供者
                except ValueError:
                    print("输入格式不正确，请确保输入为 'lon,lat' 的格式并且包含有效的浮点数。")
                    continue

        QgsProject.instance().addMapLayer(layer, True)
        iface.mapCanvas().refresh()

    def drawLineString(self):
        pointsline = self.textEdit.toPlainText()
        # 使用splitlines()按行分割文本
        pointline_list = pointsline.splitlines()
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        layname = 'SSJ_CreteLine_' + timestamp
        layers = QgsProject.instance().mapLayersByName(layname)
        if layers:
            for layer in layers:
                QgsProject.instance().removeMapLayer(layer.id())

        layer = QgsVectorLayer("LineString?crs=EPSG:4326", layname, "memory")
        provider = layer.dataProvider()  # 获取图层的数据提供者
        # 输出
        for index, pointline in enumerate(pointline_list):
            geom = QgsGeometry.fromWkt(pointline)  # 从 WKT 转换为几何对象
            # 检查几何对象的有效性
            if geom.isGeosValid():
                feature = QgsFeature()  # 创建新特征
                feature.setGeometry(geom)  # 设置几何对象
                provider.addFeatures([feature])  # 将特征添加到数据提供者
            else:

                try:
                    # 替换中文逗号为英文逗号
                    output_string = pointline.replace("，", ",")
                    output_stringlines = output_string.split(';')
                    pointslines = []
                    istrue = True
                    for line in output_stringlines:
                        try:
                            lon, lat = map(float, line.split(','))  # 转换为浮点数
                            point1 = QgsPointXY(lon, lat)
                            pointslines.append(point1)
                        except ValueError:
                            istrue = False
                    # 如果其中有一个经纬度错误
                    if istrue:
                        geom = QgsGeometry.fromPolylineXY(pointslines)
                        if geom.isGeosValid():  # 检查几何对象的有效性
                            feature = QgsFeature()  # 创建新特征
                            feature.setGeometry(geom)  # 设置几何对象
                            provider.addFeatures([feature])  # 将特征添加到数据提供者
                except Exception as e:
                    print(index,e)
                    continue

        QgsProject.instance().addMapLayer(layer, True)
        iface.mapCanvas().refresh()

    def drawPolygon(self):
        pointsline = self.textEdit.toPlainText()
        # 使用splitlines()按行分割文本
        pointline_list = pointsline.splitlines()
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        layname = 'SSJ_CretePolygon_' + timestamp
        layers = QgsProject.instance().mapLayersByName(layname)
        if layers:
            for layer in layers:
                QgsProject.instance().removeMapLayer(layer.id())

        layer = QgsVectorLayer("Polygon?crs=EPSG:4326", layname, "memory")
        provider = layer.dataProvider()  # 获取图层的数据提供者
        # 输出
        for index, pointline in enumerate(pointline_list):
            geom = QgsGeometry.fromWkt(pointline)  # 从 WKT 转换为几何对象
            if geom.isGeosValid():
                feature = QgsFeature()  # 创建新特征
                feature.setGeometry(geom)  # 设置几何对象
                provider.addFeatures([feature])  # 将特征添加到数据提供者

            else:
                print(index, '不是wkt')
                try:
                    # 替换中文逗号为英文逗号
                    output_string = pointline.replace("，", ",")
                    output_stringlines = output_string.split(';')
                    pointslines = []
                    istrue = True
                    for line in output_stringlines:
                        try:
                            lon, lat = map(float, line.split(','))  # 转换为浮点数
                            point1 = QgsPointXY(lon, lat)
                            pointslines.append(point1)
                        except ValueError:
                            istrue = False
                    # 如果其中有一个经纬度错误

                    if istrue:
                        geom = QgsGeometry.fromPolygonXY([pointslines])
                        if geom.isGeosValid():  # 检查几何对象的有效性
                            feature = QgsFeature()  # 创建新特征
                            feature.setGeometry(geom)  # 设置几何对象
                            provider.addFeatures([feature])  # 将特征添加到数据提供者
                except Exception as e:
                    print(index,e)
                    continue

        QgsProject.instance().addMapLayer(layer, True)
        iface.mapCanvas().refresh()

    @staticmethod
    def is_wkt(geom_string):
        # 定义WKT的正则表达式
        wkt_regex = re.compile(
            r'^\s*(POINT|LINESTRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON)\s*\(\s*'
            r'((\(\s*'
            r'((-?\d+(\.\d+)?\s+(-?\d+(\.\d+)?)(,\s*)?)+)\s*\)(,\s*)?)+|'
            r'((-?\d+(\.\d+)?\s+(-?\d+(\.\d+)?)(,\s*)?)+|'
            r'(?:(\(\s*([-+]?\d+(\.\d+)?\s+[-+]?\d+(\.\d+)?(\s*,\s*)?)+\s*\))\s*))'
            r')\)\s*$'
        )
        return bool(wkt_regex.match(geom_string))
