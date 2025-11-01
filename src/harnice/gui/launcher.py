import os
import subprocess
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog
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
        self.setAcceptDrops(True)
        self.grid_buttons = {}  # Store buttons by their grid coordinates
        # Set background color to make grid visible
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

        # Set pen to dotted line style
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

    def __init__(self, parent, label, path, grid_x, grid_y):
        super().__init__(label, parent)
        self.parent_grid = parent
        self.path = path
        self.grid_x = grid_x
        self.grid_y = grid_y

        # Position button at grid crossing using parametrized dimensions
        self.setFixedSize(parent.BUTTON_WIDTH, parent.BUTTON_HEIGHT)
        self.setAcceptDrops(True)
        self.dragStartPosition = None
        self.is_dragging = False

        # Make sure button is visible
        self.show()

        # Position immediately
        self.update_position()

    def update_position(self):
        """Update button position based on its grid coordinates"""
        screen_x, screen_y = self.parent_grid.grid_to_screen(self.grid_x, self.grid_y)
        # Center the button on the grid crossing
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

        # Start drag if mouse moved enough
        if (event.position().toPoint() - self.dragStartPosition).manhattanLength() < 10:
            return

        # Mark as dragging
        self.is_dragging = True

        # Store old position before updating
        old_grid_x = self.grid_x
        old_grid_y = self.grid_y

        # Convert current position to grid coordinates
        global_pos = self.mapToGlobal(event.position().toPoint())
        local_pos = self.parent_grid.mapFromGlobal(global_pos)
        new_grid_x, new_grid_y = self.parent_grid.screen_to_grid(
            local_pos.x(), local_pos.y()
        )

        # Only update if position actually changed
        if new_grid_x == old_grid_x and new_grid_y == old_grid_y:
            return

        # Move to new position if valid and not occupied
        if self.parent_grid.is_grid_occupied(new_grid_x, new_grid_y, exclude=self):
            return

        self.grid_x = new_grid_x
        self.grid_y = new_grid_y
        self.update_position()

        # Mark old position as free and new as occupied
        self.parent_grid.grid_buttons.pop((old_grid_x, old_grid_y), None)
        self.parent_grid.grid_buttons[(self.grid_x, self.grid_y)] = self

    def mouseReleaseEvent(self, event):
        """Clean up drag state"""
        if self.is_dragging:
            # Prevent click event after dragging
            self.dragStartPosition = None
            self.is_dragging = False
            self.setDown(False)  # Release button visual state
            event.ignore()  # Don't process further
            return
        self.dragStartPosition = None
        self.is_dragging = False
        super().mouseReleaseEvent(event)


class HarniceGUI(QWidget):
    """Main window with grid and buttons"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Harnice GUI")

        # Window floats on top
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window)

        # Create grid widget first to access its spacing properties
        self.grid = GridWidget(self)

        # Set default size to show 5 horizontal and 1 vertical grid crossings
        default_width = self.grid.GRID_SPACING_X * 6  # 0 through 5 horizontal crosses
        default_height = self.grid.GRID_SPACING_Y * 2  # 0 through 1 vertical cross
        self.resize(default_width, default_height)
        self.grid.setGeometry(0, 0, default_width, default_height)

        # Add "Load part for render..." button at (0, 0)
        self.load_button = QPushButton("Load part for render...", self.grid)
        self.load_button.setFixedSize(self.grid.BUTTON_WIDTH, self.grid.BUTTON_HEIGHT)
        self.load_button.clicked.connect(self.pick_folder)
        # Position button at grid crossing (0, 0)
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

    def pick_folder(self):
        """Open file dialog to select a folder and create a button"""
        folder = QFileDialog.getExistingDirectory(self, "Select revision folder")
        if not folder:
            return

        # Find next available grid position (skip (0,0) as it's the load button)
        grid_x, grid_y = self.find_next_grid_position()

        # Create button with folder name as label
        label = os.path.basename(folder)
        button = PartButton(self.grid, label, folder, grid_x, grid_y)
        button.clicked.connect(lambda checked=False, p=folder: self.render_part(p))

        # Store button at grid position
        self.grid.grid_buttons[(grid_x, grid_y)] = button

    def find_next_grid_position(self):
        """Find the next available grid crossing"""
        # Start searching from (0, 0) and go through rows
        for grid_y in range(100):  # Reasonable limit
            for grid_x in range(100):  # Reasonable limit
                if not self.grid.is_grid_occupied(grid_x, grid_y):
                    return (grid_x, grid_y)
        return (0, 1)  # Fallback

    def render_part(self, cwd):
        """Run harnice render on the selected part"""
        try:
            subprocess.run(["harnice", "-r"], cwd=cwd)
        except FileNotFoundError:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", "Could not run harnice")


def main():
    app = QApplication([])
    gui = HarniceGUI()
    gui.show()
    app.exec()


if __name__ == "__main__":
    main()
