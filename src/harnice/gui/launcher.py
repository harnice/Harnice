import json
import os
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QMenu,
    QMessageBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QMimeData, QPoint
from PySide6.QtGui import QDrag, QPixmap

CONFIG_PATH = Path.home() / ".harnice-gui.json"


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {"buttons": []}


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


class PartButton(QPushButton):
    def __init__(self, parent, label, path):
        super().__init__(label)
        self.parent = parent
        self.path = path
        self.setAcceptDrops(True)
        self.setMinimumWidth(200)
        self.setMaximumWidth(200)
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.dragStartPosition = QPoint()
        self.dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            menu = QMenu(self)
            remove = menu.addAction("Remove Button")
            newrev = menu.addAction("Run --newrev")
            action = menu.exec(event.globalPos())
            if action == remove:
                self.parent.remove_button(self)
            elif action == newrev:
                subprocess.run(["harnice", "--newrev"], cwd=self.path)
            return
        # Store drag start position and reset dragging flag
        self.dragStartPosition = event.position().toPoint()
        self.dragging = False
        # Call super to maintain normal button press behavior
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Check if we should start a drag
        if not (event.buttons() & Qt.LeftButton):
            return

        # Only start drag if mouse has moved enough
        if (
            event.position().toPoint() - self.dragStartPosition
        ).manhattanLength() < QApplication.startDragDistance():
            return

        # Mark as dragging to prevent click event
        self.dragging = True

        # Create drag object
        drag = QDrag(self)
        mimeData = QMimeData()

        # Store button data
        mimeData.setText(self.path)
        drag.setMimeData(mimeData)

        # Create pixmap of the button for drag visual
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)

        # Create cursor offset
        drag.setHotSpot(event.position().toPoint())

        # Start drag
        drag.exec(Qt.MoveAction)

        # Reset dragging flag and button pressed state
        self.dragging = False
        self.setDown(False)

    def mouseReleaseEvent(self, event):
        # Only handle click if we're not dragging
        if event.button() == Qt.LeftButton and not self.dragging:
            super().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("background-color: lightblue;")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event):
        if event.mimeData().hasText():
            dropped_path = event.mimeData().text()
            event.acceptProposedAction()
            self.setStyleSheet("")

            # Reorder buttons
            self.parent.reorder_buttons(dropped_path, self.path)


