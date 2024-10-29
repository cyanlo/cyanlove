# -*- coding: utf-8 -*-
"""
/***************************************************************************
 cyanloveDockWidget
                                 A QGIS plugin
 申少军的工具箱
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-10-19
        git sha              : $Format:%H$
        copyright            : (C) 2024 by cyan
        email                : shenshaojun@139.com
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
import sqlite3
from .cyanlove_readconfig import *
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt import QtWidgets, uic, QtCore
from qgis.PyQt.QtCore import pyqtSignal

from qgis._core import QgsProject, QgsVectorLayer, QgsPointXY, QgsGeometry, QgsFeature, QgsFillSymbol, \
    QgsSingleSymbolRenderer, QgsField, QgsRendererCategory, \
    QgsCategorizedSymbolRenderer
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'cyanlove_dockwidget_base.ui'))

# 配置文件int格式
pathsaveint = os.path.join(os.path.dirname(__file__), 'config.ini')


class cyanloveDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):

        super(cyanloveDockWidget, self).__init__(parent)
        self.setupUi(self)
        self.setFloating(True)
        self.setWindowFlags(QtCore.Qt.Dialog)  # 使对话框始终在前
        self.toolButton.clicked.connect(self.dropbutton)
        self.toolButton_2.clicked.connect(self.GetNeightCell)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def dropbutton(self):
        cgi = self.textEdit.toPlainText()
        self.shenshaojunSet(cgi)

    def shenshaojunSet(self, cgistr: str):
        tbname = "[TB_栅格9月CELL]"

        query = """SELECT cgi,cgi_name,gh,gpscenterlng,gpscenterlat,cnt_rsrp,cnt_rsrp110
                   FROM """ + tbname + """
                   WHERE cgi='""" + cgistr + """'
                   AND cast(cnt_rsrp as double)>=20
                   AND cast(cnt_rsrp110 as double)/cast(cnt_rsrp as double)<0.8"""

        self.GetFeatures(query, "SSJ_SG", 'red')

        query = """SELECT cgi,cgi_name,gh,gpscenterlng,gpscenterlat,cnt_rsrp,cnt_rsrp110
                                  FROM """ + tbname + """
                                  WHERE cgi='""" + cgistr + """'
                                  AND cast(cnt_rsrp as double)>=20
                                  AND cast(cnt_rsrp110 as double)/cast(cnt_rsrp as double)>=0.8"""
        self.GetFeatures(query, "SSJ_SG2", 'chartreuse')

    def GetFeatures(self, query: str, layName: str, FillColor: str):
        # SQLite 数据库文件路径
        try:
            db_path = readconfig.read_ini_file(pathsaveint, 'Settings', 'sqlite_栅格分析')

            # 连接到 SQLite 数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            # 获取查询结果
            results = cursor.fetchall()

            if not results:  # 如果结果为空
                self.label_2.setText('没有查询到数据！')
                return
            else:
                self.label_2.setText('有数据！')
            # 矩形的尺寸（单位：米）
            length = 19  # 矩形的长度
            width = 38  # 矩形的宽度
            # 获取所有图层
            layers = QgsProject.instance().mapLayersByName(layName)
            # 如果找到图层，则删除它
            if layers:
                for layer in layers:
                    # 从项目中移除图层
                    QgsProject.instance().removeMapLayer(layer.id())
            # 创建一个新的矢量图层
            layer = QgsVectorLayer("Polygon?crs=EPSG:4326", layName, "memory")
            provider = layer.dataProvider()

            center_lon1 = 0
            center_lat1 = 0
            k = 1

            # 打印结果
            for row in results:
                center_lon = float(row[3])
                center_lat = float(row[4])
                if k == 1:
                    center_lon1 = center_lon
                    center_lat1 = center_lat
                    # 小区名称显示
                    self.textEdit_2.setText(row[1])
                k = k + 1
                # 1度经度约为111320米，1度纬度约为110540米
                delta_lon = float(width / 111320)
                delta_lat = float(length / 110540)

                # 计算矩形的四个角点
                bottom_left = QgsPointXY(center_lon - delta_lon / 2, center_lat - delta_lat / 2)
                bottom_right = QgsPointXY(center_lon + delta_lon / 2, center_lat - delta_lat / 2)
                top_left = QgsPointXY(center_lon - delta_lon / 2, center_lat + delta_lat / 2)
                top_right = QgsPointXY(center_lon + delta_lon / 2, center_lat + delta_lat / 2)
                # 创建矩形的几何形状
                rect_geometry = QgsGeometry.fromPolygonXY(
                    [[bottom_left, bottom_right, top_right, top_left, bottom_left]])
                # 创建一个新特征并设置几何形状
                feature = QgsFeature()
                feature.setGeometry(rect_geometry)
                # 将特征添加到图层
                provider.addFeatures([feature])

            # 将图层添加到项目中
            root = QgsProject.instance().layerTreeRoot()
            QgsProject.instance().addMapLayer(layer, True)

            # 设置图层的颜色，内部填充为红色
            fill_symbol = QgsFillSymbol.createSimple({'color': '255,0,0,0',
                                                      'outline_color': FillColor,
                                                      'outline_width': '0.8',
                                                      'style': 'solid'})  # alpha 值范围 0-255，0 完全透明，255 不透明
            renderer = QgsSingleSymbolRenderer(fill_symbol)
            layer.setRenderer(renderer)

            # 获取图层数量
            layers = QgsProject.instance().mapLayers()
            layer_count = len(layers)

            # 设置试图到第一个点
            target_point = QgsPointXY(center_lon1, center_lat1)
            iface.mapCanvas().setCenter(target_point)
            # 更改图层顺序
            self.insertable(layName)
            # 刷新地图视图
            iface.mapCanvas().refresh()
            # 关闭连接
            cursor.close()
            conn.close()

        except Exception as e:
            self.label_2.setText(e)

    def GetNeightCell(self):
        tbname1 = "[TB_Neighbor]"
        tbname2 = "[TB_Cell]"
        cgistr = self.textEdit.toPlainText()
        split_cgistr = cgistr.split('-')
        if len(split_cgistr) != 2:
            self.label_2.setText('cgi填写错误！')
            return
        try:
            db_path = readconfig.read_ini_file(pathsaveint, 'Settings', 'sqlite_栅格分析')
            # 连接到 SQLite 数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            query = f"""            
                SELECT A.CellType,A.NodeBSet,CellIDSet,B.[LTE小区名称], B.边界P FROM 
                (
                    SELECT 'Scell' AS CellType,{split_cgistr[0]} AS NodeBSet,{split_cgistr[1]} as CellIDSet           
                    UNION ALL 
                    SELECT 'Ncell' AS CellType,Ncell_NodeB AS NodeBSet,Ncell_CellID as CellIDSet  
                    FROM {tbname1} WHERE Scell_NodeB ='{split_cgistr[0]}' AND Scell_CellID ='{split_cgistr[1]}'
                ) A 
                INNER JOIN {tbname2} B ON A.NodeBSet=B."LTE基站标识" AND A.CellIDSet=B."LTE小区标识";
            """

            cursor.execute(query)

            # 获取查询结果
            results = cursor.fetchall()

            if not results:  # 如果结果为空
                self.label_2.setText('没有查询到数据！')
                return
            else:
                self.label_2.setText('有数据！')

            # 获取当前地图画布的边界
            canvas = iface.mapCanvas()
            map_extent = canvas.extent()

            layer = self.create_polygon_layer('SSJ_SG3')
            linelayer = self.create_line_layer('SSJ_SG3_line')
            if not layer.isValid():
                self.label_2.setText('图层无效，无法创建！')
                return
            else:
                # 获取图层的数据提供者
                provider = layer.dataProvider()
                providerline = linelayer.dataProvider()
                # 添加属性字段 'name' 和 'cginame'
                provider.addAttributes([
                    QgsField('name', QVariant.String),
                    QgsField('cginame', QVariant.String)
                ])

                # 刷新属性表，必须有这个
                layer.updateFields()

                first_feature_geom = None  # 用于存储第一个要素的几何
                for row in results:
                    # 小区名称显示

                    # 创建一个新特征并设置几何形状
                    sid = row[0]
                    geomset = row[4]
                    rect_geometry = QgsGeometry.fromWkt(geomset)
                    feature = QgsFeature()
                    feature.setGeometry(rect_geometry)
                    feature.setAttributes([sid, '111'])  # 设置属性值为 'A' 和 '111'
                    # 将特征添加到图层
                    provider.addFeatures([feature])

                    # 检查第一个要素的几何
                    if first_feature_geom is None:
                        first_feature_geom = rect_geometry
                        self.textEdit_2.setText(row[3]) # 主小区名称
                    else:
                        # 检查要素是否在地图边界外
                        if not map_extent.intersects(rect_geometry.boundingBox()):
                            # 定义点坐标
                            points = [
                                QgsPointXY(first_feature_geom.centroid().asPoint()),
                                QgsPointXY(rect_geometry.centroid().asPoint())
                            ]
                            # 创建线几何
                            line_geom = QgsGeometry.fromPolylineXY(points)
                            line_feature = QgsFeature()
                            line_feature.setGeometry(line_geom)
                            providerline.addFeatures([line_feature])

                # 创建符号层，定义颜色
                categoryA = QgsRendererCategory('Scell', QgsFillSymbol.createSimple(
                    {'color': 'red', 'outline_color': 'black', 'outline_width': '0.5'}), 'Scell')
                categoryB = QgsRendererCategory('Ncell', QgsFillSymbol.createSimple(
                    {'color': 'blue', 'outline_color': 'black', 'outline_width': '0.5'}), 'Ncell')

                # 创建分类渲染器，使用 'name' 属性字段
                renderer = QgsCategorizedSymbolRenderer('name', [categoryA, categoryB])
                # 将渲染器应用到图层
                layer.setRenderer(renderer)

                # 添加图层
                QgsProject.instance().addMapLayer(layer, True)
                QgsProject.instance().addMapLayer(linelayer, True)
                # 更新界面
                self.label_2.setText('图层添加成功！')
                print('图层添加成功')

                print('ok')
                iface.mapCanvas().refresh()
                cursor.close()
                conn.close()
        except Exception as e:
            self.label_2.setText(str(e))

    def insertable(self, tbname: str):
        # 获取当前项目
        project = QgsProject.instance()
        tblist = project.mapLayers().values()
        countlayers = len(tblist)

        root = project.layerTreeRoot()
        # 获取表名称
        vl = QgsProject.instance().mapLayersByName(tbname)[0]

        myvl = root.findLayer(vl.id())

        myvlclone = myvl.clone()

        parent = myvl.parent()

        parent.insertChildNode(countlayers - 1, myvlclone)

        root.removeChildNode(myvl)

    def create_polygon_layer(self, layname: str):
        # 获取所有图层
        layers = QgsProject.instance().mapLayersByName(layname)

        # 如果找到图层，则删除它
        if layers:
            for layer in layers:
                # 从项目中移除图层
                QgsProject.instance().removeMapLayer(layer.id())

        # 创建一个新的矢量图层
        new_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", layname, "memory")

        # 检查图层是否有效
        if not new_layer.isValid():
            print(f"图层 '{layname}' 创建失败！")
            return None

        # 将新图层添加到项目
        QgsProject.instance().addMapLayer(new_layer)

        # 返回新创建的图层
        return new_layer

    def create_line_layer(self, layname: str):
        # 获取所有图层
        layers = QgsProject.instance().mapLayersByName(layname)

        # 如果找到图层，则删除它
        if layers:
            for layer in layers:
                # 从项目中移除图层
                QgsProject.instance().removeMapLayer(layer.id())

        # 创建一个新的矢量图层
        new_layer = QgsVectorLayer("LineString?crs=EPSG:4326", layname, "memory")

        # 检查图层是否有效
        if not new_layer.isValid():
            print(f"图层 '{layname}' 创建失败！")
            return None

        # 将新图层添加到项目
        QgsProject.instance().addMapLayer(new_layer)

        # 返回新创建的图层
        return new_layer
