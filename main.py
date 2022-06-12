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

def getCutoffString(t, length=15):
    t = str(t).strip()
    if len(t) <= length:
        return t
    else:
        return t[:length - min(3, len(t) - length)] + '...'

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
        self.vl = QVBoxLayout()
        self.hl = QHBoxLayout()

        self.buttons = (QPushButton("Open xlsx"), QPushButton("Analysis"))
        for b in self.buttons:
            b.setFixedSize(160, 40)
            self.hl.addWidget(b, alignment=Qt.AlignLeft)

        self.tabs = []
        self.tabWindow = QTabWidget()
        self.addTab()

        self.vl.addLayout(self.hl)
        self.vl.addWidget(self.tabWindow)
        self.setLayout(self.vl)

    def addTab(self, tabName = "New Tab", data = None, setFocus = True):
        newFrame = QFrame()
        newVLayout = QVBoxLayout()
        newScrollArea = QScrollArea()
        newWidget = QWidget()
        newGrid = QGridLayout()

        if data is None:
            self.clearGrid(newGrid)
        else:
            #fill new tab with data
            self.fillGrid(data, newGrid)

        newGrid.setSpacing(0)
        newWidget.setLayout(newGrid)
        newScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        newScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        newScrollArea.setWidgetResizable(False)
        newScrollArea.setWidget(newWidget)

        newVLayout.addWidget(newScrollArea)
        newFrame.setLayout(newVLayout)

        self.tabWindow.addTab(newFrame, tabName)
        self.tabs.append(newFrame)

        if setFocus:
            self.tabWindow.setCurrentWidget(newFrame)

    def fillGrid(self, d, grid):
        self.clearGrid(grid)
        h, w = d.shape

        for x in range(w):
            for y in range(h + 1):
                if y == 0:
                    lb = QLineEdit(getCutoffString(d.columns[x]))
                else:
                    lb = QLineEdit(getCutoffString(d.iloc[y - 1, x]))
                lb.setStyleSheet("border-style: solid; border-width: 0.75px; border-color: black;")
                lb.setFixedSize(100, 35)
                grid.addWidget(lb, y, x)

        self.data = d

    def clearGrid(self, grid):
        # method taken from SO: https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        for i in reversed(range(grid.count())): 
            widgetToRemove = grid.itemAt(i).widget()
            # remove it from the layout list
            grid.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)
        #

        for id in range(100):
            lb = QLineEdit("")
            lb.setStyleSheet("border-style: solid; border-width: 1px; border-color: black;")
            lb.setFixedSize(100, 35)
            grid.addWidget(lb, id // 10, id % 10)

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
        model = ols(formula=formula, data=self.data).fit()
        self.addTab("Results", pd.concat([pd.DataFrame(model.summary().tables[0]), pd.DataFrame(model.summary().tables[1])]), setFocus=False)


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
        self.hlayout = QHBoxLayout()
        self.hlayout2 = QHBoxLayout()
        self.sheetLabel = QLabel("Spreadsheet name/number:")
        self.sheetInput = QLineEdit("")
        self.rownamesYN = QCheckBox("Add row names (case number)")
        self.rownamesYN.setChecked(False)
        self.customNameLabel = QLabel("Custom name (optional):")
        self.customNameInput = QLineEdit("")
        self.openButton = QPushButton("Choose File...")
        self.openButton.setFixedSize(120, 30)

        self.hlayout.addWidget(self.sheetLabel, Qt.AlignLeft)
        self.hlayout.addWidget(self.sheetInput, Qt.AlignRight)
        self.vlayout.addLayout(self.hlayout)
        self.hlayout2.addWidget(self.customNameLabel, Qt.AlignLeft)
        self.hlayout2.addWidget(self.customNameInput, Qt.AlignRight)
        self.vlayout.addLayout(self.hlayout2)
        self.vlayout.addWidget(self.rownamesYN, Qt.AlignLeft)
        self.vlayout.addWidget(self.openButton, Qt.AlignCenter)

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
            if self.rownamesYN.isChecked():
                data = pd.DataFrame({"No. obs" : [i + 1 for i in range(data.shape[0])]}).join(data)

            name = self.customNameInput.text()

            mainWindow.addTab(fname[fname.find("/") + 1:] if name == "" else name, data, True)

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