class EmptySlot(QWidget):
    """Empty slot widget with same dimensions as buttons"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.setMaximumWidth(200)
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAcceptDrops(True)
        # Make it look like an empty button
        self.setStyleSheet(
            "background-color: rgba(128, 128, 128, 0.1); border: 1px dashed rgba(128, 128, 128, 0.3);"
        )

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet(
                "background-color: rgba(128, 128, 128, 0.3); border: 1px dashed rgba(128, 128, 128, 0.6);"
            )

    def dragLeaveEvent(self, event):
        self.setStyleSheet(
            "background-color: rgba(128, 128, 128, 0.1); border: 1px dashed rgba(128, 128, 128, 0.3);"
        )

    def dropEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet(
                "background-color: rgba(128, 128, 128, 0.1); border: 1px dashed rgba(128, 128, 128, 0.3);"
            )
            # Get parent to handle reordering
            dropped_path = event.mimeData().text()
            # Find a nearby button to use as target for reordering
            parent = self.parent()
            if hasattr(parent, "reorder_to_slot"):
                parent.reorder_to_slot(dropped_path, self)


class HarniceGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Harnice Launcher")
        # Make window float over all other windows
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)

        self.layout = QVBoxLayout()
        self.layout.setSpacing(8)  # 8px spacing between buttons
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.layout)

        # Track button widgets by path
        self.button_map = {}

        self.cfg = load_config()

        # Add load button at top
        self.add_new_load_button()

        # Restore saved buttons
        for b in self.cfg["buttons"]:
            self.add_button(b["label"], b["path"])

        # Add stretch spacer at the end to absorb extra height
        self.layout.addStretch()

        # Set minimum height to 5 buttons, fixed width, allow user to resize height
        self.setMinimumSize(220, 272)
        self.setMaximumWidth(220)  # Keep width fixed

    def add_button(self, label, path):
        btn = PartButton(self, label, path)
        btn.clicked.connect(lambda checked=False, p=path: self.render_part(p))
        # Find first empty slot to replace
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item and isinstance(item.widget(), EmptySlot):
                self.layout.removeWidget(item.widget())
                item.widget().deleteLater()
                self.layout.insertWidget(i, btn)
                self.button_map[path] = btn
                return
        # If no empty slot found, just add it
        self.layout.addWidget(btn)
        self.button_map[path] = btn

    def add_new_load_button(self):
        btn = QPushButton("Load part for render…")
        btn.setMinimumWidth(200)
        btn.setMaximumWidth(200)
        btn.setMinimumHeight(40)
        btn.setMaximumHeight(40)
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        btn.clicked.connect(self.pick_folder)
        self.layout.addWidget(btn)

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select revision folder")
        if not folder:
            return
        label = os.path.basename(folder)
        self.add_button(label, folder)
        self.cfg["buttons"].append({"label": label, "path": folder})
        save_config(self.cfg)

    def remove_button(self, button):
        idx = self.layout.indexOf(button)
        self.layout.takeAt(idx)
        button.deleteLater()
        # Remove from button_map
        self.button_map.pop(button.path, None)
        self.cfg["buttons"] = [
            b for b in self.cfg["buttons"] if b["path"] != button.path
        ]
        save_config(self.cfg)

    def reorder_buttons(self, dragged_path, target_path):
        """Reorder buttons by moving dragged_path to position before target_path"""
        if dragged_path == target_path:
            return

        dragged_btn = self.button_map.get(dragged_path)
        target_btn = self.button_map.get(target_path)

        if not dragged_btn or not target_btn:
            return

        # Get current indices
        dragged_idx = self.layout.indexOf(dragged_btn)
        target_idx = self.layout.indexOf(target_btn)

        # Remove dragged button from layout
        self.layout.takeAt(dragged_idx)

        # Insert at target position (account for removed item if dragging down)
        if dragged_idx < target_idx:
            self.layout.insertWidget(target_idx - 1, dragged_btn)
        else:
            self.layout.insertWidget(target_idx, dragged_btn)

        # Update config order
        buttons = self.cfg["buttons"]
        dragged_item = next((b for b in buttons if b["path"] == dragged_path), None)
        if dragged_item:
            buttons.remove(dragged_item)
            target_idx_config = next(
                (i for i, b in enumerate(buttons) if b["path"] == target_path),
                len(buttons),
            )
            if dragged_idx < target_idx:
                buttons.insert(target_idx_config - 1, dragged_item)
            else:
                buttons.insert(target_idx_config, dragged_item)

        save_config(self.cfg)

    def reorder_to_slot(self, dragged_path, empty_slot):
        """Move button to empty slot position"""
        dragged_btn = self.button_map.get(dragged_path)
        if not dragged_btn:
            return

        # Get current indices
        dragged_idx = self.layout.indexOf(dragged_btn)
        slot_idx = self.layout.indexOf(empty_slot)

        # Remove dragged button and empty slot
        self.layout.takeAt(slot_idx)
        empty_slot.deleteLater()
        self.layout.takeAt(dragged_idx)

        # Insert button at empty slot position
        self.layout.insertWidget(slot_idx, dragged_btn)

        # Add new empty slot where dragged button was
        new_empty = EmptySlot(self)
        self.layout.insertWidget(dragged_idx, new_empty)

    def render_part(self, cwd):
        try:
            subprocess.run(["harnice", "-r", "harness"], cwd=cwd)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Could not run harnice")


def main():
    app = QApplication([])
    gui = HarniceGUI()
    gui.show()
    app.exec()


if __name__ == "__main__":
    main()
