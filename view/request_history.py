import copy
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

MAX_ENTRIES = 50


class RequestHistory(QWidget):
    """Requests run in this session (kept in memory only), newest first."""
    entry_selected = Signal(dict)

    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout()

        self.list = QListWidget(self)
        self.list.itemClicked.connect(self._emit_entry)
        self.list.itemActivated.connect(self._emit_entry)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.list.clear)

        layout.addWidget(QLabel('HISTORY'))
        layout.addWidget(self.list)
        layout.addWidget(self.clear_btn)
        self.setLayout(layout)

    def add_entry(self, fields: dict, status: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        item = QListWidgetItem(f"{timestamp}  {fields.get('method')} {status}  {fields.get('url')}")
        item.setToolTip(fields.get('url') or '')
        # Copy so later edits to the caller's dict can't change the stored request
        item.setData(Qt.ItemDataRole.UserRole, copy.deepcopy(fields))
        self.list.insertItem(0, item)
        while self.list.count() > MAX_ENTRIES:
            self.list.takeItem(self.list.count() - 1)

    def _emit_entry(self, item: QListWidgetItem):
        self.entry_selected.emit(copy.deepcopy(item.data(Qt.ItemDataRole.UserRole)))
