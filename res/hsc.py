from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class HeteroscedasticityAnalysisWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.initAppear()
        self.initUI()
        self.initConnects()

        self.show()

    def initAppear(self):
        self.setWindowTitle("Heteroscedasticity")
        self.resize(300, 250)
        self.move(400, 300)

    def initUI(self):
        pass

    def initConnects(self):
        pass