from PyQt5.QtCore import Qt, QTimer, QTime, QLocale, QRect
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QFont, QIcon, QGuiApplication, QPixmap, QKeySequence
from PyQt5.QtWidgets import *
from PyQt5 import sip

import os.path
import pandas as pd
import numpy as np
import pylab
from statsmodels.formula.api import ols
app_g = QGuiApplication([])

from xlopen import *
from regression import *
from residuals import *
from hsc import *

from icons import *

def forward_selected(data, response):
    remaining = set(data.columns) 
    remaining.remove(response) 
    selected = []
    currentScore, bestNewScore = 0.0, 0.0 
    while remaining and currentScore == bestNewScore:
        scoresWithCandidates = [] 
        for candidate in remaining:
            score = ols(formula="{} ~ {}".format(response, " + ".join(selected + [candidate])), data=data).fit().rsquared_adj
            scoresWithCandidates.append((score, candidate))
        scoresWithCandidates.sort() 
        bestNewScore, bestCandidate = scoresWithCandidates.pop() 
        if currentScore < bestNewScore:
            remaining.remove(bestCandidate) 
            selected.append(bestCandidate) 
            currentScore = bestNewScore

    return ols(formula="{} ~ {}".format(response, " + ".join(sorted(selected))), data=data).fit()

def backward_elimination(data, response):
    selected = set(data.columns) 
    selected.remove(response) 
    currentPValues = ols(formula="{} ~ {}".format(response, " + ".join(selected)), data=data).fit().pvalues
    for _ in range(len(data.columns)): 
        currentAdjR2 = -1.0 
        if (max(currentPValues) >= 0.05):
            for i in range(1, len(currentPValues)):
                candidateToRemove = currentPValues.axes[0][i] 
                newModel = ols(formula="{} ~ {}".format(response, " + ".join(selected - set([candidateToRemove]))), data=data).fit()
                newAdjR2 = newModel.rsquared_adj 
                if (currentAdjR2 < newAdjR2):
                    currentAdjR2, deletedVar, improvedPValues = newAdjR2, candidateToRemove, newModel.pvalues
        if (currentAdjR2 == -1.0):
            break
        selected.remove(deletedVar) 
        currentPValues = improvedPValues
    return ols(formula="{} ~ {}".format(response, " + ".join(sorted(selected))), data=data). fit()

def warn(warnText="???"):
    qb = QMessageBox()
    qb.setIcon(QMessageBox.Warning)
    qb.setText(warnText)
    qb.setWindowTitle("Warning")

    qb.exec_()

def getText(language, wd, txt):
    pass


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

        self.buttons = (QPushButton(MyIcon.OPEN_XL.getQIcon(), "Open File"), QPushButton("Multiple Regression"), QPushButton("Residuals"),
                        QPushButton("Heteroscedasticity"), QPushButton("Create Empty Tab"),
                        QPushButton(MyIcon.CHOOSE_LANGUAGE.getQIcon(), "LANGUAGE"),)
        for b in self.buttons:
            self.hl.addWidget(b, alignment=Qt.AlignLeft)

        self.tabs = []
        self.tabWindow = QTabWidget()
        self.addTab()

        self.vl.addLayout(self.hl)
        self.vl.addWidget(self.tabWindow)
        self.setLayout(self.vl)

    def initConnects(self):
        self.buttons[0].clicked.connect(self.preXlsxOpen)
        self.buttons[1].clicked.connect(self.chooseVariables)
        self.buttons[2].clicked.connect(self.residualAnalysis)
        self.buttons[3].clicked.connect(self.hcdAnalysis)
        self.buttons[4].clicked.connect(lambda: self.addTab(setFocus = True, overwriteCurrent = False))
        self.buttons[5].clicked.connect(self.chooseLanguage)

        # create shortcuts
        self.shortcuts = (QShortcut(QKeySequence("Ctrl+X"), self), QShortcut(QKeySequence("Ctrl+R"), self), QShortcut(QKeySequence("Ctrl+D"), self))
        self.shortcuts[0].activated.connect(self.preXlsxOpen)
        self.shortcuts[1].activated.connect(self.chooseVariables)
        self.shortcuts[2].activated.connect(self.residualAnalysis)

    def addTab(self, tabName = "New Tab", data = None, setFocus = True, overwriteCurrent = False):
        if tabName == "New Tab": 
            tabName += str(len(self.tabs) + 1)

        if overwriteCurrent:
            newFrame = self.tabWindow.currentWidget()

            # https://stackoverflow.com/questions/26212106/remove-everything-from-a-frame-in-pyqt
            layout = newFrame.layout()
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.deleteLayout(item.layout())
                sip.delete(layout)
        else:
            newFrame = QFrame()
        
        newTable = QTableWidget()
        newVLayout = QVBoxLayout()
        newScrollArea = QScrollArea()

        if data is None:
            self.clearGrid(newTable)
        else:
            #fill new tab with data
            self.fillGrid(data, newTable)
            
        newScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        newScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        newScrollArea.setWidgetResizable(True)
        newScrollArea.setWidget(newTable)

        newVLayout.addWidget(newScrollArea)
        newFrame.setLayout(newVLayout)

        self.tabWindow.addTab(newFrame, tabName)
        self.tabs.append(newFrame)

        if setFocus:
            self.tabWindow.setCurrentWidget(newFrame)

    def fillGrid(self, d, table):
        self.clearGrid(table)

        if type(d) == pd.DataFrame:
            h, w = d.shape
            table.setColumnCount(w + 1)
            table.setRowCount(h + 1)

            for x in range(w):
                for y in range(h + 1):
                    if y == 0:
                        txt = str(d.columns[x]).strip()[:12]
                    else:
                        txt = str(d.iloc[y - 1, x]).strip()[:12]
                    
                    table.setItem(y, x, QTableWidgetItem(txt, 1))
        elif type(d) == pd.Series:
            h = d.shape[0]
            table.setColumnCount(2)
            table.setRowCount(h + 1)

            for y in range(h):
                txt = str(d.iloc[y]).strip()[:12]
                table.setItem(y, 0, QTableWidgetItem(txt, 1))

    def clearGrid(self, table):
        table.setRowCount(10)
        table.setColumnCount(10)

        for id in range(100):
            qw = QTableWidgetItem(type=1)
            table.setItem(id // 10, id % 10, qw)

    def chooseLanguage(self):
        pass

    def preXlsxOpen(self):
        # new window that suggest you select a spreadsheet from xlsx file and specify if row/column names are there
        self.preXlsxOpenWindow = PreXlsxOpenWindow(parent=self)

    def residualAnalysis(self):
        try:
            self.residualsWindow = ResidualAnalysisWindow(parent=self, resid=self.model.resid)
        except AttributeError:
            warn("Perform regression analysis before analyzing residuals!")

    def chooseVariables(self):
        try:
            self.regressionWindow = ChooseVariablesWindow(parent=self, choices=self.data.columns)
        except AttributeError:
            warn("Load data before performing analysis!")

    def buildRegression(self, x, y, rgType="normal"):
        if rgType == "normal":
            model = ols(formula="{} ~ {}".format(y, "+".join(x)), data=self.data).fit()
        elif rgType == "backward":
            model = forward_selected(self.data, y)
        elif rgType == "forward":
            model = backward_elimination(self.data, y)

        self.model = model
        self.addTab("Results", 
                    pd.concat([pd.DataFrame(model.summary().tables[0]), pd.DataFrame(model.summary().tables[1])]), setFocus=True)

    def hcdAnalysis(self):
        pass
        #TODO make this window

app = QApplication([])
mainWindow = MainWindow()
app.exec_()
