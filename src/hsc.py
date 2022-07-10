from venv import create
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from statsmodels.formula.api import ols
from statsmodels.stats.api import het_goldfeldquandt
from statsmodels.regression.linear_model import OLS

import matplotlib as mpl
import matplotlib.pyplot
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from scipy.stats import norm, kstest, spearmanr, f
import numpy as np
import pandas as pd

from icons import *

def createMsgBox(text="???", iconType=QMessageBox.Information):
    qb = QMessageBox()
    qb.setIcon(iconType)
    qb.setText(text)
    qb.setWindowTitle("Results")

    qb.exec_()

class HeteroskedasticityAnalysisWindow(QWidget):
    def __init__(self, parent, data, model=None):
        super().__init__()
        self.parent = parent
        self.data = data
        self.model = model
        
        self.initAppear()
        self.initUI()
        self.initConnects()

        self.show()

    def initAppear(self):
        self.setWindowTitle("Heteroscedasticity")
        self.resize(700, 700)
        self.move(300, 150)

    def initUI(self):
        self.vl = QVBoxLayout()
        self.hl = QHBoxLayout()
        self.lbl = QLabel()
        self.combo = QComboBox()
        self.combo.addItems(self.data.columns)

        self.scrollArea = QScrollArea()
        self.scrollContents = QWidget()
        self.scrollLayout = QVBoxLayout()

        self.targetVar = "???"
        self.targetResid = None
        maxK = -1

        #https://stackoverflow.com/questions/12234917/show-several-plots-in-a-scrollable-widget-with-pyqt-and-matplotlib
        for i in range(1, len(self.data.columns)):
            qfigWidget = QWidget()

            fig = matplotlib.pyplot.figure(figsize=(5.0, 4.0), dpi=100)
            canvas = FigureCanvas(fig)
            canvas.setParent(qfigWidget)
            toolbar = NavigationToolbar(canvas, qfigWidget)
            axes = fig.add_subplot(111)

            # adding an actual data to plots
            y, x = self.data.columns[0], self.data.columns[i]
            E = ols(formula=f"{y} ~ {x}", data=self.data).fit().resid
            X = [i for i in range(self.data.shape[0])]

            axes.grid()
            axes.plot(X, abs(E))

            z = np.polyfit(X, abs(E), 1) 
            p = np.poly1d(z)
            axes.set_title(f"|e| from {self.data.columns[i]}\n equation: y = {z[0]:6f}x + ({z[1]:6f})", fontsize=15)
            axes.plot(X, p(X), "r-")

            if abs(z[0]) > maxK:
                maxK = abs(z[0])
                self.targetVar = self.data.columns[i]
                self.targetResid = E

            # place plot components in a layout
            plotLayout = QVBoxLayout()
            plotLayout.addWidget(toolbar)
            plotLayout.addWidget(canvas)
            qfigWidget.setLayout(plotLayout)

            # prevent the canvas to shrink beyond a point
            # original size looks like a good minimum size
            canvas.setMinimumSize(canvas.size())

            self.scrollLayout.addWidget(qfigWidget)

        self.lbl.setText(f"Variable {self.targetVar} chosen automatically for heteroscedasticity analysis. If you wish, you can select another variable from the list below.")
        self.scrollContents.setLayout(self.scrollLayout)
        self.scrollArea.setWidget(self.scrollContents)

        self.buttons = [QPushButton("Spearman Test"), QPushButton("Goldfeld-Quant Test"), QPushButton("Gleyser Test")]

        for b in self.buttons:
            self.hl.addWidget(b)

        self.vl.addLayout(self.hl)
        self.vl.addWidget(self.lbl)
        self.vl.addWidget(self.combo)
        self.vl.addWidget(self.scrollArea)

        self.setLayout(self.vl)

        self.testResults = {"SPEARMAN" : False, "GQ" : (False, None), "GLEYSER" : False}

    def initConnects(self):
        self.buttons[0].clicked.connect(self.spearman)
        self.buttons[1].clicked.connect(self.goldfeldQuandt)
        self.buttons[2].clicked.connect(self.gleyser)
        self.combo.currentTextChanged.connect(self.comboChanged)

    def comboChanged(self):
        self.targetVar = self.combo.currentText()
        self.lbl.setText(f"Variable {self.targetVar} chosen manually for heteroscedasticity analysis. If you wish, you can select another variable from the list below.")
        self.targetResid = ols(formula=f"{self.data.columns[0]} ~ {self.targetVar}", data=self.data).fit().resid

    def spearman(self):
        _, pval = spearmanr(self.targetResid, self.data[self.targetVar])

        self.testResults['SPEARMAN'] = pval < 0.05

        createMsgBox(f"Spearman test results:\nFactual p-value = {pval:3f} vs critical = 0.05\n" +
                    ("No heteroskedasticity." if self.testResults['SPEARMAN'] == False else "Heteroskedasticity detected!"))

    def goldfeldQuandt(self):
        nobs, nvar = self.data.shape
        subSampleSize = round(3 * nobs / 8)
        gqFVal, _, _ = het_goldfeldquandt(
            y=self.data[self.data.columns[0]], 
            x=np.hstack([np.ones((self.data.shape[0], 1)), pd.DataFrame(self.data[self.targetVar])]), 
            idx=1, split=subSampleSize, drop=(nobs - 2 * subSampleSize)
            )
        gqFCrit = f.ppf(q=0.95, dfn=subSampleSize - nvar, dfd=subSampleSize - nvar)

        if gqFVal > gqFCrit:
            if gqFVal < 1.0:
                gqFVal = 1.0 / gqFVal
                self.testResults['GQ'] = (True, True)   #inverse proportional
            else:
                self.testResults['GQ'] = (True, False)  #proportional
        else:
            self.testResults['GQ'] = (False, None)
                
        createMsgBox(f"Goldfeld-Quandt test results:\nFactual F-statistic = {gqFVal:4f} vs critical F = {gqFCrit:4f}\n" +
                    ("No heteroskedasticity." if self.testResults['GQ'][0] == False else "Heteroskedasticity detected!" +
                    "\nResiduals are " + ("inverse " if self.testResults['GQ'][1] == True else "") + "proportional to the No. obs."))

    def gleyser(self):
        self.gleyserTestWindow = GleyserTestWindow(self, self.data)

