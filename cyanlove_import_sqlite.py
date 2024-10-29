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

from .cyanlove_readconfig import readconfig

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'cyanlove_import_sqlite_base.ui'))

# 配置文件int格式
pathsaveint = os.path.join(os.path.dirname(__file__), 'config.ini')


class cyanlove_import_sqlite(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(cyanlove_import_sqlite, self).__init__(parent)
        self.export_thread = None
        self.tbname = ''
        self.setupUi(self)
        self.setFloating(True)
        self.setWindowFlags(QtCore.Qt.Dialog)  # 使对话框始终在前
        self.radioButton_3.toggled.connect(self.toggleTextEdit)  # 小区表
        self.radioButton_2.toggled.connect(self.toggleTextEdit)  # 邻区表
        self.radioButton.toggled.connect(self.toggleTextEdit)  # 自定义表
        self.mQgsFileWidget.setFilter("*.csv;*.xlsx")
        self.pushButton.clicked.connect(self.import_csv_excel_sqlite_thread)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def update_label(self, value):
        self.label_2.setText(value)  # 更新值

    def toggleTextEdit(self):

        if self.radioButton_3.isChecked():
            self.textEdit.setDisabled(True)  # 禁用 QTextEdit
        elif self.radioButton_2.isChecked():
            self.textEdit.setDisabled(True)  # 禁用 QTextEdit
        else:
            self.textEdit.setEnabled(True)  # 启用 QTextEdit

    def import_csv_excel_sqlite_thread(self):
        # 获取选择的文件路径

        filepath = self.mQgsFileWidget.filePath()
        if filepath:
            if self.radioButton_3.isChecked():
                tbname = "TB_Cell"
            elif self.radioButton_2.isChecked():
                tbname = "TB_Neighbor"
            else:
                tbname = self.textEdit.toPlainText()

            if tbname.strip():  # 检查是否为空（strip()去除前后空白）
                # 启动导出线程
                self.export_thread = ExportThread(filepath, tbname)
                self.export_thread.updatelabel.connect(self.update_label)
                self.export_thread.start()  # 启动线程
            else:
                self.label_2.setText("没有表名称，请填写！")
        else:
            self.label_2.setText("没有选择文件")


class ExportThread(QThread):
    updatelabel = pyqtSignal(str)  # 声明一个更新label新增信号

    def __init__(self, filepaths, tbnames=None):
        super().__init__()  # 初始化父类
        self.filepath = filepaths
        self.tbname = tbnames

    def run(self):
        # 获取文件扩展名
        file_path = pathlib.Path(self.filepath)
        file_extension = file_path.suffix

        if file_extension.lower() == '.csv':
            self.readcsvpath(self.filepath)
        if file_extension.lower() == '.xlsx':
            self.readexcelpath(self.filepath)

    def readcsvpath(self, csvpath: str):
        try:
            self.updatelabel.emit('开始读取中...')
            # 自动检测 CSV 文件的编码

            with open(csvpath, 'rb') as f:
                raw_data = f.read(2000)  # 读取前 1000 个字节
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                print(encoding)
            if encoding.lower() == 'gb2312':
                encoding = 'gbk'
            db_path = readconfig.read_ini_file(pathsaveint, 'Settings', 'sqlite_栅格分析')
            # 连接到 SQLite 数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            query = f"drop table if exists [{self.tbname}]"
            print(query)
            cursor.execute(query)
            # 定义每个块的大小
            chunksize = 1000000  # 每次读取10000行
            # 使用迭代器读取CSV文件并逐块写入数据库
            for chunk in pd.read_csv(self.filepath, chunksize=chunksize, encoding=encoding):  # 指定编码
                chunk.to_sql(self.tbname, conn, if_exists='append', index=False)  # 追加插入
            print('ok')
            self.updatelabel.emit(f"写入完毕！")
            # 关闭连接
            conn.close()
        except Exception as e:
            self.updatelabel.emit(f"读取文件时出错: {e}")
            print(f"读取文件时出错: {e}")

    def readexcelpath(self, excelpath: str):
        try:
            self.updatelabel.emit('开始读取中...')
            db_path = readconfig.read_ini_file(pathsaveint, 'Settings', 'sqlite_栅格分析')
            # 连接到 SQLite 数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            df = pd.read_excel(excelpath, sheet_name=0)  # 使用0读取第一个工作表
            df.to_sql(self.tbname, conn, if_exists='replace', index=False)
            print('ok')
            self.updatelabel.emit(f"写入完毕！")
            # 关闭连接
            conn.close()
        except Exception as e:
            self.updatelabel.emit(f"读取文件时出错: {e}")
            print(f"读取文件时出错: {e}")
