from ctypes import alignment
from multiprocessing.sharedctypes import Value
from PyQt5.QtCore import Qt, QTimer, QTime, QLocale
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QFont
from PyQt5.QtWidgets import *

import os.path
import pandas as pd
import numpy as np
from statsmodels.formula.api import ols

def getCutoffString(t):
    t = str(t)
    if len(t) <= 12:
        return t
    else:
        return t[:9] + '...'

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initAppear()
        self.initUI()
        self.initConnects()
        self.show()

    def initAppear(self):
        self.setWindowTitle("Statistica at home")
        self.resize(1200, 800)
        self.move(200, 100)

    def initUI(self):
        self.uiobjects = {"lbl" : list(),
                          "btn" : list()}

        self.labels = self.uiobjects.get("lbl")
        self.buttons = self.uiobjects.get("btn")

        self.buttons.append(QPushButton("Open xlsx"))
        self.buttons.append(QPushButton("Multiple Regression"))

        self.grid = QGridLayout()
        self.tablePreview = [[QLineEdit("") for _ in range(13)] for _ in range(23)]    #preview is 23x13 (22x13 without headers)

        self.grid.addWidget(self.buttons[0], 1, 1, Qt.AlignLeft)
        self.grid.addWidget(self.buttons[1], 2, 1, Qt.AlignLeft)

        for x in range(2, 15):
            for y in range(2, 25):
                lbl = self.tablePreview[y - 2][x - 2]
                lbl.setStyleSheet("border-style: solid; border-width: 1px; border-color: black;")
                lbl.setFixedSize(80, (60 if y == 2 else 30))
                self.grid.addWidget(lbl, y, x)
        
        self.grid.setSpacing(0)
        self.setLayout(self.grid)

    def initConnects(self):
        self.buttons[0].clicked.connect(self.preXlsxOpen)
        self.buttons[1].clicked.connect(self.chooseVariables)

    def preXlsxOpen(self):
        # new window that suggest you select a spreadsheet from xlsx file and specify if row/column names are there
        preXlsxOpenWindow.show()

    def chooseVariables(self):
        try:
            chooseVariablesWindow.comboBox.addItems(self.data.columns)
            chooseVariablesWindow.show()
        except AttributeError:
            pass

    def fillTablePreview(self, d):
        self.clearTablePreview()
        h, w = d.shape
        h = min(h, 23)
        w = min(w, 13)

        for x in range(w):
            self.tablePreview[0][x].setText(getCutoffString(d.columns[x]))
            for y in range(h - 1):
                self.tablePreview[y + 1][x].setText(getCutoffString(d.iloc[y, x]))
        self.data = d

    def clearTablePreview(self):
        for x in range(13):
            for y in range(23):
                self.tablePreview[y][x].setText("")
        self.data = None

    def buildRegression(self, x, y):
        formula = "{} ~ {}".format(y, "+".join(x))
        model = ols(formula = formula, data = self.data).fit()
        #print(model.summary())
        #TODO make it so that it's visible in the app


class PreXlsxOpenWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initAppear()
        self.initUI()
        self.initConnects()

    def initAppear(self):
        self.setWindowTitle("Options")
        self.resize(400, 200)
        self.move(400, 300)

    def initUI(self):
        self.vlayout = QVBoxLayout()
        self.hlayouts = [QHBoxLayout(), QHBoxLayout(), QHBoxLayout()]
        self.sheetLabel = QLabel("Specify spreadsheet number or name:")
        self.sheetInput = QLineEdit("")
        self.rownamesYN = QCheckBox("Table contains row names")
        self.rownamesYN.setChecked(True)
        self.openButton = QPushButton("Open")
        self.openButton.setFixedSize(80, 30)

        self.hlayouts[0].addWidget(self.sheetLabel, Qt.AlignLeft)
        self.hlayouts[0].addWidget(self.sheetInput, Qt.AlignRight)
        self.hlayouts[1].addWidget(self.rownamesYN, Qt.AlignLeft)
        self.hlayouts[2].addWidget(self.openButton, Qt.AlignCenter)

        for i in range(3):
            self.vlayout.addLayout(self.hlayouts[i])

        self.setLayout(self.vlayout)

    def initConnects(self):
        self.openButton.clicked.connect(self.openXlsx)

    def openXlsx(self):
        fname = QFileDialog.getOpenFileName(self, 'Open XLSX', '', "(*.xlsx);; (*.*)", "(*.xlsx)", QFileDialog.ReadOnly)[0]

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
            data = pd.read_excel(fname, sheet, header = 0)
            if not self.rownamesYN.isChecked():
                data = pd.DataFrame({"No. obs" : [i + 1 for i in range(data.shape[0])]}).join(data)
            mainWindow.fillTablePreview(data)

class ChooseVariablesWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.choice = list()
        
        self.initAppear()
        self.initUI()
        self.initConnects()

    def initAppear(self):
        self.setWindowTitle("Choose Variables")
        self.resize(400, 400)
        self.move(400, 300)

    def initUI(self):
        self.vlayout = QVBoxLayout()

        self.yLabel = QLabel("Dependent variable:")
        self.comboBox = QComboBox()

        self.xLabel = QLabel("Independent variables (separated by ','):")
        self.xLineEdit = QLineEdit("")

        self.performButton = QPushButton("Perform")

        self.vlayout.addWidget(self.yLabel)
        self.vlayout.addWidget(self.comboBox)
        self.vlayout.addWidget(self.xLabel)
        self.vlayout.addWidget(self.xLineEdit)
        self.vlayout.addWidget(self.performButton)
        self.setLayout(self.vlayout)

    def initConnects(self):
        self.performButton.clicked.connect(self.perform)

    def perform(self):
        mainWindow.buildRegression(x = [el.strip() for el in self.xLineEdit.text().split(',')], y = self.comboBox.currentText())
        self.hide()



app = QApplication([])
mainWindow = MainWindow()
preXlsxOpenWindow = PreXlsxOpenWindow()
chooseVariablesWindow = ChooseVariablesWindow()
app.exec_()