class GleyserTestWindow(QWidget):
    def __init__(self, parent, data, model=None):
        super().__init__()
        self.parent = parent
        self.data = data
        self.model = model
        
        self.initAppear()
        self.initUI()
        self.initConnects()

        self.show()

    def initAppear(self):
        self.setWindowTitle("Heteroskedasticity")
        self.resize(860, 600)
        self.move(300, 150)
    
    def initUI(self):
        self.l = QVBoxLayout()

        self.gSamplesTWidget = QTableWidget()
        h, w = self.data.shape[0], 14
        self.gleyserSamples = np.zeros((h, w))

        self.gSamplesTWidget.setRowCount(h)
        self.gSamplesTWidget.setColumnCount(w)
        self.gSamplesTWidget.setFixedSize(850, 300)
        self.gSamplesTWidget.setHorizontalHeaderLabels(["1"] + ["γ = " + str((gamma - 6) / 2) for gamma in range(w)])

        for x in range(w):
            gamma = -3 + 0.5 * x
            for y in range(h):
                if x == 0:
                    val = 1
                else:
                    val = self.data[self.parent.targetVar].iloc[y - 1] ** gamma
                    
                self.gleyserSamples[y][x] = val
                self.gSamplesTWidget.setItem(y, x, QTableWidgetItem(str(val).strip(), 1)) 

        self.l.addWidget(self.gSamplesTWidget)

        self.gResultsTWidget = QTableWidget()
        h, w = 13, 7
        self.gleyserResults = np.zeros((h, w))

        self.gResultsTWidget.setRowCount(h)
        self.gResultsTWidget.setColumnCount(w)
        self.gResultsTWidget.setFixedSize(850, 300)
        self.gResultsTWidget.setHorizontalHeaderLabels(["γ", "b0", "b1", "F", "p-val", "R?", "Het-sk"])

        FVal_crit = f.ppf(q = 0.95, dfn = 1, dfd = self.data.shape[0] - 2)

        for y in range(h):
            gamma = -3 + 0.5 * y
            temp = OLS(abs(self.parent.targetResid), self.gleyserSamples[:, [0, y + 1]]).fit()
            self.gleyserResults[y][0] = gamma
            self.gResultsTWidget.setItem(y, 0, QTableWidgetItem(str(gamma).strip(), 1))
            self.gleyserResults[y][1] = temp.params[0]
            self.gResultsTWidget.setItem(y, 1, QTableWidgetItem(str(temp.params[0]).strip(), 1)) 
            self.gleyserResults[y][2] = temp.params[1]
            self.gResultsTWidget.setItem(y, 2, QTableWidgetItem(str(temp.params[1]).strip(), 1))
            self.gleyserResults[y][3] = temp.fvalue
            self.gResultsTWidget.setItem(y, 3, QTableWidgetItem(str(temp.fvalue).strip(), 1))
            self.gleyserResults[y][4] = temp.f_pvalue
            self.gResultsTWidget.setItem(y, 4, QTableWidgetItem(str(temp.f_pvalue).strip(), 1))
            self.gleyserResults[y][5] = temp.rsquared
            self.gResultsTWidget.setItem(y, 5, QTableWidgetItem(str(temp.rsquared).strip(), 1))

            self.gleyserResults[y][6] = self.gleyserResults[y][3] > FVal_crit
            self.gResultsTWidget.setItem(y, 6, QTableWidgetItem("Yes" if self.gleyserResults[y][3] > FVal_crit else "No", 1))

        if any(self.gleyserResults[:, 6]):
            self.parent.testResults["GLEYSER"] = True

        self.l.addWidget(self.gResultsTWidget)

        self.setLayout(self.l)

    def initConnects(self):
        pass


