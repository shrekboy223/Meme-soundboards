from PySide6.QtWidgets import QApplication

from app.ui import MainWindow, apply_theme


def main() -> None:
    app = QApplication([])
    apply_theme(app)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
