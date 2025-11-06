from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import untitled
class my_window(QtWidgets.QMainWindow,untitled.Ui_MainWindow):
    def __init__(self):
        super(my_window, self).__init__()
        self.setupUi(self)
        #允许窗体接受拖拽
        self.setAcceptDrops(True)

    def dragEnterEvent(self, a0: QtGui.QDragEnterEvent) -> None:
        #判断有没有接受到内容
        if a0.mimeData().hasUrls():
            #如果接收到内容了，就把它存在事件中
            a0.accept()
        else:
            #没接收到内容就忽略
            a0.ignore()

    def dropEvent(self, a0: QtGui.QDropEvent) -> None:
        if a0:
            for i in a0.mimeData().urls():
                print(i.path())
                file_path = i.path()[1:]
                self.lineEdit.setText(file_path)



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = my_window()
    window.show()
    sys.exit(app.exec_())