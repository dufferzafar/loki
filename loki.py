#!/usr/bin/python3

import os
import sys
import subprocess

from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from search import SearchThread

# Handle Ctrl + C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Load the UI
form_class = uic.loadUiType("main.ui")[0]


class loki(QMainWindow, form_class):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.itemCount = 0

        # Status Bar
        self.status = self.statusBar()
        self.status.showMessage("Ready")

        self.itemStatus = QLabel("%d Items" % self.itemCount)
        self.status.addPermanentWidget(self.itemStatus)

        self.searchBtn.clicked.connect(self.search)
        self.query.returnPressed.connect(self.searchBtn.click)

        self.connect(self.results, SIGNAL("itemDoubleClicked(QTreeWidgetItem*, int)"), self.onDoubleClickItem)
        self.results.keyPressEvent = self.onKeyPressEvent

        self.query.setFocus()

        # Todo: Add these things to Menus too?
        # http://zetcode.com/gui/pyqt4/menusandtoolbars/
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("Ctrl+F"), self, self.query.setFocus)
        QShortcut(QKeySequence("Ctrl+L"), self, self.results.clear)

        # Query from command line
        if len(sys.argv) >= 2:
            self.query.setText(sys.argv[1])
            # Todo: Display window and begin searching
            # self.search()

    def search(self):
        """ Run locate command and display results. """

        # Empty query
        query = self.query.text().strip()
        if not query:
            return

        # Set working status
        self.results.clear()
        self.status.showMessage("Searching...")
        self.results.setSortingEnabled(False)
        self.repaint()

        thread = SearchThread(self)
        thread.update.connect(self.update_results)
        thread.terminated.connect(self.finished)
        thread.setup(query)
        thread.start()

    def update_results(self, count, items):
        self.results.insertTopLevelItems(count, items)
        self.results.resizeColumnToContents(0)
        self.results.resizeColumnToContents(1)
        self.results.resizeColumnToContents(2)
        self.results.resizeColumnToContents(3)
        self.results.repaint()

    def finished(self):
        self.status.showMessage("Ready")

        self.itemCount = self.results.topLevelItemCount()
        self.itemStatus.setText("%d Items" % self.itemCount)

        # Sort by Name
        self.results.setSortingEnabled(True)
        if self.itemCount < 10000:
            self.results.sortByColumn(0, 0)

    def onDoubleClickItem(self, item, column):
        print(item, column)

    def onKeyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            item = self.results.currentItem()

            # Ctrl + Enter - Launch File
            if event.modifiers() == Qt.ControlModifier:
                path = os.path.join(item.text(1), item.text(0))

            # Enter - Open Folder
            else:
                path = os.path.join(item.text(1))

            subprocess.Popen(['xdg-open', path])

            return

        QTreeWidget.keyPressEvent(self.results, event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = loki(None)
    window.showMaximized()

    app.exec_()
