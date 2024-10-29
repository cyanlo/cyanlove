import time
from PyQt5.QtCore import QThread, pyqtSignal


class UpdateThread(QThread):
    update_signal = pyqtSignal(str)

    def run(self):
        for i in range(5):
            time.sleep(1)  # 模拟长时间运行的任务
            self.update_signal.emit(f"更新文本: {i}")  # 发出信号更新文本
