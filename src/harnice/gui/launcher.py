import os
import sys
import json
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QFileDialog,
    QMenu,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen


def layout_config_path():
    """
    Store layout in the root of the harnice repository.
    (one level above the harnice package directory)
    """
    return Path(__file__).resolve().parents[2] / "gui_layout.json"


def run_harnice_render(cwd, lightweight=False):
    """
    Safely run harnice.cli.main() without sys.exit killing the GUI.
    """
    import harnice.cli

    old_cwd = os.getcwd()
    os.chdir(cwd)

    try:
        sys.argv = ["harnice", "-l" if lightweight else "-r"]
        try:
            harnice.cli.main()
        except SystemExit:
            pass
    finally:
        os.chdir(old_cwd)


class GridWidget(QWidget):
    BUTTON_WIDTH = 180
    BUTTON_WIDTH_MARGIN = 20
    BUTTON_HEIGHT = 40
    BUTTON_HEIGHT_MARGIN = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_buttons = {}
        self.setStyleSheet("background-color: white;")
        self.setAutoFillBackground(True)

    @property
    def GRID_SPACING_X(self):
        return self.BUTTON_WIDTH + self.BUTTON_WIDTH_MARGIN

    @property
    def GRID_SPACING_Y(self):
        return self.BUTTON_HEIGHT + self.BUTTON_HEIGHT_MARGIN

    @property
    def OFFSET_X(self):
        return self.GRID_SPACING_X / 2

    @property
    def OFFSET_Y(self):
        return self.GRID_SPACING_Y / 2

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DotLine)
        painter.setPen(pen)

        width = self.width()
        height = self.height()

        x = self.OFFSET_X
        while x < width:
            painter.drawLine(x, 0, x, height)
            x += self.GRID_SPACING_X

        y = self.OFFSET_Y
        while y < height:
            painter.drawLine(0, y, width, y)
            y += self.GRID_SPACING_Y

    def grid_to_screen(self, grid_x, grid_y):
        return (
            grid_x * self.GRID_SPACING_X + self.OFFSET_X,
            grid_y * self.GRID_SPACING_Y + self.OFFSET_Y,
        )

    def screen_to_grid(self, screen_x, screen_y):
        return (
            int((screen_x - self.OFFSET_X) / self.GRID_SPACING_X),
            int((screen_y - self.OFFSET_Y) / self.GRID_SPACING_Y),
        )

    def is_grid_occupied(self, grid_x, grid_y, exclude=None):
        button = self.grid_buttons.get((grid_x, grid_y))
        return button is not None and button != exclude


class PartButton(QPushButton):
    def __init__(self, parent, label, path, grid_x, grid_y, main_window=None):
        super().__init__(label, parent)
        self.parent_grid = parent
        self.path = path
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.main_window = main_window

        self.setFixedSize(parent.BUTTON_WIDTH, parent.BUTTON_HEIGHT)
        self.dragStartPosition = None
        self.is_dragging = False
        self.show()
        self.update_position()

    def update_position(self):
        screen_x, screen_y = self.parent_grid.grid_to_screen(self.grid_x, self.grid_y)
        self.move(screen_x - self.width() // 2, screen_y - self.height() // 2)
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragStartPosition = event.position().toPoint()
            self.is_dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton) or not self.dragStartPosition:
            return

        if (event.position().toPoint() - self.dragStartPosition).manhattanLength() < 8:
            return

        self.is_dragging = True
        old_x, old_y = self.grid_x, self.grid_y

        global_pos = self.mapToGlobal(event.position().toPoint())
        local_pos = self.parent_grid.mapFromGlobal(global_pos)
        new_x, new_y = self.parent_grid.screen_to_grid(local_pos.x(), local_pos.y())

        if (new_x, new_y) == (old_x, old_y):
            return

        if self.parent_grid.is_grid_occupied(new_x, new_y, exclude=self):
            return

        self.grid_x, self.grid_y = new_x, new_y
        self.update_position()

        self.parent_grid.grid_buttons.pop((old_x, old_y), None)
        self.parent_grid.grid_buttons[(self.grid_x, self.grid_y)] = self

    def mouseReleaseEvent(self, event):
        was_dragging = self.is_dragging
        self.dragStartPosition = None
        self.is_dragging = False

        if was_dragging:
            if self.main_window:
                self.main_window.save_layout()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        if not self.main_window:
            return

        menu = QMenu(self)
        remove = menu.addAction("Remove button")
        remove.triggered.connect(lambda: self.main_window.remove_button(self))

        newrev = menu.addAction("Create new revision")
        newrev.triggered.connect(lambda: self.main_window.new_rev(self))

        menu.exec(event.globalPos())


class HarniceGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Harnice GUI Launcher")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window)

        self.grid = GridWidget(self)

        default_width = self.grid.GRID_SPACING_X * 6
        default_height = self.grid.GRID_SPACING_Y * 2
        self.resize(default_width, default_height)
        self.grid.setGeometry(0, 0, default_width, default_height)

        self.load_button = QPushButton("Load part for render...", self.grid)
        self.load_button.setFixedSize(self.grid.BUTTON_WIDTH, self.grid.BUTTON_HEIGHT)
        self.load_button.clicked.connect(self.pick_folder)
        x, y = self.grid.grid_to_screen(0, 0)
        self.load_button.move(x - self.load_button.width() // 2,
                              y - self.load_button.height() // 2)
        self.grid.grid_buttons[(0, 0)] = self.load_button

        self.load_layout()   # <-- restore saved layout

    def resizeEvent(self, event):
        self.grid.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select revision folder")
        if not folder:
            return

        gx, gy = self.find_next_grid_position()
        label = os.path.basename(folder)
        button = PartButton(self.grid, label, folder, gx, gy, main_window=self)
        button.clicked.connect(lambda checked=False, p=folder: self.run_render(p))
        self.grid.grid_buttons[(gx, gy)] = button
        self.save_layout()

    def find_next_grid_position(self):
        for y in range(100):
            for x in range(100):
                if not self.grid.is_grid_occupied(x, y):
                    return (x, y)
        return (0, 1)

    def run_render(self, cwd):
        run_harnice_render(cwd, lightweight=False)

    def remove_button(self, button):
        self.grid.grid_buttons.pop((button.grid_x, button.grid_y), None)
        button.deleteLater()
        self.save_layout()

    def new_rev(self, button):
        run_harnice_render(button.path, lightweight=False)

    def save_layout(self):
        data = []
        for (gx, gy), button in self.grid.grid_buttons.items():
            if isinstance(button, PartButton):
                data.append({
                    "label": button.text(),
                    "path": button.path,
                    "grid_x": button.grid_x,
                    "grid_y": button.grid_y,
                })

        try:
            with open(layout_config_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save GUI layout: {e}")

    def load_layout(self):
        cfg = layout_config_path()
        if not cfg.exists():
            return

        try:
            with open(cfg, "r", encoding="utf-8") as f:
                items = json.load(f)
        except Exception:
            return

        for item in items:
            gx, gy = item["grid_x"], item["grid_y"]
            label = item["label"]
            path = item["path"]

            button = PartButton(self.grid, label, path, gx, gy, main_window=self)
            button.clicked.connect(lambda checked=False, p=path: self.run_render(p))
            self.grid.grid_buttons[(gx, gy)] = button


def main():
    app = QApplication([])
    gui = HarniceGUI()
    gui.show()
    app.exec()


if __name__ == "__main__":
    main()
