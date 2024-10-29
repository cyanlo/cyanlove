import csv
import os
import pathlib
import sqlite3
import threading

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
    os.path.dirname(__file__), 'cyanlove_import_geometry_base.ui'))


class cyanlove_import_geometry(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(cyanlove_import_geometry, self).__init__(parent)
        self.setupUi(self)
        self.setFloating(True)
        self.setWindowFlags(QtCore.Qt.Dialog)  # 使对话框始终在前
        self.toolButton.clicked.connect(self.selectfilepath)
        self.pushButton.clicked.connect(self.writerpolygon)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def update_progress(self, value):
        self.progressBar.setValue(value)  # 更新进度条的值

    def update_label(self, value):
        self.label.setText(value)  # 更新值

    def selectfilepath(self):
        # 设置文件过滤器
        filters = "Excel Files (*.xlsx);;CSV Files (*.csv)"
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择文件", "", filters)
        if filepath is not None:
            self.textEdit.setText(filepath)
            # 获取文件扩展名
            file_path = pathlib.Path(filepath)
            file_extension = file_path.suffix
            # 清除 comboBox 的现有选项
            self.comboBox.clear()
            print((file_path, file_extension))
            if file_extension.lower() == '.csv':
                self.readcsvpath(filepath)
            if file_extension.lower() == '.xlsx':
                self.readexcelpath(filepath)

    def readcsvpath(self, csvpath: str):
        try:
            self.label.setText('')
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
        except Exception as e:
            self.label.setText(f"读取文件时出错: {e}")
            print(f"读取文件时出错: {e}")

    def readexcelpath(self, excelpath: str):
        try:
            df = pd.read_excel(excelpath, header=0, nrows=1)
            # 获取表头的所有值
            headers = df.columns.tolist()
            # 将表头的值添加到 comboBox
            self.comboBox.addItems(headers)
        except Exception as e:
            self.label.setText(f"读取文件时出错: {e}")
            print(f"读取文件时出错: {e}")

    def writerpolygon(self):

        excel_or_csv_path = self.textEdit.toPlainText()
        layName = self.textEdit_2.toPlainText()

        if not layName and not excel_or_csv_path:
            self.label.setText("没有图层名称和文件路径")
            return
        elif not layName:
            self.label.setText("没有图层名称")
            return
        elif not excel_or_csv_path:
            self.label.setText("没有  文件路径")
            return

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
            self.writethread(df, layName)

        if file_extension.lower() == '.xlsx':
            df = pd.read_excel(excel_or_csv_path, header=0)
            self.writethread(df, layName)

    def writethread(self, df, layName):
        selected_header = self.comboBox.currentText().strip()  # 同样去除前后空格
        # 清理列名
        df.columns = df.columns.str.strip()  # 去除前后空格

        # 检查选择的表头是否在 DataFrame 中
        if selected_header not in df.columns:
            self.label.setText("选择的列不在 Excel 文件中")
            return
        print('开始线程...')
        # 确保使用现有的进度条
        self.progressBar.setRange(0, 100)  # 设置进度条范围
        self.progressBar.setValue(0)  # 初始化进度条值
        self.progressBar.show()  # 显示进度条 (如果之前是隐藏状态)
        layers = QgsProject.instance().mapLayersByName(layName)
        if layers:
            for layer in layers:
                QgsProject.instance().removeMapLayer(layer.id())

        layer = QgsVectorLayer("Polygon?crs=EPSG:4326", layName, "memory")
        boolwkt = True
        if self.radioButton_2.isChecked():
            boolwkt = True
        if self.radioButton_2.isChecked():
            boolwkt = False

        # 启动导出线程
        self.export_thread = ExportThread(df, layer, selected_header, boolwkt)
        self.export_thread.progress.connect(self.update_progress)  # 连接信号到槽
        self.export_thread.updatelabel.connect(self.update_label)
        self.export_thread.layerAdded.connect(lambda: QgsProject.instance().addMapLayer(layer, True))
        self.export_thread.layerAdded.connect(iface.mapCanvas().refresh)
        self.export_thread.start()  # 启动线程


class ExportThread(QThread):
    progress = pyqtSignal(int)  # 声明一个进度信号
    layerAdded = pyqtSignal()  # 声明一个图层新增信号
    updatelabel = pyqtSignal(str)  # 声明一个更新label新增信号

    def __init__(self, dfs, layers, selected_headers, boolwkts):
        super().__init__()  # 初始化父类
        self.df = dfs  # 存储数据框
        self.boolwkt = boolwkts  # 是否使用 WKT 格式
        self.layer = layers  # QGIS 图层
        self.selected_header = selected_headers  # 选中的列名

    def run(self):
        countdf = len(self.df)  # 获取数据框的行数
        provider = self.layer.dataProvider()  # 获取图层的数据提供者
        print(self.boolwkt)
        fields = QgsFields()  # 创建字段集合
        # 添加属性字段到字段集合
        for column in self.df.columns:
            if column != self.selected_header:
                fields.append(QgsField(column, QVariant.String))  # 添加字符串类型字段

        provider.addAttributes(fields)  # 将字段添加到数据提供者
        self.layer.updateFields()  # 更新图层的字段

        # 遍历数据框中的每一行
        for index, row in self.df.iterrows():
            try:

                wkt = row[self.selected_header]  # 获取选定列的 WKT 内容

                if self.boolwkt:  # 处理 WKT 格式
                    geom = QgsGeometry.fromWkt(wkt)  # 从 WKT 转换为几何对象
                    # 检查几何对象的有效性
                    if geom.isGeosValid():

                        feature = QgsFeature(fields)  # 创建新特征
                        feature.setGeometry(geom)  # 设置几何对象
                        # 填充属性字段的数据
                        for column in self.df.columns:
                            if column != self.selected_header:
                                feature[column] = row[column]  # 填充特征属性

                        provider.addFeatures([feature])  # 将特征添加到数据提供者

                    else:
                        self.updatelabel.emit(index, '不是wkt格式')
                        continue


                else:  # 处理逗号和分号格式
                    points = []  # 存储点的列表
                    for pair in wkt.split(';'):  # 分割每一组坐标
                        lon, lat = map(float, pair.split(','))  # 转换为浮点数
                        points.append(QgsPointXY(lon, lat))  # 创建 QgsPoint 对象并添加到列表

                    if len(points) > 2:  # 确保至少有三个点构成多边形

                        geom = QgsGeometry.fromPolygonXY([points])

                        if geom.isGeosValid():  # 检查几何对象的有效性
                            feature = QgsFeature(fields)  # 创建新特征
                            feature.setGeometry(geom)  # 设置几何对象
                            # 填充属性字段的数据
                            for column in self.df.columns:
                                if column != self.selected_header:
                                    feature[column] = row[column]

                            provider.addFeatures([feature])  # 将特征添加到数据提供者

                    else:
                        print(f"无效的几何图形在索引 {index}: {wkt}")  # 打印无效几何信息
                        continue  # 继续循环
                        
            except Exception as e:
                self.updatelabel.emit(f"经纬度错误-行: {index}")
                print(f"经纬度错误-行: {index}")
                continue
            # 计算并发出进度信号
            progress_value = int((index + 1) / countdf * 100)  # 计算进度百分比
            self.progress.emit(progress_value)  # 发出进度信号

        print('绘制完毕！')  # 完成处理
        self.layerAdded.emit()  # 发出图层新增信号
        self.updatelabel.emit('绘制完毕！')
