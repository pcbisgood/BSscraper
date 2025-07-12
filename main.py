import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QRadioButton, QHBoxLayout, QButtonGroup, QPushButton, QWidget, QTableWidget, QProgressBar, QTableWidgetItem, QStackedWidget, QMessageBox, QCheckBox, QHeaderView
)
from PyQt5.QtGui import QFont, QPixmap, QIcon  
from PyQt5.QtCore import Qt

from functional import WorkerThread, WorkerThreadGermanyAsync, WorkerThreadChocolate, REGIONI_ITALIA


import ctypes
import warnings
import os
from time import sleep

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
logo_path = resource_path('resources/logo.png')
icon_path = resource_path('resources/icon.ico')
myappid = 'yomidev.yomicorp.mailscraper.1-0' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(" [Y-Corp] Business Scrapers 🐼")
        self.setWindowIcon(QIcon(icon_path))

        self.resize(600, 400)
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_intro_screen()
        self.init_table_screen()

        # Usa un timer per garantire che la finestra venga portata in primo piano dopo essere stata mostrata
        QTimer.singleShot(0, self.bring_to_front)

    def bring_to_front(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.force_foreground()

    def force_foreground(self):
        hwnd = int(self.winId())
        ctypes.windll.user32.SetForegroundWindow(hwnd)

    def showEvent(self, event):
        self.activateWindow()
        self.raise_()
        self.show()
        super().showEvent(event)

    def init_intro_screen(self):
        intro_widget = QWidget()
        intro_layout = QVBoxLayout()

        logo_label = QLabel(self)
        pixmap = QPixmap(logo_path)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        intro_layout.addWidget(logo_label)

        self.radio_pizza = QRadioButton("🍕", self)
        self.radio_pizza.setFont(QFont("Arial", 50))
        self.radio_beer = QRadioButton("🍺", self)
        self.radio_beer.setFont(QFont("Arial", 50))
        self.radio_chocolate = QRadioButton('🍫')
        self.radio_chocolate.setFont(QFont("Arial", 50))
        
        radio_layout = QHBoxLayout()
        radio_layout.addStretch()
        radio_layout.addWidget(self.radio_pizza)
        radio_layout.addStretch()
        radio_layout.addWidget(self.radio_beer)
        radio_layout.addStretch()
        radio_layout.addWidget(self.radio_chocolate)
        radio_layout.addStretch()
        
        self.radio_group = QButtonGroup(self)
        self.radio_group.addButton(self.radio_pizza)
        self.radio_group.addButton(self.radio_beer)
        self.radio_group.addButton(self.radio_chocolate)
        intro_layout.addLayout(radio_layout)

        next_button = QPushButton("Next", self)
        next_button.clicked.connect(self.show_table_screen)
        intro_layout.addWidget(next_button)

        self.made_by_label_intro = QLabel("Made By Yomi With ☕ & 💛", self)
        self.made_by_label_intro.setFont(QFont("Arial", 10))
        self.made_by_label_intro.setAlignment(Qt.AlignCenter)
        intro_layout.addWidget(self.made_by_label_intro)

        intro_widget.setLayout(intro_layout)
        self.stacked_widget.addWidget(intro_widget)

    def init_table_screen(self):
        table_widget = QWidget()
        self.layout = QVBoxLayout()

        self.table_widget = QTableWidget(0, 2, self)
        self.table_widget.setHorizontalHeaderLabels(["Attivita", "Dove"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table_widget)

        self.add_row_button = QPushButton("Add Row", self)
        self.add_row_button.clicked.connect(self.add_row)
        self.layout.addWidget(self.add_row_button)

        self.remove_row_button = QPushButton("Remove Row", self)
        self.remove_row_button.clicked.connect(self.remove_row)
        self.layout.addWidget(self.remove_row_button)

        self.tutto_il_territorio_checkbox = QCheckBox("Tutto il Territorio", self)
        self.tutto_il_territorio_checkbox.setStyleSheet("color: #90caf9")
        self.tutto_il_territorio_checkbox.stateChanged.connect(self.toggle_dove_column)
        self.layout.addWidget(self.tutto_il_territorio_checkbox)

        self.progress_label = QLabel("", self)
        self.progress_label.setFont(QFont("Arial", 12))
        self.layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { background-color: #555555; color: #ffffff; }")
        self.layout.addWidget(self.progress_bar)

        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_processing)
        self.start_button.setStyleSheet("background-color: #777777; color: #ffffff;")
        self.layout.addWidget(self.start_button)

        self.made_by_label = QLabel("Made By Yomi With ☕ & 💛", self)
        self.made_by_label.setFont(QFont("Arial", 10))
        self.made_by_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.made_by_label)

        table_widget.setLayout(self.layout)
        self.stacked_widget.addWidget(table_widget)

    def show_table_screen(self):
        self.stacked_widget.setCurrentIndex(1)

    def add_row(self):
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        for column in range(self.table_widget.columnCount()):
            item = QTableWidgetItem()
            item.setBackground(Qt.white)
            item.setForeground(Qt.black)
            self.table_widget.setItem(row_position, column, item)

    def remove_row(self):
        current_row = self.table_widget.currentRow()
        if current_row >= 0:
            self.table_widget.removeRow(current_row)
        else:
            QMessageBox.warning(self, "Warning", "Please select a row to remove.")

    def toggle_dove_column(self, state):
        dove_column_enabled = not bool(state)
        self.table_widget.setColumnHidden(1, not dove_column_enabled)
        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, 1)
            if item:
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled if dove_column_enabled else Qt.NoItemFlags)

    def start_processing(self):
        data = []
        tutto_il_territorio = self.tutto_il_territorio_checkbox.isChecked()
        
        for row in range(self.table_widget.rowCount()):
            attivita_item = self.table_widget.item(row, 0)
            dove_item = self.table_widget.item(row, 1)
            attivita = attivita_item.text() if attivita_item else ""
            dove = dove_item.text() if dove_item else ""
            if attivita:
                if tutto_il_territorio:
                    if self.radio_pizza.isChecked():
                        for regione in REGIONI_ITALIA:
                            data.append((attivita, regione))
                    else:
                        data.append((attivita, ""))
                else:
                    data.append((attivita, dove))

        if data:
            if self.radio_pizza.isChecked():
                self.worker_thread = WorkerThread(data, tutto_il_territorio)
            elif self.radio_beer.isChecked():
                self.worker_thread = WorkerThreadGermanyAsync(data, tutto_il_territorio)
            elif self.radio_chocolate.isChecked():
                self.worker_thread = WorkerThreadChocolate(data, tutto_il_territorio)

            self.worker_thread.progress_update.connect(self.update_progress)
            self.worker_thread.finished.connect(self.processing_finished)
            self.worker_thread.start()

            self.start_button.setVisible(False)
            self.progress_bar.setVisible(True)
        else:
            QMessageBox.warning(self, "Warning", "Please fill in the activity field for all rows.")

    def update_progress(self, percentage, message):
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(f"<font color='#90caf9'>{message}: {percentage}%</font>")
        self.progress_label.adjustSize()

    def processing_finished(self):
        self.style_msgbox()
        QMessageBox.information(self, "Information", "Processing finished. Cleaned data saved to result.csv")
        self.reset_ui()

    def style_msgbox(self):
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMessageBox):
                widget.setStyleSheet("QLabel { color: #000000; }")

    def reset_ui(self):
        self.stacked_widget.setCurrentIndex(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.start_button.setVisible(True)
        self.table_widget.setRowCount(0)
        self.progress_label.setText("")



if __name__ == "__main__":
    app = QApplication(sys.argv)

    style_sheet = """
        QMainWindow {
            background-color: #333333;
            color: #ffffff;
        }

        QLabel {
            color: #ffffff;
        }

        QProgressBar {
            background-color: #555555;
            color: #ffffff;
        }

        QPushButton {
            background-color: #000301;
            color: #ffffff;
        }
        
        QTableWidget {
            background-color: #ffffff;
            color: #000000;
        }

        QHeaderView::section {
            background-color: #777777;
            color: #ffffff;
        }

        QMessageBox {
            background-color: #ffffff;
        }

        QMessageBox QLabel {
            color: #000000;
        }
    """

    app.setStyleSheet(style_sheet)
    window = MainWindow()
    window.setWindowIcon(QIcon(icon_path))

    window.show()
    sys.exit(app.exec_())
