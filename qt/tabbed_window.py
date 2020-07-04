# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PyQt5.QtCore import QRect, Qt, pyqtSlot
from PyQt5.QtWidgets import (
    QWidget,
    QFileDialog,
    QHeaderView,
    QVBoxLayout,
    QHBoxLayout,
    QTreeView,
    QAbstractItemView,
    QSpacerItem,
    QSizePolicy,
    QPushButton,
    QMainWindow,
    QTabWidget,
    QMenuBar
)
from .directories_dialog import DirectoriesDialog


class TabWindow(QMainWindow):
    def __init__(self, app, **kwargs):
        super().__init__(None, **kwargs)
        self.app = app
        self._setupUi()

    def _setupUi(self):
        self.setWindowTitle(self.app.NAME)
        self.resize(420, 338)
        self.tabwidget = QTabWidget()
        self.tabwidget.currentChanged.connect(self.updateMenuBar)
        self.centralWidget = QWidget(self)
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.addWidget(self.tabwidget)
        self.directories_dialog = DirectoriesDialog(self.app)
        self.tabwidget.addTab(self.directories_dialog, "Directories")
        # self.setLayout(self.verticalLayout)
        self.setCentralWidget(self.centralWidget)

        self.menubar = self.menuBar()
        self.menubar.setGeometry(QRect(0, 0, 630, 22))
        # self.setMenuBar(self.menubar)
        self.updateMenuBar(self.tabwidget.currentIndex())

    @pyqtSlot(int)
    def updateMenuBar(self, page_index=None):
        if page_index is None:
            page_index = self.tabwidget.currentIndex()
        self.menubar = self.tabwidget.widget(page_index).menubar
        self.setMenuBar(self.menubar)
