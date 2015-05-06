#!/usr/bin/python3

import io
import os
import sys
import subprocess
from datetime import datetime


from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Handle Ctrl + C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Load the UI
form_class = uic.loadUiType("main.ui")[0]


def sizeof_fmt(num, suffix='B'):
    """
    Convert Bytes to Human Readable Form: KB, MB etc.

    http://stackoverflow.com/a/1094933/2043048
    """
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Y', suffix)


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

        # Launch Command
        locate = subprocess.Popen(['locate', query, '-l', '10000', '--existing'],
                                  stdout=subprocess.PIPE)

        items = []
        count = 0
        for line in io.open(locate.stdout.fileno()):

            path = line.rstrip('\n')
            parts = os.path.split(path)

            # Skip non existent files
            try:
                info = os.stat(path)
            except FileNotFoundError:
                continue

            item = QTreeWidgetItem()

            # Name & Path
            item.setText(0, parts[1])
            item.setText(1, parts[0])

            # Size & Date Modified
            item.setText(2, sizeof_fmt(info.st_size))
            time = datetime.utcfromtimestamp(
                info.st_mtime).strftime('%d/%m/%Y %H:%M:%S')
            item.setText(3, time)

            item.setSizeHint(0, QSize(450, 20))
            item.setSizeHint(1, QSize(550, 20))
            item.setSizeHint(2, QSize(75, 20))
            item.setSizeHint(3, QSize(200, 20))

            items.append(item)

            # Todo: Improve
            if len(items) == 500:
                self.results.insertTopLevelItems(count, items)
                self.results.resizeColumnToContents(0)
                self.results.resizeColumnToContents(1)
                self.results.resizeColumnToContents(2)
                self.results.resizeColumnToContents(3)
                self.results.repaint()
                items = []
                count += 500

        if items:
            self.results.insertTopLevelItems(count, items)

        # Resize Columns
        self.results.resizeColumnToContents(0)
        self.results.resizeColumnToContents(1)
        self.results.resizeColumnToContents(2)
        self.results.resizeColumnToContents(3)

        self.status.showMessage("Ready")

        self.itemCount = self.results.topLevelItemCount()
        self.itemStatus.setText("%d Items" % self.itemCount)

        # Sort by Name
        self.results.setSortingEnabled(True)
        if self.itemCount < 10000:
            self.results.sortByColumn(0, 0)

        # print("Search finished!")

    def onDoubleClickItem(self, item, column):
        print (item, column)

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
