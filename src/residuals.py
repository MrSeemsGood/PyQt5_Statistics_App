from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

import matplotlib as mpl
import matplotlib.pyplot
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from scipy.stats import norm, kstest 
from numpy import arange

from icons import *

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = matplotlib.pyplot.figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(1, 1, 1)
        super(MplCanvas, self).__init__(fig)

class ResidualAnalysisWindow(QWidget):
    def __init__(self, parent, resid):
        super().__init__()
        self.parent = parent
        self.resid = resid

        self.initAppear()
        self.initUI()
        self.initConnects()

        self.show()

    def initAppear(self):
        self.setWindowTitle("Residuals")
        self.resize(700, 700)
        self.move(200, 200)

    def initUI(self):
        self.vlayout = QVBoxLayout()
        self.hlayout = QHBoxLayout()
        self.buttons = (QPushButton("Load to new tab"), QPushButton("Durbin-Watson statistic"))

        for b in self.buttons:
            self.hlayout.addWidget(b, alignment=Qt.AlignCenter)

        self.vlayout.addLayout(self.hlayout)

        # create histogram and plot
        sc = MplCanvas(self, width=5, height=4, dpi=100)
        histData = sc.axes.hist(self.resid)
        range_ = arange(min(self.resid), max(self.resid), 0.05) 
        normalityCurve = norm(self.resid.mean(), self.resid.std())
        coefY = len(self.resid) * max([1, (max(histData[0]) // (normalityCurve.pdf(self.resid.mean()) * len(self.resid)))])
        sc.axes.plot(range_, [normalityCurve.pdf(x) * coefY for x in range_], color="r")

        KS_maxD, KS_PValue = kstest(self.resid, cdf="norm", args=(self.resid.mean(), self.resid.std()))
        sc.axes.set_title("Histogram of the distribution of regression residues\nKolmogorov-Smirnov test = {:.5}, p-value = {:.5}".format(KS_maxD, KS_PValue), fontsize=16)
        sc.axes.grid()

        # add it to the widget with a toolbar
        toolbar = NavigationToolbar(sc, self)

        self.vlayout.addWidget(toolbar)
        self.vlayout.addWidget(sc)

        self.setLayout(self.vlayout)

    def initConnects(self):
        self.buttons[0].clicked.connect(lambda: self.parent.addTab("Residuals", self.resid, False, False))
