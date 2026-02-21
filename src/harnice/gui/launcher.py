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
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QPainter, QPen


def layout_config_path():
    """
    Save layout JSON into the root of the harnice project directory.
    """
    return Path(__file__).resolve().parents[2] / "gui_layout.json"


def _hex_adjust_brightness(hex_color, toward_white_ratio=0.0):
    """
    Adjust brightness of a #rrggbb or #rgb hex color.
    toward_white_ratio: 0 = no change; 0.2 = 20% blend toward white (lighter);
                       negative = blend toward black (darker), e.g. -0.15.
    """
    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        return "#" + hex_color
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    if toward_white_ratio >= 0:
        r = int(r + (255 - r) * toward_white_ratio)
        g = int(g + (255 - g) * toward_white_ratio)
        b = int(b + (255 - b) * toward_white_ratio)
    else:
        r = int(r * (1 + toward_white_ratio))
        g = int(g * (1 + toward_white_ratio))
        b = int(b * (1 + toward_white_ratio))
    return f"#{r:02x}{g:02x}{b:02x}"


def button_color_for_product(product_type):
    """
    Return the button_color from the product module for the given product_type,
    or None if the product has no button_color.
    """
    if not product_type:
        return None
    try:
        product_module = __import__(
            f"harnice.products.{product_type}", fromlist=[product_type]
        )
        return getattr(product_module, "button_color", None)
    except Exception:
        return None


def product_type_for_revision_folder(rev_folder):
    """
    Return the Harnice product type (e.g. "harness", "device") for a revision
    folder path, or None if it cannot be determined.
    """
    rev_folder = os.path.normpath(rev_folder)
    part_dir = os.path.dirname(rev_folder)
    rev_folder_name = os.path.basename(rev_folder)
    part_dir_name = os.path.basename(part_dir)
    if not rev_folder_name.startswith(f"{part_dir_name}-rev"):
        return None
    rev_str = rev_folder_name.split("-rev")[-1]
    if not rev_str.isdigit():
        return None
    rev_history_path = os.path.join(part_dir, f"{part_dir_name}-revision_history.tsv")
    if not os.path.exists(rev_history_path):
        return None
    try:
        from harnice.lists import rev_history

        return rev_history.info(rev=rev_str, path=rev_history_path, field="product")
    except Exception:
        return None


