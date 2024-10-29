import os
import sqlite3

from PyQt5.QtWidgets import QFileDialog
from qgis.PyQt import uic, QtWidgets, QtCore

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'cyanlove_sqliteset_base.ui'))
# 相对导入方式，不能用import 否则会找不到模块，相对导入会从当前目录搜索
from .testssj import *
from .cyanlove_readconfig import *
from pathlib import Path

# 配置文件int格式
pathsaveint = os.path.join(os.path.dirname(__file__), 'config.ini')


class cyanlove_sqliteset(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()
    progress = pyqtSignal(int)  # 声明一个信号

    def __init__(self, parent=None):
        super(cyanlove_sqliteset, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.Dialog)  # 使对话框始终在前
        # 设置为模态窗口
        self.setWindowModality(QtCore.Qt.ApplicationModal)  # 或者使用 Qt.WindowModal
        self.toolButton.clicked.connect(self.open_file_dialog)
        self.toolButton_2.clicked.connect(self.write_sqlite_shangefenxi)
        self.toolButton_3.clicked.connect(self.read_sqlite_shangefenxi)
        self.toolButton_4.clicked.connect(self.crete_sqlite_shangefenxi)
        # 可选：如果你希望这个窗口在其他窗口前面显示
        self.raise_()

        print(os.path.dirname(__file__))

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def open_file_dialog(self):  # 定义打开文件对话框的方法
        options = QFileDialog.Options()  # 创建文件对话框选项
        options |= QFileDialog.ReadOnly  # 可以设置一些选项，例如只读
        file_name, _ = QFileDialog.getOpenFileName(self,
                                                   "选择文件",
                                                   "",
                                                   "SQLite文件 (*.db);;所有文件 (*)",  # 可以添加其他过滤器
                                                   options=options)  # 传递 options 参数
        if file_name:  # 检查用户是否选择了文件
            self.textEdit.setText(file_name)  # 更新标签的文本为选择的文件路径
        else:
            print("用户取消了文件选择")  # 处理取消选择的情况

    def crete_sqlite_shangefenxi(self):
        options = QFileDialog.Options()  # 创建文件对话框选项
        options |= QFileDialog.ReadOnly  # 可以设置一些选项，例如只读
        file_name, _ = QFileDialog.getSaveFileName(self,
                                                   "选择文件",
                                                   "",
                                                   "SQLite文件 (*.db);;所有文件 (*)",  # 可以添加其他过滤器
                                                   options=options)  # 传递 options 参数
        if file_name:  # 检查用户是否选择了文件
            db_path = file_name
            # 连接到 SQLite 数据库
            conn = sqlite3.connect(db_path)
            conn.close()
            self.label_2.setText("数据库创建成功！")
            self.textEdit.setText(file_name)
        else:
            self.label_2.setText("用户取消操作")  # 处理取消选择的情况

    def write_sqlite_shangefenxi(self):
        pathstr = self.textEdit.toPlainText()
        path = Path(pathstr)

        if path.is_file():
            readconfig.write_ini_file(pathsaveint, 'Settings', 'sqlite_栅格分析', pathstr)
            self.label_2.setText('配置成功!')
        else:
            self.label_2.setText('不是文件路径，请检查!')

    def read_sqlite_shangefenxi(self):
        p1 = readconfig.read_ini_file(pathsaveint, 'Settings', 'sqlite_栅格分析')
        self.textEdit.setText(p1)
