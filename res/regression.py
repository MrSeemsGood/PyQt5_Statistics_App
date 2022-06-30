from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import patsy

class ChooseVariablesWindow(QWidget):
    def __init__(self, parent, choices):
        super().__init__()
        self.parent = parent
        self.choices = choices
        
        self.initAppear()
        self.initUI()
        self.initConnects()

        self.show()

    def initAppear(self):
        self.setWindowTitle("Regression")
        self.resize(300, 250)
        self.move(400, 300)

    def initUI(self):
        self.vlayout = QVBoxLayout()

        self.yLabel = QLabel("Dependent variable")
        self.yComboBox = QComboBox()
        self.yComboBox.addItems(self.choices)

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
                    self.parent.buildRegression(x=[el.strip() for el in self.xLineEdit.text().split(',')], 
                                                y=self.yComboBox.currentText(), rgType="normal")
                
                    self.hide()
                except patsy.PatsyError:
                    qb = QMessageBox(self)
                    qb.setIcon(QMessageBox.Warning)
                    qb.setText("No independent variables with specified names found!")
                    qb.setWindowTitle("Warning")

                    qb.exec_()

            elif self.rgrBackward.isChecked():
                self.parent.buildRegression(x=self.parent.data.columns, y=self.yComboBox.currentText(), rgType="backward")
                self.hide()
            elif self.rgrForward.isChecked():
                self.parent.buildRegression(x=self.parent.data.columns, y=self.yComboBox.currentText(), rgType="forward")   
                self.hide()