def run_harnice_render(cwd, lightweight=False):
    """
    Safely run harnice.cli.main() without sys.exit closing the GUI.
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


class RenderWorker(QObject):
    finished = Signal(bool, str)  # True = success, False = error, error_message

    def __init__(self, cwd, lightweight):
        super().__init__()
        self.cwd = cwd
        self.lightweight = lightweight

    def run(self):
        try:
            run_harnice_render(self.cwd, self.lightweight)
            self.finished.emit(True, "")
        except Exception as e:
            import traceback

            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            self.finished.emit(False, error_msg)


class GridWidget(QWidget):
    BUTTON_WIDTH = 180
    BUTTON_HEIGHT = 40
    BUTTON_WIDTH_MARGIN = 20
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
        btn = self.grid_buttons.get((grid_x, grid_y))
        return btn is not None and btn is not exclude


class PartButton(QPushButton):
    def __init__(
        self, parent, label, path, grid_x, grid_y, main_window=None, product_type=None
    ):
        super().__init__(label, parent)
        self.parent_grid = parent
        self.path = path
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.main_window = main_window
        self.product_type = (
            product_type
            if product_type is not None
            else product_type_for_revision_folder(path)
        )

        # ✅ Store the intended "default / unclicked" theme
        bg = button_color_for_product(self.product_type) or "#e6e6e6"
        bg_hover = _hex_adjust_brightness(bg, 0.18)
        bg_pressed = _hex_adjust_brightness(bg, -0.12)
        self.default_style = f"""
            QPushButton {{
                background-color: {bg};
                border: 1px solid #666;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {bg_hover};
            }}
            QPushButton:pressed {{
                background-color: {bg_pressed};
            }}
        """
        self.setStyleSheet(self.default_style)

        self.setFixedSize(parent.BUTTON_WIDTH, parent.BUTTON_HEIGHT)
        self.dragStartPosition = None
        self.is_dragging = False
        self.show()
        self.update_position()

    def update_position(self):
        x, y = self.parent_grid.grid_to_screen(self.grid_x, self.grid_y)
        self.move(x - self.width() // 2, y - self.height() // 2)
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragStartPosition = event.position().toPoint()
            self.is_dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            not (event.buttons() & Qt.MouseButton.LeftButton)
            or not self.dragStartPosition
        ):
            return

        if (event.position().toPoint() - self.dragStartPosition).manhattanLength() < 8:
            return

        self.is_dragging = True
        old_pos = (self.grid_x, self.grid_y)

        global_pos = self.mapToGlobal(event.position().toPoint())
        local_pos = self.parent_grid.mapFromGlobal(global_pos)
        new_x, new_y = self.parent_grid.screen_to_grid(local_pos.x(), local_pos.y())

        if (new_x, new_y) == old_pos:
            return

        if self.parent_grid.is_grid_occupied(new_x, new_y, exclude=self):
            return

        self.grid_x, self.grid_y = new_x, new_y
        self.update_position()

        self.parent_grid.grid_buttons.pop(old_pos, None)
        self.parent_grid.grid_buttons[(new_x, new_y)] = self

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            if self.main_window:
                self.main_window.save_layout()
            self.is_dragging = False
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
        self.setWindowTitle("Harnice")
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
        self.load_button.move(
            x - self.load_button.width() // 2, y - self.load_button.height() // 2
        )
        self.grid.grid_buttons[(0, 0)] = self.load_button

        self._is_initializing = True
        self.load_layout()

        # Set window size after loading layout (if any)
        self.apply_window_size()
        self._is_initializing = False

    def resizeEvent(self, event):
        self.grid.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)
        # Save layout when window is manually resized
        if hasattr(self, "load_button") and not getattr(
            self, "_is_initializing", False
        ):
            self.save_layout()

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select revision folder")
        if not folder:
            return

        gx, gy = self.find_next_grid_position()
        label = os.path.basename(folder)

        btn = PartButton(self.grid, label, folder, gx, gy, main_window=self)
        btn.clicked.connect(lambda checked=False, p=folder: self.run_render(p))
        self.grid.grid_buttons[(gx, gy)] = btn
        self.save_layout()

    def find_next_grid_position(self):
        for y in range(200):
            for x in range(200):
                if not self.grid.is_grid_occupied(x, y):
                    return (x, y)

    def run_render(self, cwd):
        btn = next(
            (
                b
                for b in self.grid.grid_buttons.values()
                if isinstance(b, PartButton) and b.path == cwd
            ),
            None,
        )

        if btn:
            btn.setStyleSheet(
                btn.default_style + " QPushButton { border: 3px solid #22aa22; } "
            )

        self.thread = QThread()
        self.worker = RenderWorker(cwd, False)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(
            lambda success, error_msg: self.on_render_finished(btn, success, error_msg)
        )
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_render_finished(self, btn, success, error_msg):
        if not btn:
            return

        if success:
            # ✅ Restore original intended appearance
            btn.setStyleSheet(btn.default_style)
            btn.update()
        else:
            btn.setStyleSheet(
                btn.default_style + " QPushButton { border: 3px solid #cc3333; } "
            )
            # Print error message and traceback to console in color
            if error_msg:
                # ANSI color codes
                RED = "\033[91m"
                BOLD = "\033[1m"
                RESET = "\033[0m"
                YELLOW = "\033[93m"

                print(f"\n{RED}{BOLD}{'=' * 80}{RESET}")
                print(f"{RED}{BOLD}ERROR in {YELLOW}{btn.path}{RESET}{RED}:{RESET}")
                print(f"{RED}{BOLD}{'=' * 80}{RESET}")
                print(f"{RED}{error_msg}{RESET}")
                print(f"{RED}{BOLD}{'=' * 80}{RESET}\n")

    def remove_button(self, button):
        self.grid.grid_buttons.pop((button.grid_x, button.grid_y), None)
        button.deleteLater()
        self.save_layout()

    def new_rev(self, button):
        """
        Run harnice --newrev from the button's directory.
        """
        import harnice.cli

        old_cwd = os.getcwd()
        os.chdir(button.path)

        try:
            sys.argv = ["harnice", "--newrev"]
            try:
                harnice.cli.main()
            except SystemExit:
                pass
        finally:
            os.chdir(old_cwd)

    def save_layout(self):
        data = {
            "window": {
                "width": self.width(),
                "height": self.height(),
            },
            "buttons": [
                {
                    "label": b.text(),
                    "path": b.path,
                    "grid_x": b.grid_x,
                    "grid_y": b.grid_y,
                    "product_type": getattr(b, "product_type", None) or "",
                }
                for (gx, gy), b in self.grid.grid_buttons.items()
                if isinstance(b, PartButton)
            ],
        }

        with open(layout_config_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_layout(self):
        cfg = layout_config_path()
        if not cfg.exists():
            return

        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except Exception:
            return

        # Handle old format (array of buttons) vs new format (dict with buttons and window)
        if isinstance(data, list):
            items = data
            self.saved_window_size = None
        else:
            items = data.get("buttons", [])
            window_info = data.get("window")
            if window_info:
                self.saved_window_size = (
                    window_info.get("width"),
                    window_info.get("height"),
                )
            else:
                self.saved_window_size = None

        for item in items:
            btn = PartButton(
                self.grid,
                item["label"],
                item["path"],
                item["grid_x"],
                item["grid_y"],
                main_window=self,
                product_type=item.get("product_type") or None,
            )
            btn.clicked.connect(
                lambda checked=False, p=item["path"]: self.run_render(p)
            )
            self.grid.grid_buttons[(item["grid_x"], item["grid_y"])] = btn

    def apply_window_size(self):
        if hasattr(self, "saved_window_size") and self.saved_window_size:
            width, height = self.saved_window_size
            self.resize(width, height)
            self.grid.setGeometry(0, 0, width, height)


def main():
    app = QApplication([])
    gui = HarniceGUI()
    gui.show()
    app.exec()


if __name__ == "__main__":
    main()
