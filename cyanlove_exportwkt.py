import csv
import os
import sqlite3

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QFileDialog, QProgressBar

from .cyanlove_readconfig import *
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt import QtWidgets, uic, QtCore
from qgis.PyQt.QtCore import pyqtSignal

from qgis._core import QgsProject, QgsVectorLayer, QgsPointXY, QgsGeometry, QgsFeature, QgsFillSymbol, \
    QgsSingleSymbolRenderer, QgsField, QgsRendererCategory, \
    QgsCategorizedSymbolRenderer
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'cyanlove_exportwkt_base.ui'))


class cyanlove_exportwkt(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(cyanlove_exportwkt, self).__init__(parent)
        self.export_thread = None
        self.setupUi(self)
        self.setFloating(True)
        self.setWindowFlags(QtCore.Qt.Dialog)  # 使对话框始终在前
        self.toolButton.clicked.connect(self.export_wkt)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def export_wkt(self, event):
        options = QFileDialog.Options()  # 创建文件对话框选项
        options |= QFileDialog.ReadOnly  # 可以设置一些选项，例如只读
        file_name, _ = QFileDialog.getSaveFileName(self,
                                                   "选择文件",
                                                   "",
                                                   "CSV文件 (*.csv);;所有文件 (*)",  # 可以添加其他过滤器
                                                   options=options)  # 传递 options 参数
        # 检查用户是否选择了文件
        if file_name:

            selected_layer = self.mMapLayerComboBox.currentLayer()
            if selected_layer is None:
                print("未选择有效图层!")
            else:
                print(f"选择的图层: {selected_layer.name()}")
                csv_file_path = file_name
                self.label_2.setText('开始导出.....')
                # 确保使用现有的进度条
                self.progressBar.setRange(0, 100)  # 设置进度条范围
                self.progressBar.setValue(0)  # 初始化进度条值
                self.progressBar.show()  # 显示进度条 (如果之前是隐藏状态)

                # 启动导出线程
                self.export_thread = ExportThread(selected_layer, csv_file_path)
                self.export_thread.progress.connect(self.update_progress)  # 连接信号到槽
                self.export_thread.finished.connect(self.export_finished)  # 导出完成后连接到槽
                self.export_thread.start()  # 启动线程


        else:
            print("用户取消了文件选择")  # 处理取消选择的情况

    def update_progress(self, value):
        self.progressBar.setValue(value)  # 更新进度条的值

    def export_finished(self):
        print("导出完成！")
        self.label_2.setText('导出完毕')
        self.progressBar.setValue(100)


class ExportThread(QThread):
    progress = pyqtSignal(int)  # 声明一个信号

    def __init__(self, selected_layer, csv_file_path):
        super().__init__()
        self.selected_layer = selected_layer
        self.csv_file_path = csv_file_path

    def run(self):
        # 获取字段名，并添加 WKT_BJ，字段名两边加上双引号
        field_names = [f"{field.name()}" for field in self.selected_layer.fields()] + ['WKT_BJ']

        # 获取要素总数以计算进度
        total_features = self.selected_layer.featureCount()

        with open(self.csv_file_path, mode='w', newline='', encoding='gbk') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(field_names)

            for index, feature in enumerate(self.selected_layer.getFeatures()):
                row = []
                for field_name in field_names[:-1]:  # 不包括 WKT_BJ
                    value = feature[field_name]  # 获取每个字段的值
                    row.append(f'{value}')  # 在每个值两边添加双引号

                # 计算边界的 WKT 并添加到行中
                boundary_wkt = feature.geometry().asWkt()
                row.append(f'{boundary_wkt}')  # 在 WKT_BJ 的值两边添加双引号

                writer.writerow(row)

                # 发送进度更新
                progress_value = int((index + 1) / total_features * 100)
                self.progress.emit(progress_value)
