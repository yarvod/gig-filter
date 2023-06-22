from PyQt6.QtWidgets import QGroupBox


class GroupBox(QGroupBox):
    def __init__(self, parent):
        super().__init__(parent)
        font = self.font()
        # Set bold font for all
        font.setBold(True)
        self.setFont(font)
        # Set normal font for children
        font.setBold(False)
        for child in self.children():
            child.setFont(font)
