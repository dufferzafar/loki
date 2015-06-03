import io
import os
import subprocess
from datetime import datetime

from PyQt4.QtCore import *
from PyQt4.QtGui import *

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


class SearchThread(QThread):
    update = pyqtSignal(int, list)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super(SearchThread, self).__init__(parent)

    def setup(self, query):
        self.query = query

    def run(self):
        # Launch Command
        locate = subprocess.Popen(['locate', '-r', self.query, '-l', '10000', '--existing'],
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
            item = QTreeWidgetItem()

            # Name & Path
            item.setText(0, parts[1])
            item.setText(1, parts[0])

            # Size & Date Modified
            item.setText(2, sizeof_fmt(info.st_size))
            time = datetime.utcfromtimestamp(info.st_mtime) \
                .strftime('%d/%m/%Y %H:%M:%S')
            item.setText(3, time)

            item.setSizeHint(0, QSize(450, 20))
            item.setSizeHint(1, QSize(550, 20))
            item.setSizeHint(2, QSize(75, 20))
            item.setSizeHint(3, QSize(200, 20))

            items.append(item)

            # Todo: Improve
            if len(items) == 1000:
                self.update.emit(count, items)
                items = []
                count += 500

        if items:
            self.update.emit(count, items)

        self.terminate()
