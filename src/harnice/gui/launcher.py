import os
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

    def __init__(self, parent, label, path, grid_x, grid_y, main_window=None):
        super().__init__(label, parent)
        self.parent_grid = parent
        self.path = path
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.main_window = (
            main_window  # Reference to HarniceGUI for context menu actions
        )
        self.button_color = None  # Store current button color

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

    def contextMenuEvent(self, event):
        """Show context menu on right-click"""
        if not self.main_window:
            return

        menu = QMenu(self)

        # Remove button action
        remove_action = menu.addAction("Remove button")
        remove_action.triggered.connect(lambda: self.main_window.remove_button(self))

        # Replace button action
        replace_action = menu.addAction("Replace button")
        replace_action.triggered.connect(lambda: self.main_window.replace_button(self))

        # New rev action
        newrev_action = menu.addAction("New rev")
        newrev_action.triggered.connect(lambda: self.main_window.new_rev(self))

        # Change button color action with submenu
        color_menu = menu.addMenu("Change button color")
        colors = self.main_window.get_color_list()
        for color_name, color_value in colors.items():
            color_action = color_menu.addAction(color_name)
            # Use default arguments to capture loop variables correctly
            color_action.triggered.connect(
                lambda checked=False,
                c=color_value,
                n=color_name: self.main_window.change_button_color(self, c, n)
            )

        menu.exec(event.globalPos())


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
        button = PartButton(self.grid, label, folder, grid_x, grid_y, main_window=self)
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
            QMessageBox.critical(self, "Error", "Could not run harnice")

    def remove_button(self, button):
        """Remove a button from the grid"""
        # Remove from grid_buttons dictionary
        self.grid.grid_buttons.pop((button.grid_x, button.grid_y), None)
        # Delete the button widget
        button.deleteLater()

    def replace_button(self, button):
        """Replace button with a new folder path"""
        folder = QFileDialog.getExistingDirectory(self, "Select new revision folder")
        if not folder:
            return

        # Update button properties
        button.path = folder
        button.setText(os.path.basename(folder))

        # Disconnect old signal and connect new one
        button.clicked.disconnect()
        button.clicked.connect(lambda checked=False, p=folder: self.render_part(p))

    def new_rev(self, button):
        """Create a new revision by calling harnice --newrev in the button's directory"""
        try:
            result = subprocess.run(
                ["harnice", "--newrev"], cwd=button.path, capture_output=True, text=True
            )

            if result.returncode == 0:
                QMessageBox.information(
                    self,
                    "Success",
                    f"New revision created successfully.\n\n{result.stdout}",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"New revision creation completed with warnings:\n\n{result.stderr or result.stdout}",
                )
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Could not run harnice --newrev")
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Error creating new revision: {str(e)}"
            )

    def change_button_color(self, button, color_value, color_name):
        """Change the background color of a button"""
        button.button_color = color_value
        if color_value is None:
            # Reset to default (clear stylesheet)
            button.setStyleSheet("")
        else:
            button.setStyleSheet(f"background-color: {color_value};")

    def get_color_list(self):
        """Return a dictionary of common color names and their hex values"""
        return {
            "Default": None,
            "Red": "#FF0000",
            "Green": "#00FF00",
            "Blue": "#0000FF",
            "Yellow": "#FFFF00",
            "Orange": "#FFA500",
            "Purple": "#800080",
            "Pink": "#FFC0CB",
            "Brown": "#A52A2A",
            "Black": "#000000",
            "White": "#FFFFFF",
            "Gray": "#808080",
            "Light Gray": "#D3D3D3",
            "Dark Gray": "#A9A9A9",
            "Cyan": "#00FFFF",
            "Magenta": "#FF00FF",
            "Lime": "#00FF00",
            "Olive": "#808000",
            "Navy": "#000080",
            "Teal": "#008080",
            "Maroon": "#800000",
            "Gold": "#FFD700",
            "Silver": "#C0C0C0",
            "Coral": "#FF7F50",
            "Salmon": "#FA8072",
            "Turquoise": "#40E0D0",
            "Violet": "#EE82EE",
            "Indigo": "#4B0082",
            "Beige": "#F5F5DC",
            "Khaki": "#F0E68C",
            "Lavender": "#E6E6FA",
            "Mint": "#98FB98",
            "Peach": "#FFDAB9",
        }


def main():
    app = QApplication([])
    gui = HarniceGUI()
    gui.show()
    app.exec()


if __name__ == "__main__":
    main()
