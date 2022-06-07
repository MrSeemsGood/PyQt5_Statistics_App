from ctypes import alignment
from multiprocessing.sharedctypes import Value
from PyQt5.QtCore import Qt, QTimer, QTime, QLocale, QRect
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QFont, QIcon
from PyQt5.QtWidgets import *

import os.path
import pandas as pd
import numpy as np
from statsmodels.formula.api import ols

main_window_base_size = (10, 10)
main_window_hidden_size = (25, 15)

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

        self.vl = QVBoxLayout()

        self.buttons.append(QPushButton("Open xlsx"))
        self.buttons.append(QPushButton("Multiple Regression"))
        for b in self.buttons:
            b.setFixedSize(160, 40)
            self.vl.addWidget(b, Qt.AlignLeft)

        self.tabs = []
        self.initPreviewUI()

        self.tabs.append(self.tablePreview)
        self.vl.addWidget(self.tablePreview)

        self.setLayout(self.vl)

    def initPreviewUI(self):
        self.tablePreview = QScrollArea()
        self.prevWidget = QWidget()
        self.scrollGrid = QGridLayout()
        self.clearTablePreview()
        self.scrollGrid.setSpacing(0)
        
        self.prevWidget.setLayout(self.scrollGrid)

        self.tablePreview.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tablePreview.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tablePreview.setWidgetResizable(True)
        self.tablePreview.setWidget(self.prevWidget)

    def fillTablePreview(self, d):
        self.clearTablePreview()
        h, w = d.shape

        for x in range(w):
            for y in range(h + 1):
                if y == 0:
                    lb = QLineEdit(getCutoffString(d.columns[x]))
                else:
                    lb = QLineEdit(getCutoffString(d.iloc[y - 1, x]))
                lb.setStyleSheet("border-style: solid; border-width: 1px; border-color: black;")
                lb.setFixedSize(100, 35)
                self.scrollGrid.addWidget(lb, y, x)

        self.data = d

    def clearTablePreview(self):
        # method taken from SO: https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        for i in reversed(range(self.scrollGrid.count())): 
            widgetToRemove = self.scrollGrid.itemAt(i).widget()
            # remove it from the layout list
            self.scrollGrid.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)
        #

        for id in range(100):
            lb = QLineEdit("")
            lb.setStyleSheet("border-style: solid; border-width: 1px; border-color: black;")
            lb.setFixedSize(100, 35)
            self.scrollGrid.addWidget(lb, id // 10, id % 10)

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
            qb = QMessageBox(self)
            qb.setIcon(QMessageBox.Warning)
            qb.setText("No table found in preview; load data before performing analysis!")
            qb.setWindowTitle("Warning")

            qb.exec_()

    def buildRegression(self, x, y):
        formula = "{} ~ {}".format(y, "+".join(x))
        model = ols(formula = formula, data = self.data).fit()
        print(model.summary())
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
        self.openButton = QPushButton("Choose File...")
        self.openButton.setFixedSize(120, 30)

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
        
        self.initAppear()
        self.initUI()
        self.initConnects()

    def initAppear(self):
        self.setWindowTitle("Choose Variables")
        self.resize(250, 400)
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
        if self.xLineEdit.text() == "":
            qb = QMessageBox(self)
            qb.setIcon(QMessageBox.Warning)
            qb.setText("Choose independent variables!")
            qb.setWindowTitle("Warning")

            qb.exec_()
        else:
            mainWindow.buildRegression(x = [el.strip() for el in self.xLineEdit.text().split(',')], y = self.comboBox.currentText())
            self.hide()


app = QApplication([])
mainWindow = MainWindow()
preXlsxOpenWindow = PreXlsxOpenWindow()
chooseVariablesWindow = ChooseVariablesWindow()
app.exec_()