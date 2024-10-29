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

from qgis._core import QgsProject, QgsVectorLayer, QgsPointXY, QgsGeometry, QgsFeature, QgsFillSymbol, \
    QgsSingleSymbolRenderer, QgsField, QgsRendererCategory, \
    QgsCategorizedSymbolRenderer, QgsFields, QgsPoint, QgsPolygon, QgsLineString
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'cyanlove_createpoint_base.ui'))


class cyanlove_createpoint(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(cyanlove_createpoint, self).__init__(parent)
        self.export_thread = None
        self.setupUi(self)
        self.setFloating(True)
        self.mQgsFileWidget.setFilter("*.csv;*.xlsx")
        self.setWindowFlags(QtCore.Qt.Dialog)  # 使对话框始终在前
        self.mQgsFileWidget.fileChanged.connect(self.selectfilepath)
        self.pushButton.clicked.connect(self.writer_point)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def update_label(self, value):
        self.label_2.setText(value)  # 更新值

    def selectfilepath(self):
        # 获取选择的文件路径
        filepath = self.mQgsFileWidget.filePath()
        if filepath:

            # 获取文件扩展名
            file_path = pathlib.Path(filepath)
            file_extension = file_path.suffix
            # 清除 comboBox 的现有选项
            self.comboBox.clear()
            self.comboBox_2.clear()

            if file_extension.lower() == '.csv':
                self.readcsvpath(filepath)
            if file_extension.lower() == '.xlsx':
                self.readexcelpath(filepath)
        else:
            self.label_2.setText("没有选择文件")

    def readcsvpath(self, csvpath: str):
        try:
            self.label_2.setText('')
            # 自动检测 CSV 文件的编码
            with open(csvpath, 'rb') as f:
                raw_data = f.read(2000)  # 读取前 1000 个字节
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                print(encoding)
            if encoding.lower() == 'gb2312':
                encoding = 'gbk'
            # 使用检测到的编码读取 CSV 文件的头部列
            df = pd.read_csv(csvpath, encoding=encoding, nrows=1)

            for column in df.columns:
                self.comboBox.addItem(column)
                self.comboBox_2.addItem(column)
        except Exception as e:
            self.label_2.setText(f"读取文件时出错: {e}")
            print(f"读取文件时出错: {e}")

    def readexcelpath(self, excelpath: str):
        try:
            self.label_2.setText('')
            df = pd.read_excel(excelpath, header=0, nrows=1)
            # 获取表头的所有值
            headers = df.columns.tolist()
            # 将表头的值添加到 comboBox
            self.comboBox.addItems(headers)
            self.comboBox_2.addItems(headers)
        except Exception as e:
            self.label_2.setText(f"读取文件时出错: {e}")
            print(f"读取文件时出错: {e}")

    def writer_point(self):

        excel_or_csv_path = self.mQgsFileWidget.filePath()
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        layname = 'SSJ_Cretepoint_' + timestamp

        if not layname and not excel_or_csv_path:
            self.label.setText("没有图层名称和文件路径")
            return
        elif not layname:
            self.label.setText("没有图层名称")
            return
        elif not excel_or_csv_path:
            self.label.setText("没有  文件路径")
            return
        lngcolumn = self.comboBox.currentText()
        latcolumn = self.comboBox_2.currentText()
        # 获取文件扩展名
        file_path = pathlib.Path(excel_or_csv_path)
        file_extension = file_path.suffix

        if file_extension.lower() == '.csv':
            # 自动检测 CSV 文件的编码
            with open(excel_or_csv_path, 'rb') as f:
                raw_data = f.read(2000)  # 读取前 1000 个字节
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                print(encoding)
            if encoding.lower() == 'gb2312':
                encoding = 'gbk'
            # 使用检测到的编码读取 CSV 文件

            df = pd.read_csv(excel_or_csv_path, encoding=encoding, header=0)
            self.writethread(df, layname, lngcolumn, latcolumn)

        if file_extension.lower() == '.xlsx':
            df = pd.read_excel(excel_or_csv_path, header=0)
            self.writethread(df, layname, lngcolumn, latcolumn)

    def writethread(self, df, layName, lngcolumn, latcolumn):

        print('开始线程...')
        layers = QgsProject.instance().mapLayersByName(layName)
        if layers:
            for layer in layers:
                QgsProject.instance().removeMapLayer(layer.id())

        layer = QgsVectorLayer("Point?crs=EPSG:4326", layName, "memory")

        # 启动导出线程
        self.export_thread = ExportThread(df, layer, lngcolumn, latcolumn)
        self.export_thread.updatelabel.connect(self.update_label)
        self.export_thread.layerAdded.connect(lambda: QgsProject.instance().addMapLayer(layer, True))
        self.export_thread.layerAdded.connect(iface.mapCanvas().refresh)
        self.export_thread.start()  # 启动线程


class ExportThread(QThread):
    progress = pyqtSignal(int)  # 声明一个进度信号
    layerAdded = pyqtSignal()  # 声明一个图层新增信号
    updatelabel = pyqtSignal(str)  # 声明一个更新label新增信号

    def __init__(self, dfs, layers, lngcolumns, latcolumns):
        super().__init__()  # 初始化父类
        self.df = dfs  # 存储数据框
        self.layer = layers  # QGIS 图层
        self.lngcolumn = lngcolumns
        self.latcolumn = latcolumns

    def run(self):
        countdf = len(self.df)  # 获取数据框的行数
        provider = self.layer.dataProvider()  # 获取图层的数据提供者

        fields = QgsFields()  # 创建字段集合
        # 添加属性字段到字段集合
        for column in self.df.columns:
            fields.append(QgsField(column, QVariant.String))  # 添加字符串类型字段

        provider.addAttributes(fields)  # 将字段添加到数据提供者
        self.layer.updateFields()  # 更新图层的字段

        # 遍历数据框中的每一行
        for index, row in self.df.iterrows():
            alngcolumn = row[self.lngcolumn]  # 获取选定经度列
            alatcolumn = row[self.latcolumn]  # 获取选定经度列
            try:
                # 创建 QgsPointXY 对象
                point = QgsPointXY(alngcolumn, alatcolumn)
                geom = QgsGeometry.fromPointXY(point)  # 从 WKT 转换为几何对象
                # 检查几何对象的有效性
                if geom.isGeosValid():
                    feature = QgsFeature(fields)  # 创建新特征
                    feature.setGeometry(geom)  # 设置几何对象
                    # 填充属性字段的数据
                    for column in self.df.columns:
                        feature[column] = row[column]  # 填充特征属性

                    provider.addFeatures([feature])  # 将特征添加到数据提供者

                else:
                    self.updatelabel.emit(index, '不是wkt格式')
                    continue
                # 计算并发出进度信号
                progress_value = int((index + 1) / countdf * 100)  # 计算进度百分比
                self.updatelabel.emit(str(progress_value) + "%")  # 发出进度信号

            except Exception as e:
                self.updatelabel.emit(f"经纬度错误-行: {index}")

                print(f"经纬度错误-行: {index}")
                continue


        print('绘制完毕！')  # 完成处理
        self.layerAdded.emit()  # 发出图层新增信号
        self.updatelabel.emit('绘制完毕！')
