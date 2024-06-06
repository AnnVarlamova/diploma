import sys
import time
import os
import cv2
import sqlite3
from PySide6.QtCore import Qt, QThread, Signal, Slot, QDate, QDateTime
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QVBoxLayout, QWidget, QScrollArea, QSizePolicy)
from alg import ProcVideo
from PySide6.QtWidgets import QDialog, QDateEdit, QDialogButtonBox, QMessageBox


class Thread(QThread):
    updateFrame = Signal(QImage)

    def __init__(self, procv, parent=None):
        QThread.__init__(self, parent)
        self.status = True
        self.cap = True
        self.current_frame = None  # Store the current frame
        self.procv = procv

    def run(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        while self.status:
            ret, kadr = self.cap.read()
            if not ret:
                continue

            # Reading the image in RGB to display it
            cv2.imwrite("frame.jpg", kadr)
            res = self.procv.frame("frame.jpg")
            color_frame = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)

            # Creating QImage
            h, w, ch = color_frame.shape
            img = QImage(color_frame.data, w, h, ch * w, QImage.Format_RGB888)

            # Store the current frame for resizing
            self.current_frame = img

            # Emit signal
            self.updateFrame.emit(img)
            # time.sleep(0.05)  # Add a short delay to control frame rate
        sys.exit(-1)

    def stop(self):
        self.status = False


class ImageWidget(QWidget):
    imageClicked = Signal(int)  # Signal to indicate that an image has been clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_content = QWidget()
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_content)
        self.scroll_area.setWidget(self.scroll_area_content)
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)
        self.image_paths = []  # Store original image paths

    def add_image(self, image_path):
        self.image_paths.append(image_path)  # Store the original image path

        label = QLabel()
        pixmap = QPixmap(image_path)

        # Scale the image to fill the width of the scroll area
        pixmap_scaled = pixmap.scaledToWidth(self.scroll_area.width())

        label.setPixmap(pixmap_scaled)
        label.setScaledContents(True)  # Scale the contents of the label
        # Connect the clicked signal of the label to the slot for handling image clicks
        label.mousePressEvent = lambda event, index=self.scroll_area_layout.count(): self.handle_image_click(index)
        self.scroll_area_layout.addWidget(label)
        print(f"Image added to layout: {image_path}")  # Отладочная информация

    def handle_image_click(self, index):
        # Emit the imageClicked signal with the index of the clicked image
        self.imageClicked.emit(index)


class CarouselWindow(QDialog):
    def __init__(self, image_paths, start_index):
        super().__init__()

        self.setWindowTitle("Image Carousel")
        self.setModal(True)

        self.image_paths = image_paths
        self.current_index = start_index

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.text_label = QLabel()
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.update_image()

        prev_button = QPushButton("Previous")
        prev_button.clicked.connect(self.show_previous_image)

        next_button = QPushButton("Next")
        next_button.clicked.connect(self.show_next_image)

        button_layout = QHBoxLayout()
        button_layout.addWidget(prev_button)
        button_layout.addWidget(next_button)

        layout = QVBoxLayout()
        layout.addWidget(self.text_label)
        layout.addWidget(self.image_label)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setFixedSize(800, 600)  # Set the fixed window size

    def update_image(self):
        pixmap = QPixmap(self.image_paths[self.current_index])
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.text_label.setText(os.path.basename(self.image_paths[self.current_index]))  # Display file name

    def show_previous_image(self):
        self.current_index = (self.current_index - 1) % len(self.image_paths)
        self.update_image()

    def show_next_image(self):
        self.current_index = (self.current_index + 1) % len(self.image_paths)
        self.update_image()

    def resizeEvent(self, event):
        self.update_image()
        super().resizeEvent(event)


class SelectPeriodDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор периода")
        layout = QVBoxLayout()

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setDate(QDate.currentDate())

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setDate(QDate.currentDate())

        layout.addWidget(QLabel("Начало периода:"))
        layout.addWidget(self.start_date_edit)
        layout.addWidget(QLabel("Конец периода:"))
        layout.addWidget(self.end_date_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def get_period(self):
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()

        if start_date > end_date:
            QMessageBox.warning(self, "Ошибка", "Дата начала периода должна быть меньше или равна дате конца периода.")
            return None

        return start_date.toString(Qt.ISODate), end_date.toString(Qt.ISODate)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        # Title and dimensions
        self.setWindowTitle("Smoking detection")
        self.procv = ProcVideo()

        # Create a label for the display camera
        self.label = QLabel(self)
        self.label.setScaledContents(True)  # Enable scaled contents for label

        # Set fixed size for video label with 16:9 aspect ratio
        self.label.setFixedSize(880, 495)  # 16:9 aspect ratio (1920x1080 scaled down)

        # Set default black image for the label
        self.set_default_image()

        # Buttons layout
        self.button1 = QPushButton("Start")
        self.button2 = QPushButton("Stop")

        # Left layout
        buttons_layout = QHBoxLayout()  # Horizontal layout for buttons
        buttons_layout.addWidget(self.button1)
        buttons_layout.addWidget(self.button2)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.label)
        left_layout.addLayout(buttons_layout)

        # Right layout (empty)
        right_layout = QVBoxLayout()
        self.image_widget = ImageWidget()
        self.image_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Expand the image widget
        self.image_widget.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Expand the scroll area
        right_layout.addWidget(self.image_widget)

        # Add "Show Photos" button to the top of the right layout
        self.show_photos_button = QPushButton("Показать фотографии")
        self.show_photos_button.clicked.connect(self.load_images_from_folder)
        right_layout.addWidget(self.show_photos_button)

        # Add "Select Period" button
        self.select_period_button = QPushButton("Выбрать период")
        self.select_period_button.clicked.connect(self.show_select_period_dialog)
        right_layout.addWidget(self.select_period_button)

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 2)  # Set left layout width ratio to 2
        main_layout.addLayout(right_layout, 1)  # Set right layout width ratio to 1

        # Central widget
        central_widget = QWidget(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Connections
        self.button1.clicked.connect(self.start)
        self.button2.clicked.connect(self.stop)
        self.button2.setEnabled(False)  # Initially disable the "Stop" button

        # Thread instance
        self.th = None

        # Connect the imageClicked signal from ImageWidget to the show_carousel slot
        self.image_widget.imageClicked.connect(self.show_carousel)

    def resizeEvent(self, event):
        # Call the parent class resizeEvent to handle standard resizing behavior
        super().resizeEvent(event)
        # Update the video label size while maintaining aspect ratio
        if self.th and self.th.cap.isOpened():
            self.update_video_size()

    def update_video_size(self):
        # Получение размера метки, где отображается видео
        label_size = self.label.size()

        # Изменение размера видео метки с сохранением пропорций
        if self.th.current_frame:
            pixmap = QPixmap.fromImage(self.th.current_frame)
            pixmap_resized = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(pixmap_resized)

    def set_default_image(self):
        default_image = QImage(640, 360, QImage.Format_RGB888)
        default_image.fill(Qt.black)
        self.label.setPixmap(QPixmap.fromImage(default_image))

    def load_images_from_folder(self):
        folder_path = "detected/cam_0"

        # Очистка текущих изображений в виджете ImageWidget
        for i in reversed(range(self.image_widget.scroll_area_layout.count())):
            widget_to_remove = self.image_widget.scroll_area_layout.itemAt(i).widget()
            self.image_widget.scroll_area_layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
        self.image_widget.image_paths.clear()

        for filename in os.listdir(folder_path):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(folder_path, filename)
                print(image_path)
                self.image_widget.add_image(image_path)

    @Slot()
    def start(self):
        print("Starting...")
        self.button1.setEnabled(False)  # Disable the "Start" button
        self.button2.setEnabled(True)  # Enable the "Stop" button

        self.th = Thread(self.procv)
        self.th.updateFrame.connect(self.set_image)
        self.th.start()

    @Slot()
    def stop(self):
        print("Stopping...")
        self.button2.setEnabled(False)  # Disable the "Stop" button
        self.button1.setEnabled(True)  # Enable the "Start" button
        if self.th:
            self.th.stop()  # Stop the thread

    @Slot(QImage)
    def set_image(self, image):
        self.th.current_frame = image  # Обновление текущего кадра
        pixmap = QPixmap.fromImage(image)
        label_size = self.label.size()

        # Ограничение высоты изображения до 1080 пикселей
        if label_size.height() > 1080:
            label_size.setHeight(1080)

        pixmap_resized = pixmap.scaled(label_size, Qt.KeepAspectRatio)
        self.label.setPixmap(pixmap_resized)

    def show_carousel(self, index):
        image_paths = self.image_widget.image_paths
        carousel_window = CarouselWindow(image_paths, index)
        carousel_window.resize(800, 600)  # Set the desired window size
        carousel_window.exec()

    def get_images_by_period(self, start_date, end_date):
        conn = sqlite3.connect('smoking_pics.db')
        cursor = conn.cursor()

        cursor.execute('''SELECT path FROM фотографии WHERE date BETWEEN ? AND ?''',
                       (start_date, end_date))
        image_paths = [row[0].replace('\\', '/') for row in cursor.fetchall()]

        conn.close()
        return image_paths

    def show_select_period_dialog(self):
        dialog = SelectPeriodDialog(self)
        if dialog.exec() == QDialog.Accepted:
            period = dialog.get_period()
            if period is not None:
                start, end = period
                print("Selected period:", start, end)

                # Получение изображений из базы данных по выбранному периоду
                image_paths = self.get_images_by_period(start, end)

                print("Image paths:", image_paths)  # Отладочная информация

                # Очистка текущих изображений в виджете ImageWidget
                for i in reversed(range(self.image_widget.scroll_area_layout.count())):
                    widget_to_remove = self.image_widget.scroll_area_layout.itemAt(i).widget()
                    self.image_widget.scroll_area_layout.removeWidget(widget_to_remove)
                    widget_to_remove.setParent(None)
                self.image_widget.image_paths.clear()

                # Добавление новых изображений в виджет
                for image_path in image_paths:
                    self.image_widget.add_image(image_path)
                    print(f"Added image: {image_path}")  # Отладочная информация
            else:
                print("Period selection canceled.")
