import io
import os
import subprocess
from datetime import datetime

from PyQt4.QtCore import *
from PyQt4.QtGui import *

# TODO: Find this dynamically using Qt
SCREEN_WIDTH = 1920

exclude_dirs = ["node_modules/", ".git/", "__pycache__/"]
exclude_files = [".pyc"]


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


class ResultItem(QTreeWidgetItem):

    def __lt__(self, other):
        if (not isinstance(other, ResultItem)):
            return super(ResultItem, self).__lt__(other)

        tree = self.treeWidget()
        if (not tree):
            column = 0
        else:
            column = tree.sortColumn()

        return self._sortData.get(column, self.text(column)) < \
            other._sortData.get(column, other.text(column))

    def __init__(self, *args):
        super(ResultItem, self).__init__(*args)
        self._sortData = {}

    def setSortData(self, column, data):
        self._sortData[column] = data


class SearchThread(QThread):
    update = pyqtSignal(int, list)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super(SearchThread, self).__init__(parent)

    def setup(self, query):
        self.query = query

    def run(self):
        # Launch Command
        locate = subprocess.Popen(['locate', "-b", self.query, '-l', '10000', '--existing'],
                                  stdout=subprocess.PIPE)

        items = []
        count = 0
        for line in io.open(locate.stdout.fileno()):

            path = line.rstrip('\n')

            # If the path contains an excluded directory
            if any([x in path for x in exclude_dirs]):
                continue

            # If the file has an excluded extension
            if any([path.endswith(x) for x in exclude_files]):
                continue

            # Skip non existent files
            try:
                info = os.stat(path)
            except FileNotFoundError:
                continue

            parts = os.path.split(path)
            item = ResultItem()

            # Name & Path
            item.setText(0, parts[1])
            item.setText(1, parts[0])

            # Size
            item.setText(2, sizeof_fmt(info.st_size))
            item.setSortData(2, info.st_size)

            # Date Modified
            time = datetime.utcfromtimestamp(info.st_mtime) \
                .strftime('%d/%m/%Y %H:%M:%S')
            item.setText(3, time)

            # Set width of columns depending on screen width
            item.setSizeHint(0, QSize(SCREEN_WIDTH * 0.31, 30))
            item.setSizeHint(1, QSize(SCREEN_WIDTH * 0.45, 30))
            item.setSizeHint(2, QSize(SCREEN_WIDTH * 0.06, 30))
            item.setSizeHint(3, QSize(SCREEN_WIDTH * 0.15, 30))

            count += 1
            items.append(item)

            # Todo: Improve
            if not (count % 300):
                self.update.emit(count, items)
                items = []

        if items:
            self.update.emit(count, items)

        self.terminate()
