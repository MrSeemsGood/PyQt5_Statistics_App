from PyQt5.QtCore import Qt, QTimer, QTime, QLocale, QRect
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QFont, QIcon, QGuiApplication, QPixmap
from PyQt5.QtWidgets import *
from PyQt5 import sip

import os.path
import patsy
import pandas as pd
import numpy as np
from statsmodels.formula.api import ols

import matplotlib.pyplot as plt 
from scipy.stats import norm, kstest 
from numpy import arange

app_g = QGuiApplication([])
icons = {
    "CHOOSE_LANG" : QIcon(QPixmap("icons/language_icon.png")),
    "OPEN_FILE" : QIcon(QPixmap("icons/excel.png")),
    "HISTOGRAM" : QIcon(QPixmap("icons/histogram.png"))
}

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

def getFileNameFromPath(p):
    p = str(p)
    while p.find("/") != -1:
        p = p[p.find("/") + 1:]

    return p

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

        self.buttons = (QPushButton(icons.get("OPEN_FILE"), "Open File"), QPushButton("Multiple Regression"), QPushButton("Residuals"),
                        QPushButton(icons.get("CHOOSE_LANG"), " CHANGE LANGUAGE (TBD)"),)
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
        self.buttons[3].clicked.connect(self.chooseLanguage)

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
        preXlsxOpenWindow.show()

    def residualAnalysis(self):
        try:
            residualAnalysisWindow.residuals = self.model.resid
            residualAnalysisWindow.show()
        except AttributeError:
            qb = QMessageBox(self)
            qb.setIcon(QMessageBox.Warning)
            qb.setText("Perform regressive analysis before analyzing residuals!")
            qb.setWindowTitle("Warning")

            qb.exec_()

    def chooseVariables(self):
        try:
            chooseVariablesWindow.yComboBox.addItems(self.data.columns)
            chooseVariablesWindow.show()
        except AttributeError:
            qb = QMessageBox(self)
            qb.setIcon(QMessageBox.Warning)
            qb.setText("Load data before performing analysis!")
            qb.setWindowTitle("Warning")

            qb.exec_()

    def buildRegression(self, x, y, rgType="normal"):
        if rgType == "normal":
            model = ols(formula="{} ~ {}".format(y, "+".join(x)), data=self.data).fit()
        elif rgType == "backward":
            model = forward_selected(self.data, y)
        elif rgType == "forward":
            model = backward_elimination(self.data, y)

        self.model = model
        self.addTab("Results", 
                    pd.concat([pd.DataFrame(model.summary().tables[0]), pd.DataFrame(model.summary().tables[1])]), setFocus=False)

class ResidualAnalysisWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initAppear()
        self.initUI()
        self.initConnects()

    def initAppear(self):
        self.setWindowTitle("Residuals")
        self.resize(400, 175)
        self.move(400, 300)

    def initUI(self):
        self.vlayout = QVBoxLayout()
        self.buttons = (QPushButton("Load to new tab"), QPushButton(icons.get("HISTOGRAM"), "Histogram + N(a; b) curve"),
                        QPushButton("Durbin-Watson statistic"))

        self.setLayout(self.vlayout)

        for b in self.buttons:
            self.vlayout.addWidget(b, alignment=Qt.AlignLeft)

    def initConnects(self):
        self.buttons[0].clicked.connect(lambda: mainWindow.addTab("Residuals", self.residuals, False, False))
        self.buttons[1].clicked.connect(self.drawHistogram)

    def drawHistogram(self):
        plt.figure(figsize=(9, 6))

        histData = plt.hist(self.residuals)

        range_ = arange(min(self.residuals), max(self.residuals), 0.05) 
        normalityCurve = norm(self.residuals.mean(), self.residuals.std())
        #? why does this exist?
        coefY = len(self.residuals) * max([1, (max(histData[0]) // (normalityCurve.pdf(self.residuals.mean()) * len(self.residuals)))])
        plt.plot(range_, [normalityCurve.pdf(x) * coefY for x in range_], color="r")

        plt.xticks(histData[1])

        KS_maxD, KS_PValue = kstest(self.residuals, cdf="norm", args=(self.residuals.mean(), self.residuals.std()))

        plt.title("Histogram of the distribution of regression residues\n" +
                    "Distribution: Normal\n" +
                    "Kolmogorov-Smirnov test = {:.5}, p-value = {:.5}".format(KS_maxD, KS_PValue), fontsize=18)

        plt.ylabel("No. of observations", fontsize=15) 
        plt.xlabel("Category (upper limits)", fontsize=15) 

        plt.grid()
        plt.show()

class PreXlsxOpenWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initAppear()
        self.initUI()
        self.initConnects()

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
            data = pd.read_excel(fname, sheet, header = 0)
            mainWindow.data = data

            if self.rownamesYN.isChecked():
                data = pd.DataFrame({"No. obs" : [i + 1 for i in range(data.shape[0])]}).join(data)

            name = self.customNameInput.text()

            mainWindow.addTab(getFileNameFromPath(fname) if name == "" else name, data, True, self.overwriteYN.isChecked())


class ChooseVariablesWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.initAppear()
        self.initUI()
        self.initConnects()

    def initAppear(self):
        self.setWindowTitle("Regression")
        self.resize(300, 250)
        self.move(400, 300)

    def initUI(self):
        self.vlayout = QVBoxLayout()

        self.yLabel = QLabel("Dependent variable")
        self.yComboBox = QComboBox()

        self.rgrBackward = QRadioButton("Backward stepwise")
        self.rgrForward = QRadioButton("Forward stepwise")
        self.rgrNormal = QRadioButton("Standard regression")

        self.xLineEdit = QLineEdit("Independent variables (separated by ,)")
        self.xLineEdit.setDisabled(True)

        self.performButton = QPushButton("Perform")

        self.vlayout.addWidget(self.yLabel)
        self.vlayout.addWidget(self.yComboBox)
        self.vlayout.addWidget(self.rgrBackward)
        self.vlayout.addWidget(self.rgrForward)
        self.vlayout.addWidget(self.rgrNormal)
        self.vlayout.addWidget(self.xLineEdit)
        self.vlayout.addWidget(self.performButton)

        self.setLayout(self.vlayout)

    def initConnects(self):
        self.performButton.clicked.connect(self.perform)
        self.rgrNormal.toggled.connect(self.handleRadioButton)

    def handleRadioButton(self):
        self.xLineEdit.setDisabled(not self.rgrNormal.isChecked())
        self.xLineEdit.setText("")

    def perform(self):
        if self.xLineEdit.text() == "" and self.rgrNormal.isChecked():
            qb = QMessageBox(self)
            qb.setIcon(QMessageBox.Warning)
            qb.setText("Specify independent variables!")
            qb.setWindowTitle("Warning")

            qb.exec_()
        else:
            if self.rgrNormal.isChecked():
                try:
                    mainWindow.buildRegression(x=[el.strip() for el in self.xLineEdit.text().split(',')], 
                                                y=self.yComboBox.currentText(), rgType="normal")
                
                    self.hide()
                except patsy.PatsyError:
                    qb = QMessageBox(self)
                    qb.setIcon(QMessageBox.Warning)
                    qb.setText("No independent variables with specified names found!")
                    qb.setWindowTitle("Warning")

                    qb.exec_()
            #TODO make it so that "No. obs" column isn't included when doing these
            elif self.rgrBackward.isChecked():
                mainWindow.buildRegression(x=mainWindow.data.columns, y=self.yComboBox.currentText(), rgType="backward")
                self.hide()
            elif self.rgrForward.isChecked():
                mainWindow.buildRegression(x=mainWindow.data.columns, y=self.yComboBox.currentText(), rgType="forward")   
                self.hide()

app = QApplication([])
mainWindow = MainWindow()
preXlsxOpenWindow = PreXlsxOpenWindow()
chooseVariablesWindow = ChooseVariablesWindow()
residualAnalysisWindow = ResidualAnalysisWindow()
app.exec_()
