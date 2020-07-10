# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PyQt5.QtCore import QRect, pyqtSlot, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMainWindow,
    QTabWidget,
    QMenu,
    QTabBar,
    QStackedWidget,
    QMenuBar
    # QDesktopWidget,
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
        self.menubar = None
        self.menuList = set()
        self.last_index = -1
        self.previous_widget_actions = set()
        self._setupUi()
        self.app.willSavePrefs.connect(self.appWillSavePrefs)

    def _setupUi(self, separate_tabbar=True):
        self.setWindowTitle(self.app.NAME)
        self.resize(640, 480)
        self.tabWidget = QTabWidget()  # (self)
        # self.tabWidget.setTabPosition(QTabWidget.South)
        self.tabWidget.setContentsMargins(0, 0, 0, 0)
        # self.tabWidget.setTabBarAutoHide(True)
        # This gets rid of the 1 pixel margin around the TabWidget
        self.tabWidget.setDocumentMode(True)

        # self.menubar = QMenuBar(self)
        self._setupMenu()

        if not separate_tabbar:
            # self.setMenuBar(self.menubar)  # already set if QMainWindow class
            self.verticalLayout = QVBoxLayout(self.tabWidget)  # self.centralWidget.setLayout(self.verticalLayout)
            # self.verticalLayout.addWidget(self.tabWidget)
            self.verticalLayout.setContentsMargins(0, 0, 0, 0)
            self.tabWidget.setTabsClosable(True)
            self.setCentralWidget(self.tabWidget)  # only for QMainWindow
        else:
            self.centralWidget = QWidget(self)
            self.setCentralWidget(self.centralWidget)
            self.verticalLayout = QVBoxLayout()
            self.centralWidget.setLayout(self.verticalLayout)
            # By default we separate the tab bar and place it next to the top menu
            self.tabBar = QTabBar()  #(self.tabWidget)
            self.tabWidget.setTabBar(self.tabBar)
            # self.setMenuBar(self.menubar)  # already set if QMainWindow class
            self.horizontalLayout = QHBoxLayout()
            self.horizontalLayout.addWidget(self.menubar, 0, Qt.AlignTop)
            self.horizontalLayout.addWidget(self.tabBar, 0, Qt.AlignTop)
            self.verticalLayout.addLayout(self.horizontalLayout)
            self.verticalLayout.addWidget(self.tabWidget)
            self.tabBar.setTabsClosable(True)

        self.tabWidget.currentChanged.connect(self.updateMenuBar)
        self.tabWidget.tabCloseRequested.connect(self.onTabCloseRequested)
        self.updateMenuBar(self.tabWidget.currentIndex())
        self.restoreGeometry()

    def restoreGeometry(self):
        if self.app.prefs.mainWindowRect is not None:
            self.setGeometry(self.app.prefs.mainWindowRect)
        else:
            moveToScreenCenter(self)

    def _setupMenu(self):
        """Setup the menubar boiler plates which will be filled by the underlying
        tab's widgets whenever they are instantiated."""
        if not self.menubar:
            self.menubar = self.menuBar()  # QMainWindow, similar to just QMenuBar() here
        self.menubar.setGeometry(QRect(0, 0, 100, 22))
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

        self.menuList.add(self.menuFile)
        self.menuList.add(self.menuMark)
        self.menuList.add(self.menuActions)
        self.menuList.add(self.menuColumns)
        self.menuList.add(self.menuView)
        self.menuList.add(self.menuHelp)

    @pyqtSlot(int)
    def updateMenuBar(self, page_index=None):
        if page_index < 0:
            return
        current_index = self.getCurrentIndex()
        active_widget = self.getCurrentWidget(current_index)
        if self.last_index < 0:
            self.last_index = current_index
            self.previous_widget_actions = active_widget.specific_actions
            return
        isResultWindow = isinstance(active_widget, ResultWindow)
        for menu in self.menuList:
            if menu is self.menuColumns or menu is self.menuActions or menu is self.menuMark:
                if not isResultWindow:
                    menu.setEnabled(False)
                    continue
                else:
                    menu.setEnabled(True)
            for action in menu.actions():
                if action is self.app.directories_dialog.actionShowResultsWindow:
                    if isResultWindow:
                        # Action points to ourselves, always disable it
                        self.app.directories_dialog.actionShowResultsWindow\
                            .setEnabled(False)
                        continue
                    self.app.directories_dialog.actionShowResultsWindow\
                        .setEnabled(self.app.resultWindow is not None)
                    continue
                if action not in active_widget.specific_actions:
                    if action in self.previous_widget_actions:
                        action.setEnabled(False)
                    continue
                action.setEnabled(True)

        self.previous_widget_actions = active_widget.specific_actions
        self.last_index = current_index

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

    def addTab(self, page, title, switch=False):
        # Warning: this takes ownership of the page!
        index = self.tabWidget.addTab(page, title)
        # index = self.tabWidget.insertTab(-1, page, title)
        if isinstance(page, DirectoriesDialog):
            self.tabWidget.tabBar().setTabButton(
                index, QTabBar.RightSide, None)
        if switch:
            self.setCurrentIndex(index)
        return index

    def indexOfWidget(self, widget):
        return self.tabWidget.indexOf(widget)

    def setCurrentIndex(self, index):
        return self.tabWidget.setCurrentIndex(index)

    def setTabVisible(self, index, value):
        return self.tabWidget.setTabVisible(index, value)

    def removeTab(self, index):
        return self.tabWidget.removeTab(index)

    def isTabVisible(self, index):
        return self.tabWidget.isTabVisible(index)

    def getCurrentIndex(self):
        return self.tabWidget.currentIndex()

    def getCurrentWidget(self, index):
        return self.tabWidget.widget(index)

    def getCount(self):
        return self.tabWidget.count()

    # --- Events
    def appWillSavePrefs(self):
        # Right now this is useless since the first spawn dialog inside the
        # QTabWidget will assign its geometry after restoring it
        prefs = self.app.prefs
        prefs.mainWindowIsMaximized = self.isMaximized()
        prefs.mainWindowRect = self.geometry()

    def closeEvent(self, close_event):
        # Force closing of our tabbed widgets in reverse order so that the
        # directories dialog (which usually is at index 0) will be called last
        for index in range(self.getCount() - 1, -1, -1):
            self.getCurrentWidget(index).closeEvent(close_event)
        self.appWillSavePrefs()

    @pyqtSlot(int)
    def onTabCloseRequested(self, index):
        # if self.tabWidget.tabBar().currentIndex(index) == self.tabWidget.currentWidget():
        current_widget = self.getCurrentWidget(index)
        if isinstance(current_widget, DirectoriesDialog):
            # if we close this one, the application quits,
            # force user to use the menu or shortcut
            return
        current_widget.close()
        self.setTabVisible(index, False)
        # self.tabWidget.widget(index).hide()
        self.removeTab(index)
        # self.tabWidget.setCurrentIndex(index -1)

    @pyqtSlot()
    def onDialogAccepted(self):
        """Remove tabbed dialog when Accepted/Done."""
        widget = self.sender()
        index = self.indexOfWidget(widget)
        if index > -1:
            self.removeTab(index)


