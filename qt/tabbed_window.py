# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PyQt5.QtCore import Qt, QRect, pyqtSlot
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QMainWindow,
    QTabWidget,
    QMenuBar,
    QMenu,
    QDesktopWidget
)
from hscommon.trans import trget
from qtlib.util import moveToScreenCenter
from .directories_dialog import DirectoriesDialog
from .result_window import ResultWindow
from .ignore_list_dialog import IgnoreListDialog
tr = trget("ui")


class TabWindow(QMainWindow):
    def __init__(self, app, **kwargs):
        super().__init__(None, **kwargs)
        self.app = app
        self.pages = {}
        self._setupUi()
        self.app.willSavePrefs.connect(self.appWillSavePrefs)

    def _setupUi(self):
        self.setWindowTitle(self.app.NAME)
        self.resize(420, 338)
        self.tabwidget = QTabWidget()
        # self.tabwidget.setTabBarAutoHide(False)
        self.tabwidget.currentChanged.connect(self.updateMenuBar)
        self.tabwidget.tabCloseRequested.connect(self.onTabCloseRequested)
        self.tabwidget.setTabsClosable(True)
        self.centralWidget = QWidget(self)
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.addWidget(self.tabwidget)
        self._setupMenu()
        # self.setLayout(self.verticalLayout)
        self.setCentralWidget(self.centralWidget)
        self.updateMenuBar(self.tabwidget.currentIndex())

        # if self.app.prefs.mainWindowIsMaximized:
        #     self.setWindowState(self.windowState() | Qt.WindowMaximized)
        # else:
        #     if self.app.prefs.mainWindowRect is not None:
        #         self.setGeometry(self.app.prefs.mainWindowRect)
        #         # if not on any screen move to center of default screen
        #         # moves to center of closest screen if partially off screen
        #         frame = self.frameGeometry()
        #         if QDesktopWidget().screenNumber(self) == -1:
        #             moveToScreenCenter(self)
        #         elif QDesktopWidget().availableGeometry(self).contains(frame) is False:
        #             frame.moveCenter(QDesktopWidget().availableGeometry(self).center())
        #             self.move(frame.topLeft())
        #     else:
        #         moveToScreenCenter(self)

        if self.app.prefs.mainWindowRect is not None:
            self.setGeometry(self.app.prefs.mainWindowRect)
        else:
            moveToScreenCenter(self)

    def _setupMenu(self):
        self.menubar = QMenuBar()  # self.menuBar()
        self.menubar.setGeometry(QRect(0, 0, 630, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setTitle(tr("File"))
        self.menuMark = QMenu(self.menubar)
        self.menuMark.setTitle(tr("Mark"))
        self.menuActions = QMenu(self.menubar)
        self.menuActions.setTitle(tr("Actions"))
        self.menuColumns = QMenu(self.menubar)
        self.menuColumns.setTitle(tr("Columns"))
        self.menuView = QMenu(self.menubar)
        self.menuView.setTitle(tr("View"))
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setTitle(tr("Help"))
        self.menubar.setGeometry(QRect(0, 0, 630, 22))
        self.setMenuBar(self.menubar)

    @pyqtSlot(int)
    def updateMenuBar(self, page_index=None):
        current_index = self.tabwidget.currentIndex()
        print(f"currentChanged: index is now {current_index}, {self.tabwidget.widget(current_index)}")
        if page_index is None:
            page_index = self.tabwidget.currentIndex()

    def createPage(self, cls, **kwargs):
        app = kwargs.get("app", self.app)
        page = None

        if cls == "DirectoriesDialog":
            page = DirectoriesDialog(app)
        elif cls == "ResultWindow":
            parent = kwargs.get("parent", self)
            page = ResultWindow(parent, app)
        elif cls == "IgnoreListDialog":
            parent = kwargs.get("parent", self)
            model = kwargs.get("model")
            page = IgnoreListDialog(parent, model)

        self.pages[cls] = page
        return page

    def addTab(self, page, title, visible=True):
        # Warning: this takes ownership of the page!
        index = self.tabwidget.addTab(page, title)
        # index = self.tabwidget.insertTab(-1, page, title)
        if not visible:
            self.tabwidget.setTabVisible(index, False)
        return index

    # --- Events
    def appWillSavePrefs(self):
        # Right now this is useless since the first spawn dialog inside the
        # QTabWidget will assign its geometry after restoring it
        prefs = self.app.prefs
        prefs.mainWindowIsMaximized = self.isMaximized()
        prefs.mainWindowRect = self.geometry()

    def closeEvent(self, event):
        self.appWillSavePrefs()
        # Force closing of our tabbed widgets in reverse order
        for index in range(self.tabwidget.count() - 1, -1, -1):
            self.tabwidget.widget(index).close()

    @pyqtSlot(int)
    def onTabCloseRequested(self, index):
        print(f"close requested on {index} {self.tabwidget.widget(index)}")
        # if self.tabwidget.tabBar().currentIndex(index) == self.tabwidget.currentWidget():
        if isinstance(self.tabwidget.widget(index), DirectoriesDialog):
            # if we close this one, the application quits,
            # force user to use the menu or shortcut
            return
        self.tabwidget.widget(index).close()
        self.tabwidget.setTabVisible(index, False)
        # self.tabwidget.widget(index).hide()
        self.tabwidget.removeTab(index)
        # self.tabwidget.setCurrentIndex(index -1)

    @pyqtSlot()
    def onDialogAccepted(self):
        """Remove tabbed dialog when Accepted/Done."""
        widget = self.sender()
        index = self.tabwidget.indexOf(widget)
        if index > -1:
            self.tabwidget.removeTab(index)
