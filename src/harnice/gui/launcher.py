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
)
from PySide6.QtCore import Qt

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
        super().mousePressEvent(event)


class HarniceGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Harnice Launcher")
        # Make window float over all other windows
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.cfg = load_config()

        # Restore saved buttons
        for b in self.cfg["buttons"]:
            self.add_button(b["label"], b["path"])

        # Add blank button at bottom
        self.add_new_load_button()

    def add_button(self, label, path):
        btn = PartButton(self, label, path)
        btn.clicked.connect(lambda: self.render_part(path))
        self.layout.addWidget(btn)

    def add_new_load_button(self):
        btn = QPushButton("Load part for render…")
        btn.clicked.connect(self.pick_folder)
        self.layout.addWidget(btn)

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select revision folder")
        if not folder:
            return
        self.add_button(f"Render {os.path.basename(folder)}", folder)
        self.cfg["buttons"].append(
            {"label": f"Render {os.path.basename(folder)}", "path": folder}
        )
        save_config(self.cfg)

    def remove_button(self, button):
        idx = self.layout.indexOf(button)
        self.layout.takeAt(idx)
        button.deleteLater()
        self.cfg["buttons"] = [
            b for b in self.cfg["buttons"] if b["path"] != button.path
        ]
        save_config(self.cfg)

    def render_part(self, cwd):
        try:
            subprocess.run(["harnice", "-r"], cwd=cwd)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Could not run harnice")


def main():
    app = QApplication([])
    gui = HarniceGUI()
    gui.show()
    app.exec()


if __name__ == "__main__":
    main()