class TabBarWindow(TabWindow):
    """Implementation which uses a separate QTabBar and QStackedWidget.
    The Tab bar is placed next to the menu bar to save real estate."""
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)

    def _setupUi(self):
        self.setWindowTitle(self.app.NAME)
        self.resize(640, 480)
        self.tabBar = QTabBar()
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self._setupMenu()

        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.stackedWidget = QStackedWidget()
        self.centralWidget.setLayout(self.verticalLayout)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.addWidget(self.menubar, 0, Qt.AlignTop)
        self.horizontalLayout.addWidget(self.tabBar, 0, Qt.AlignTop)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.stackedWidget)

        self.stackedWidget.currentChanged.connect(self.updateMenuBar)
        # Circular logic here:
        # self.stackedWidget.widgetRemoved.connect(self.removeTab)
        self.tabBar.currentChanged.connect(self.showTab)
        self.tabBar.tabCloseRequested.connect(self.onTabCloseRequested)
        self.tabBar.setTabsClosable(True)
        self.restoreGeometry()

    def addTab(self, page, title, switch=True):
        stack_index = self.stackedWidget.addWidget(page)
        tab_index = self.tabBar.addTab(title)
        # index = self.tabWidget.insertTab(-1, page, title)
        if isinstance(page, DirectoriesDialog):
            self.tabBar.setTabButton(
                tab_index, QTabBar.RightSide, None)
        if switch:  # switch to the added tab immediately upon creation
            self.setCurrentIndex(tab_index)
        return stack_index

    @pyqtSlot(int)
    def showTab(self, index):
        if index >= 0 and index < self.stackedWidget.count():
            self.stackedWidget.setCurrentIndex(index)
            # if not self.tabBar.isTabVisible(index):
            self.setTabVisible(index, True)

    def indexOfWidget(self, widget):
        # Warning: this may return -1 if widget is not a child of stackedwidget
        return self.stackedWidget.indexOf(widget)

    def setCurrentIndex(self, tab_index):
        # The signal will handle switching the stackwidget's widget
        self.tabBar.setCurrentIndex(tab_index)

    @pyqtSlot(int)
    def setTabIndex(self, index):
        if not index:
            return
        self.tabBar.setCurrentIndex(index)

    def setTabVisible(self, index, value):
        return self.tabBar.setTabVisible(index, value)

    @pyqtSlot(int)
    def removeTab(self, index):
        self.stackedWidget.removeWidget(self.stackedWidget.widget(index))
        return self.tabBar.removeTab(index)

    @pyqtSlot(int)
    def removeWidget(self, widget):
        return self.stackedWidget.removeWidget(widget)

    def isTabVisible(self, index):
        return self.tabBar.isTabVisible(index)

    def getCurrentIndex(self):
        return self.stackedWidget.currentIndex()

    def getCurrentWidget(self, index):
        return self.stackedWidget.widget(index)

    def getCount(self):
        return self.stackedWidget.count()


# class FakeCloseButton(QAbstractButton):
#     """Cloes button that doesn't display on the tab bar."""
#     def __init__(self):
#         super().__init__()
#         self.setFocusPolicy(Qt.NoFocus)
#         self.setCursor(Qt.ArrowCursor)
#         self.setToolTip(tr("Close Tab"))
#         self.resize(self.sizeHint())

#     def paintEvent(self, event):
#         pass
