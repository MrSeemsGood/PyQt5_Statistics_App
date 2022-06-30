from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from pandas import read_excel, DataFrame as df

def getFileNameFromPath(p):
    p = str(p)
    while p.find("/") != -1:
        p = p[p.find("/") + 1:]

    return p

class PreXlsxOpenWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.initAppear()
        self.initUI()
        self.initConnects()

        self.show()

    def initAppear(self):
        self.setWindowTitle("Launch options")
        self.resize(400, 200)
        self.move(400, 300)

    def initUI(self):
        self.vlayout = QVBoxLayout()
        self.hlayout = QHBoxLayout()
        self.hlayout2 = QHBoxLayout()
        self.sheetLabel = QLabel("Sheet label or name:")
        self.sheetInput = QLineEdit("")
        self.rownamesYN = QCheckBox("Add row names")
        self.rownamesYN.setChecked(True)
        self.overwriteYN = QCheckBox("Overwrite current tab")
        self.overwriteYN.setChecked(True)
        self.customNameLabel = QLabel("Custom sheet name (optional):")
        self.customNameInput = QLineEdit("")
        self.openButton = QPushButton("Open file...")
        self.openButton.setFixedSize(120, 30)

        self.hlayout.addWidget(self.sheetLabel, Qt.AlignLeft)
        self.hlayout.addWidget(self.sheetInput, Qt.AlignRight)
        self.vlayout.addLayout(self.hlayout)
        self.hlayout2.addWidget(self.customNameLabel, Qt.AlignLeft)
        self.hlayout2.addWidget(self.customNameInput, Qt.AlignRight)
        self.vlayout.addLayout(self.hlayout2)
        self.vlayout.addWidget(self.rownamesYN, Qt.AlignLeft)
        self.vlayout.addWidget(self.overwriteYN, Qt.AlignLeft)
        self.vlayout.addWidget(self.openButton, Qt.AlignCenter)

        self.setLayout(self.vlayout)

    def initConnects(self):
        self.openButton.clicked.connect(self.openXlsx)

    def openXlsx(self):
        fname = QFileDialog.getOpenFileName(self, 'Открыть .xlsx', '', "(*.xlsx);; (*.*)", "(*.xlsx)", QFileDialog.ReadOnly)[0]

        if fname:
            self.hide()
            sheet = self.sheetInput.text()
            if sheet == "":
                sheet = 0
            else:
                try:
                    sheet = int(sheet)
                except ValueError:
                    pass
            global data
            data = read_excel(fname, sheet, header = 0)
            self.parent.data = data

            if self.rownamesYN.isChecked():
                data = df({"No. obs" : [i + 1 for i in range(data.shape[0])]}).join(data)

            name = self.customNameInput.text()

            self.parent.addTab(getFileNameFromPath(fname) if name == "" else name, data, True, self.overwriteYN.isChecked())
