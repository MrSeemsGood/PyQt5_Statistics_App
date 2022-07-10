from enum import Enum, auto
from PyQt5.QtGui import QIcon, QPixmap

class MyIcon(Enum):
    CHOOSE_LANGUAGE = auto()
    OPEN_XL = auto()
    HISTOGRAM = auto()

    def getQIcon(self):
        return icons.get(self, QIcon(QPixmap("res/icons/!blank.png")))
    #* use it like this: Icon.CHOOSE_LANGUAGE.getQICon()

icons = {
    MyIcon.CHOOSE_LANGUAGE : QIcon(QPixmap("res/icons/language_icon.png")),
    MyIcon.OPEN_XL : QIcon(QPixmap("res/icons/excel.png")),
    MyIcon.HISTOGRAM : QIcon(QPixmap("res/icons/histogram.png"))
}