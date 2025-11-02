import os
import sys
import subprocess
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


class GridWidget(QWidget):
    """Widget with a cartesian grid background"""

    # Button dimensions and margins
    BUTTON_WIDTH = 180
    BUTTON_WIDTH_MARGIN = 20
    BUTTON_HEIGHT = 40
    BUTTON_HEIGHT_MARGIN = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_buttons = {}  # Store buttons by their grid coordinates
        self.setStyleSheet("background-color: white;")
        self.setAutoFillBackground(True)

    @property
    def GRID_SPACING_X(self):
        """Horizontal spacing between grid lines"""
        return self.BUTTON_WIDTH + self.BUTTON_WIDTH_MARGIN

    @property
    def GRID_SPACING_Y(self):
        """Vertical spacing between grid lines"""
        return self.BUTTON_HEIGHT + self.BUTTON_HEIGHT_MARGIN

    @property
    def OFFSET_X(self):
        """X offset for grid position (0,0)"""
        return self.GRID_SPACING_X / 2

    @property
    def OFFSET_Y(self):
        """Y offset for grid position (0,0)"""
        return self.GRID_SPACING_Y / 2

    def paintEvent(self, event):
        """Draw the dotted grid lines"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DotLine)
        painter.setPen(pen)

        width = self.width()
        height = self.height()

        # Draw vertical lines
        x = self.OFFSET_X
        while x < width:
            painter.drawLine(x, 0, x, height)
            x += self.GRID_SPACING_X

        # Draw horizontal lines
        y = self.OFFSET_Y
        while y < height:
            painter.drawLine(0, y, width, y)
            y += self.GRID_SPACING_Y

    def grid_to_screen(self, grid_x, grid_y):
        """Convert grid coordinates to screen pixel coordinates"""
        return (
            grid_x * self.GRID_SPACING_X + self.OFFSET_X,
            grid_y * self.GRID_SPACING_Y + self.OFFSET_Y,
        )

    def screen_to_grid(self, screen_x, screen_y):
        """Convert screen pixel coordinates to grid coordinates"""
        return (
            int((screen_x - self.OFFSET_X) / self.GRID_SPACING_X),
            int((screen_y - self.OFFSET_Y) / self.GRID_SPACING_Y),
        )

    def is_grid_occupied(self, grid_x, grid_y, exclude=None):
        """Check if a grid position is already occupied by a button"""
        button = self.grid_buttons.get((grid_x, grid_y))
        return button is not None and button != exclude


class PartButton(QPushButton):
    """Button that displays a part path and can be dragged"""

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
        """Update button position based on its grid coordinates"""
        screen_x, screen_y = self.parent_grid.grid_to_screen(self.grid_x, self.grid_y)
        self.move(screen_x - self.width() // 2, screen_y - self.height() // 2)

    def mousePressEvent(self, event):
        """Store drag start position"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragStartPosition = event.position().toPoint()
            self.is_dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle dragging to move button to new grid crossing"""
        if (
            not (event.buttons() & Qt.MouseButton.LeftButton)
            or not self.dragStartPosition
        ):
            return

        if (event.position().toPoint() - self.dragStartPosition).manhattanLength() < 50:
            return

        self.is_dragging = True
        old_grid_x = self.grid_x
        old_grid_y = self.grid_y

        global_pos = self.mapToGlobal(event.position().toPoint())
        local_pos = self.parent_grid.mapFromGlobal(global_pos)
        new_grid_x, new_grid_y = self.parent_grid.screen_to_grid(
            local_pos.x(), local_pos.y()
        )

        if new_grid_x == old_grid_x and new_grid_y == old_grid_y:
            return

        if self.parent_grid.is_grid_occupied(new_grid_x, new_grid_y, exclude=self):
            return

        self.grid_x = new_grid_x
        self.grid_y = new_grid_y
        self.update_position()

        self.parent_grid.grid_buttons.pop((old_grid_x, old_grid_y), None)
        self.parent_grid.grid_buttons[(self.grid_x, self.grid_y)] = self

    def mouseReleaseEvent(self, event):
        """Clean up drag state"""
        was_dragging = self.is_dragging
        self.dragStartPosition = None
        self.is_dragging = False

        if was_dragging:
            self.setDown(False)
            event.ignore()
            return

        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        """Show context menu on right-click"""
        if not self.main_window:
            return

        menu = QMenu(self)

        remove_action = menu.addAction("Remove button")
        remove_action.triggered.connect(lambda: self.main_window.remove_button(self))

        newrev_action = menu.addAction("New rev")
        newrev_action.triggered.connect(lambda: self.main_window.new_rev(self))

        menu.exec(event.globalPos())


class HarniceGUI(QWidget):
    """Main window with grid and buttons"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Harnice GUI")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window)

        self.grid = GridWidget(self)

        default_width = self.grid.GRID_SPACING_X * 6
        default_height = self.grid.GRID_SPACING_Y * 2
        self.resize(default_width, default_height)
        self.grid.setGeometry(0, 0, default_width, default_height)

        # Add "Load part for render..." button at (0, 0)
        self.load_button = QPushButton("Load part for render...", self.grid)
        self.load_button.setFixedSize(self.grid.BUTTON_WIDTH, self.grid.BUTTON_HEIGHT)
        self.load_button.clicked.connect(self.pick_folder)
        screen_x, screen_y = self.grid.grid_to_screen(0, 0)
        self.load_button.move(
            screen_x - self.load_button.width() // 2,
            screen_y - self.load_button.height() // 2,
        )
        self.grid.grid_buttons[(0, 0)] = self.load_button

    def resizeEvent(self, event):
        """Handle window resize to make grid fill the window"""
        self.grid.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def closeEvent(self, event):
        """Clean up on close"""
        event.accept()
        sys.exit(0)

    def pick_folder(self):
        """Open file dialog to select a folder and create a button"""
        folder = QFileDialog.getExistingDirectory(self, "Select revision folder")
        if not folder:
            return

        grid_x, grid_y = self.find_next_grid_position()

        label = os.path.basename(folder)
        button = PartButton(self.grid, label, folder, grid_x, grid_y, main_window=self)
        button.clicked.connect(lambda checked=False, p=folder: self.render_part(p))
        self.grid.grid_buttons[(grid_x, grid_y)] = button

    def find_next_grid_position(self):
        """Find the next available grid crossing"""
        for grid_y in range(100):
            for grid_x in range(100):
                if not self.grid.is_grid_occupied(grid_x, grid_y):
                    return (grid_x, grid_y)
        return (0, 1)

    def render_part(self, cwd):
        """Run harnice render on the selected part (non-blocking)"""
        try:
            subprocess.Popen(
                [sys.executable, "-m", "harnice", "-r"],
                cwd=cwd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True if os.name != "nt" else False,
            )
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Could not run harnice")

    def remove_button(self, button):
        """Remove a button from the grid"""
        self.grid.grid_buttons.pop((button.grid_x, button.grid_y), None)
        button.deleteLater()

    def new_rev(self, button):
        """Create a new revision by calling harnice --newrev in the button's directory (non-blocking)"""
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "harnice", "--newrev"],
                cwd=button.path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True if os.name != "nt" else False,
            )

            from PySide6.QtCore import QTimer

            def check_result():
                try:
                    stdout, stderr = process.communicate(timeout=0.1)
                except subprocess.TimeoutExpired:
                    return

                if process.returncode == 0:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"New revision created successfully.\n\n{stdout}",
                    )
                else:
                    error_msg = stderr or stdout or "Unknown error"
                    QMessageBox.warning(
                        self,
                        "Warning",
                        f"New revision creation completed with warnings:\n\n{error_msg}",
                    )

            QTimer.singleShot(100, check_result)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Could not run harnice --newrev")


def main():
    app = QApplication([])
    gui = HarniceGUI()
    gui.show()
    app.exec()


if __name__ == "__main__":
    main()
