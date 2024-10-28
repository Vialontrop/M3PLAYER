from PyQt5 import QtCore, QtGui, QtWidgets,QtMultimedia
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QSlider, QListWidget, QDialog, QInputDialog, QDialogButtonBox, QVBoxLayout, QFileDialog,QStyleOptionSlider,QStyle
from PyQt5.QtGui import QPixmap, QPainter, QTransform,QFontDatabase ,QFont, QPainter, QColor, QLinearGradient, QBrush, QPen 
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt ,QUrl
from mutagen.mp3 import MP3
import librosa , os.path ,numpy as np, sys
from mutagen import MutagenError
from PIL import Image, ImageDraw
import io
import sys
import os 
from PyQt5.QtCore import pyqtSignal
import weakref
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu
from PyQt5.QtGui import QPalette, QColor


# Получаем путь к директории, в которой находится исполняемый файл
if getattr(sys, 'frozen', False):
    # Если мы запущены как исполняемый файл
    base_dir = os.path.dirname(sys.executable)
else:
    # Если мы запущены как обычный скрипт
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Создаем относительный путь к ресурсам
image_path = os.path.join(base_dir, "img", "image.png")
music_path = os.path.join(base_dir, "Music", "music.mp3")
font_path = os.path.join(base_dir, "Minecraft Rus", "font.ttf")


class DoubleClickablePushButton(QPushButton):
    doubleClicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(DoubleClickablePushButton, self).__init__(*args, **kwargs)
        self.single_click_timer = QTimer()
        self.single_click_timer.setSingleShot(True)
        self.single_click_timer.timeout.connect(self.single_click_event)
        self.clicked.connect(self.handle_click)

    def handle_click(self):
        if self.single_click_timer.isActive():
            self.single_click_timer.stop()
            self.doubleClicked.emit()
        else:
            self.single_click_timer.start(300)

    def single_click_event(self):
        self.clicked.emit()

class ScrollingTextLabel(QLabel):


    def __init__(self, *args, **kwargs):
        super(ScrollingTextLabel, self).__init__(*args, **kwargs)
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.update_scroll_position)
        self.pause_timer = QTimer(self)
        self.pause_timer.timeout.connect(self.resume_scrolling)
        self.scroll_position = 0
        self.scroll_text = ""
        self.is_scrolling = False
        self.pause_duration = 1000  # Пауза в миллисекундах (1 секунда)

    def setText(self, text):
        super(ScrollingTextLabel, self).setText(text)
        self.scroll_text = text
        self.scroll_position = 0
        if self.fontMetrics().width(text) > self.width():
            self.is_scrolling = True
            self.scroll_timer.start(100)
        else:
            self.is_scrolling = False
            self.scroll_timer.stop()

    def update_scroll_position(self):
        self.scroll_position -= 5
        if abs(self.scroll_position) > self.fontMetrics().width(self.scroll_text):
            self.scroll_timer.stop()
            self.pause_timer.start(self.pause_duration)
        self.update()

    def resume_scrolling(self):
        self.scroll_position = 0
        self.pause_timer.stop()
        self.scroll_timer.start(100)

    def paintEvent(self, event):
        painter = QPainter(self)
        text_width = self.fontMetrics().width(self.scroll_text)
        if text_width > self.width() and self.is_scrolling:
            # Добавляем один пробел между повторами текста
            full_text = self.scroll_text + " " + self.scroll_text
            painter.drawText(self.scroll_position, self.fontMetrics().height(), full_text)
        else:
            painter.drawText(0, self.fontMetrics().height(), self.scroll_text)
        painter.end()

class EqualizerBar(QtWidgets.QWidget):
    def __init__(self, bars, steps, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )

        if isinstance(steps, list):
            self.n_steps = len(steps)
            self.steps = steps
        elif isinstance(steps, int):
            self.n_steps = steps
            self.steps = ['red'] * steps
        else:
            raise TypeError('steps must be a list or int')

        self.n_bars = bars
        self._x_solid_percent = 0.8
        self._y_solid_percent = 0.8
        self._background_color = QtGui.QColor('#F0F0F0')
        self._padding = 25

        self._timer = None
        self.setDecayFrequencyMs(100)
        self._decay = 10

        self._vmin = 0
        self._vmax = 100

        self._values = [0.0] * bars

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)

        brush = QtGui.QBrush()
        brush.setColor(self._background_color)
        brush.setStyle(Qt.SolidPattern)
        rect = QtCore.QRect(0, 0, painter.device().width(), painter.device().height())
        painter.fillRect(rect, brush)

        d_height = painter.device().height() - (self._padding * 2)
        d_width = painter.device().width() - (self._padding * 2)

        step_y = d_height / self.n_steps
        bar_height = step_y * self._y_solid_percent
        bar_height_space = step_y * (1 - self._x_solid_percent) / 2

        step_x = d_width / self.n_bars
        bar_width = step_x * self._x_solid_percent
        bar_width_space = step_x * (1 - self._y_solid_percent) / 2

        for b in range(self.n_bars):
            if b < len(self._values):
                if self._vmax - self._vmin == 0:
                    pc = 0
                else:
                    pc = (self._values[b] - self._vmin) / (self._vmax - self._vmin)

                if pc < 0:
                    pc = 0
                elif pc > 1:
                    pc = 1

                if np.isnan(pc):
                    pc = 0

                n_steps_to_draw = int(pc * self.n_steps)

                for n in range(n_steps_to_draw):
                    if n < len(self.steps):
                        brush.setColor(QtGui.QColor(self.steps[n]))
                        rect = QtCore.QRect(
                            int(self._padding + (step_x * b) + bar_width_space),
                            int(self._padding + d_height - ((1 + n) * step_y) + bar_height_space),
                            int(bar_width),
                            int(bar_height)
                        )
                        painter.fillRect(rect, brush)

        painter.end()

    def sizeHint(self):
        return QtCore.QSize(20, 120)

    def _trigger_refresh(self):
        self.update()

    def setDecay(self, f):
        self._decay = float(f)

    def setDecayFrequencyMs(self, ms):
        if self._timer:
            self._timer.stop()

        if ms:
            self._timer = QtCore.QTimer()
            self._timer.setInterval(ms)
            self._timer.timeout.connect(self._decay_beat)
            self._timer.start()

    def _decay_beat(self):
        self._values = [
            max(0, v - self._decay)
            for v in self._values
        ]
        self.update()

    def setValues(self, v):
        if len(v) != self.n_bars:
            raise ValueError(f"The length of values must be equal to the number of bars ({self.n_bars})")
        self._values = v
        self.update()

    def values(self):
        return self._values

    def setRange(self, vmin, vmax):
        assert float(vmin) < float(vmax)
        self._vmin, self._vmax = float(vmin), float(vmax)

    def setColor(self, color):
        self.steps = [color] * self._bar.n_steps
        self.update()

    def setColors(self, colors):
        self.n_steps = len(colors)
        self.steps = colors
        self.update()

    def setBarPadding(self, i):
        self._padding = int(i)
        self.update()

    def setBarSolidPercent(self, f):
        self._bar_solid_percent = float(f)
        self.update()

    def setBackgroundColor(self, color):
        self._background_color = QtGui.QColor(color)
        self.update()



class CustomizationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")

        # Создаем список доступных пластинок
        self.disc_list = QListWidget()
        self.disc_list.addItems(["Music_disc2", "Music_disc0.2", "Alviss","C418_disc","music_disc3","Music_disc6","music_disc7"])

        # Создаем кнопки ОК и Отмена
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Устанавливаем layout
        layout = QVBoxLayout()
        layout.addWidget(self.disc_list)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_selected_disc(self):
        return self.disc_list.currentItem().text()


class CustomSlider(QtWidgets.QSlider):
    def __init__(self, parent=None):
        super(CustomSlider, self).__init__(parent)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Инициализация опций стиля для слайдера
        option = QStyleOptionSlider()
        self.initStyleOption(option)

       # Рисуем дорожку слайдера
        track_rect = self.rect()
        track_rect.adjust(0, 7, 0, -27)  # Уменьшаем высоту дорожки
        gradient = QLinearGradient(track_rect.topLeft(), track_rect.bottomLeft())
        gradient.setColorAt(0, QColor(100, 100, 100))
        gradient.setColorAt(1, QColor(50, 50, 50))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, 5, 5)

        # Рисуем ползунок
        handle_rect = self.style().subControlRect(QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self)
        handle_rect.adjust(0, -6, 0, 5)  # Увеличиваем размер ползунка
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(150, 150, 150), 2))
        painter.drawEllipse(handle_rect.center(), 10, 10)
       
        # Рисуем белую линию слева от ползунка
        left_rect = QtCore.QRect(track_rect.topLeft(), QtCore.QPoint(handle_rect.left(), track_rect.bottom()))
        painter.fillRect(left_rect, QColor(255, 255, 255))

class CenteredPixmapLabel(QLabel):
    def __init__(self, parent=None):
        super(CenteredPixmapLabel, self).__init__(parent)
        self.pixmap = QPixmap()
        self.record_image = QPixmap()

    def setPixmap(self, pixmap, record_image=None):
        self.pixmap = pixmap
        if record_image:
            self.record_image = record_image
        else:
            self.record_image = QPixmap(pixmap)  # Обновляем record_image при изменении изображения
        self.update_record_image()  # Вызываем функцию для обновления record_image
        self.update()  # Перерисовываем виджет

    def paintEvent(self, event):
        painter = QPainter(self)
        pixmap_rect = self.pixmap.rect()
        label_rect = self.rect()
        pixmap_rect.moveCenter(label_rect.center())
        painter.drawPixmap(pixmap_rect.topLeft(), self.pixmap)

    def update_record_image(self):
        if self.pixmap:
            self.record_image = QPixmap(self.pixmap)

def load_songs_generator(song_paths):
        for song_path in song_paths:
            yield song_path               

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):

        #окно 
        MainWindow.setObjectName("MainWindow")
        MainWindow.setFixedSize(429, 572)
        MainWindow.setFocusPolicy(QtCore.Qt.NoFocus)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)

        
        #иконка окна 
        icon = QtGui.QIcon(os.path.join(base_dir, "img", "icon2.bmp"))
        MainWindow.setWindowIcon(icon)
        self.previous_amplitudes = np.zeros(30)
        self.alpha = 0.025
        self.sensitivity = 1.0
        self.analysis_data = {}

        #шрифт
        minecraft_font_id = QFontDatabase.addApplicationFont(os.path.join(base_dir, "Minecraft Rus", "minecraft.ttf"))
        minecraft_font_families = QFontDatabase.applicationFontFamilies(minecraft_font_id)

         # Флаг для определения, находится ли приложение в фоновом режиме
        self.is_background = False


        # Подключение сигнала о потере фокуса
        MainWindow.windowIconChanged.connect(self.on_window_icon_changed)

        #пуск
        self.Start_button = QtWidgets.QPushButton(self.centralwidget)
        self.Start_button.setGeometry(QtCore.QRect(200, 425, 50, 50))
        self.Start_button.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(os.path.join(base_dir, "img", "pusk.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.Start_button.setIcon(icon1)
        self.Start_button.setIconSize(QtCore.QSize(45, 45))
        self.Start_button.setObjectName("Start_button")
        self.Start_button.clicked.connect(self.pause_and_unpause)
        self.Start_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: transparent;
            }
        """)

        # Инициализация меток для отображения продолжительности и текущего времени трека
        self.trackDurationLabel = QtWidgets.QLabel(self.centralwidget)
        self.trackDurationLabel.setGeometry(QtCore.QRect(330, 390, 100, 20))
        self.trackDurationLabel.setText("00:00")
        minecraft_font_family = minecraft_font_families[0]
        minecraft_font = QFont(minecraft_font_family, 9)  # Размер шрифта
        self.trackDurationLabel.setFont(minecraft_font)
        self.trackPositionLabel = QtWidgets.QLabel(self.centralwidget)
        self.trackPositionLabel.setGeometry(QtCore.QRect(75, 390, 100, 20))
        self.trackPositionLabel.setText("00:00")
        minecraft_font_family = minecraft_font_families[0]
        minecraft_font = QFont(minecraft_font_family, 9)  # Размер шрифта
        self.trackPositionLabel.setFont(minecraft_font)

        #self.loading_overlay = LoadingOverlay(MainWindow)
        #self.loading_overlay.resize(MainWindow.width(), MainWindow.height())
        #self.loading_overlay.show()

        #эквалайзер
        self.equalizer = EqualizerBar(bars=30, steps=20)
        self.equalizer.setColors([
    "#9fccfa",  # Шаг 1
    "#8fb8f8",  # Шаг 2
    "#7fa5f6",  # Шаг 3
    "#6fa1f4",  # Шаг 4
    "#5f9ef2",  # Шаг 5
    "#4f9af0",  # Шаг 6
    "#3f97ee",  # Шаг 7
    "#2f93ec",  # Шаг 8
    "#1f90ea",  # Шаг 9
    "#0f8ce8",  # Шаг 10
    "#0e88e6",  # Шаг 11
    "#0d84e4",  # Шаг 12
    "#0c80e2",  # Шаг 13
    "#0b7ce0",  # Шаг 14
    "#0a78de",  # Шаг 15
    "#0974dc",  # Шаг 16
    "#0870da",  # Шаг 17
    "#076cd8",  # Шаг 18
    "#0668d6",  # Шаг 19
    "#0564d4"   # Шаг 20
]
)

        self.equalizer.setGeometry(QtCore.QRect(95, 480, 250, 100))
        self.equalizer.setParent(MainWindow)
        self.equalizer.lower()

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_visualization)
        
        
        # Моделируем загрузку данных


        #кнопка назад
        self.backbutton = DoubleClickablePushButton(self.centralwidget)
        self.backbutton.setGeometry(QtCore.QRect(50, 400, 100, 100))
        self.backbutton.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(os.path.join(base_dir, "img", "back.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.backbutton.setIcon(icon2)
        self.backbutton.setIconSize(QtCore.QSize(50, 50))
        self.backbutton.setObjectName("backbutton")

        self.backbutton.clicked.connect(self.single_click_action)
        self.backbutton.doubleClicked.connect(self.double_click_action)
        self.backbutton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: transparent;
            }
        """)

        #кнопка вперёд
        self.nextbutton = QtWidgets.QPushButton(self.centralwidget)
        self.nextbutton.setGeometry(QtCore.QRect(290, 400, 100, 100))
        self.nextbutton.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(os.path.join(base_dir, "img", "next.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.nextbutton.setIcon(icon3)
        self.nextbutton.setIconSize(QtCore.QSize(50, 50))
        self.nextbutton.setObjectName("nextbutton")
        self.nextbutton.clicked.connect(self.next_song)
        self.nextbutton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: transparent;
            }
        """)

        #кнопка паузы
        self.Pausebutton = QtWidgets.QPushButton(self.centralwidget)
        self.Pausebutton.setGeometry(QtCore.QRect(170, 400, 100, 100))
        self.Pausebutton.setStyleSheet("")
        self.Pausebutton.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(os.path.join(base_dir, "img", "pause.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.Pausebutton.setIcon(icon4)
        self.Pausebutton.setIconSize(QtCore.QSize(50, 50))
        self.Pausebutton.setObjectName("Pausebutton")
        self.Pausebutton.hide()
        self.Pausebutton.clicked.connect(self.pause_and_unpause)
        self.Pausebutton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: transparent;
            }
        """)

        # Добавление QTabWidget в главное окно
        self.tab_widget = QtWidgets.QTabWidget(self.centralwidget)
        self.tab_widget.setGeometry(QtCore.QRect(10, 10, 410, 500))
        self.tab_widget.hide()

        self.animation = QPropertyAnimation(self.tab_widget, b"geometry")
        self.animation.setDuration(500)  # Длительность анимации в миллисекундах
        self.animation.setStartValue(QtCore.QRect(10, 510, 410, 0))  # Начальная геометрия
        self.animation.setEndValue(QtCore.QRect(10, 10, 410, 510))  # Конечная геометрия
        self.animation.setEasingCurve(QEasingCurve.OutQuad)  # Тип анимации

        # Создание вкладки для списка треков
        self.track_list_tab = QtWidgets.QWidget()
        self.track_list_tab_layout = QtWidgets.QVBoxLayout(self.track_list_tab)

        # QListWidget для отображения списка треков
        self.track_list_widget = QtWidgets.QListWidget(self.track_list_tab)
        self.track_list_widget.setStyleSheet("""
            QListWidget::item {
                margin: 4px;  /* Настройте значение поля по мере необходимости */
            }
        """)
        self.track_list_tab_layout.addWidget(self.track_list_widget)
        self.track_list_tab.raise_()

        self.tab_widget.addTab(self.track_list_tab, "Треки")
        minecraft_font_family = minecraft_font_families[0]
        minecraft_font = QFont(minecraft_font_family, 12)  # Размер шрифта
        self.track_list_widget.setFont(minecraft_font)
        self.tab_widget.setFont(minecraft_font)

        # Инициализация иконки в трее
        self.tray_icon = QSystemTrayIcon(MainWindow)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setVisible(True)

        # Создание меню для иконки в трее
        self.tray_menu = QMenu()
        self.show_action = self.tray_menu.addAction("Show")
        self.hide_action = self.tray_menu.addAction("Hide")
        self.theme_action = self.tray_menu.addAction("Toggle Dark Theme")
        self.quit_action = self.tray_menu.addAction("Quit")


        self.tray_icon.setContextMenu(self.tray_menu)

        # Подключение действий
        self.show_action.triggered.connect(MainWindow.show)
        self.hide_action.triggered.connect(MainWindow.hide)
        self.theme_action.triggered.connect(self.toggle_dark_theme)
        self.quit_action.triggered.connect(QApplication.quit)


        # Скрытие главного окна при запуске
        MainWindow.hide()


        # громкость
        self.verticalSlider = QtWidgets.QSlider(self.centralwidget)
        self.verticalSlider.setGeometry(QtCore.QRect(30, 390, 20, 101))
        self.verticalSlider.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider.setMinimum(0)  # Минимальное значение
        self.verticalSlider.setMaximum(100)  # Максимальное значение
        self.verticalSlider.setTickPosition(QSlider.TicksBelow)
        self.verticalSlider.setTickInterval(10)  # Установка интервала между делениями
        self.verticalSlider.sliderMoved[int].connect(lambda value: self.volume_changed(value))

        # индикатор громкости
        self.volume_label = QLabel(self.centralwidget)
        self.volume_label.setGeometry(QtCore.QRect(30, 490, 40, 40))
        self.volume_label.setObjectName("volume_label")
        self.volume_label.setText("0%")
        minecraft_font_family = minecraft_font_families[0]
        minecraft_font = QFont(minecraft_font_family, 9)  # Размер шрифта
        self.volume_label.setFont(minecraft_font)

        # дорожка трека 
        self.customSlider = CustomSlider(self.centralwidget)
        self.customSlider.setGeometry(QtCore.QRect(70, 370, 300, 40))
        self.customSlider.setOrientation(QtCore.Qt.Horizontal)
        self.customSlider.setMinimum(0)
        self.customSlider.setMaximum(100)
        self.customSlider.setTickPosition(QSlider.TicksBelow)
        self.customSlider.setTickInterval(10)
        self.customSlider.sliderMoved[int].connect(lambda: self.player.setPosition(self.customSlider.value()))

        
        # Настройка метки названия трека
        self.label = ScrollingTextLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(110, 310, 220, 30))
        self.label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")

        # Настройка метки артиста
        self.artistLabel = ScrollingTextLabel(self.centralwidget)
        self.artistLabel.setGeometry(QtCore.QRect(110, 345, 220, 30))
        self.artistLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.artistLabel.setObjectName("artistLabel")
        self.artistLabel.setText("")

        # Установка шрифта для метки артиста
        artist_palette = self.artistLabel.palette()
        artist_palette.setColor(self.artistLabel.foregroundRole(), QtGui.QColor('gray'))
        self.artistLabel.setPalette(artist_palette)

        artist_font = QFont(minecraft_font_family, 12)
        artist_font.setWeight(QFont.Light)
        self.artistLabel.setFont(artist_font)
            
        if minecraft_font_families:
            # Устанавливаем шрифт Minecraft для названия трека
            minecraft_font_family = minecraft_font_families[0]
            minecraft_font = QFont(minecraft_font_family, 20)  # Размер шрифта
            self.label.setFont(minecraft_font)
        #обложка 
        self.Cover_label =CenteredPixmapLabel (self.centralwidget)
        self.Cover_label.setGeometry(QtCore.QRect(70, 20, 300, 300))
        self.Cover_label.setStyleSheet("")
        self.Cover_label.setLineWidth(2)
        self.Cover_label.setMidLineWidth(10)
        self.Cover_label.setText("")
        self.Cover_label.setPixmap(QtGui.QPixmap(os.path.join(base_dir, "img", "default_disc.png")))
        self.Cover_label.setScaledContents(False)
        self.Cover_label.setObjectName("Cover_label")
        self.record_image = QPixmap("img/default_disc.png")

       

        # кнопка кастомизации 
        self.customizationButton = QtWidgets.QPushButton(self.centralwidget)
        self.customizationButton.setGeometry(QtCore.QRect(185, 135, 70, 70))
        self.customizationButton.setText("")
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(os.path.join(base_dir, "img", "setting.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.customizationButton.setIcon(icon8)
        self.customizationButton.setIconSize(QtCore.QSize(45, 45))
        self.customizationButton.setObjectName("customizationButton")
        self.customizationButton.clicked.connect(self.open_customization_dialog)
        self.customizationButton.setVisible(False)
        self.customizationButton.setStyleSheet("background-color: transparent;")
    
        # Создание виджета, который будет отслеживать наведение курсора
        self.hoverWidget = QtWidgets.QWidget(self.centralwidget)
        self.hoverWidget.setGeometry(QtCore.QRect(195, 145, 70, 70))  # Установите геометрию, которая соответствует вашей кнопке
        self.hoverWidget.setObjectName("hoverWidget")
        self.hoverWidget.enterEvent = self.show_customization_button
        self.hoverWidget.leaveEvent = self.hide_customization_button

        # кнопка загрузки 
        self.Load_button = QtWidgets.QPushButton(self.centralwidget)
        self.Load_button.setGeometry(QtCore.QRect(380, 355, 40, 40))
        self.Load_button.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(os.path.join(base_dir, "img", "plus.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.Load_button.setIcon(icon5)
        self.Load_button.setIconSize(QtCore.QSize(25, 25))
        self.Load_button.setObjectName("Load_button")
        MainWindow.setCentralWidget(self.centralwidget)
        self.Load_button.clicked.connect(self.add_songs)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.Load_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: transparent;
            }
        """)
        # список треков
        self.listButton = QtWidgets.QPushButton(self.centralwidget)
        self.listButton.setGeometry(QtCore.QRect(80,520,40,40))
        self.listButton.setText("")
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap("img/list.png"), QtGui.QIcon.Normal,QtGui.QIcon.Off)
        self.listButton.setIcon(icon7)
        self.listButton.setIconSize(QtCore.QSize(25, 25))
        self.listButton.setObjectName("pushButton_7")
        MainWindow.setCentralWidget(self.centralwidget)
        self.listButton.clicked.connect(self.toggle_track_list_tab)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.listButton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: transparent;
            }
        """)
        self.track_list_widget.itemDoubleClicked.connect(self.play_selected_track)

        # кнопка повтора 
        self.repeatButton = QtWidgets.QPushButton(self.centralwidget)
        self.repeatButton.setGeometry(QtCore.QRect(380,395 , 35, 35))
        self.repeatButton.setText("")
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(os.path.join(base_dir, "img", "repeat.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.repeatButton.setIcon(icon6)
        self.repeatButton.setIconSize(QtCore.QSize(25, 25))
        self.repeatButton.setObjectName("pushButton_6")
        MainWindow.setCentralWidget(self.centralwidget)
        self.repeatButton.toggle()
        self.repeatButton.setCheckable(True)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        

        # кнопка таймера сна 
        self.sleepButton = QtWidgets.QPushButton(self.centralwidget)
        self.sleepButton.setGeometry(QtCore.QRect(325, 520, 40,40))
        self.sleepButton.setText("")
        icon7 =QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(os.path.join(base_dir, "img", "sleeptimer.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sleepButton.setIcon(icon7)
        self.sleepButton.setIconSize(QtCore.QSize(25,25))
        self.sleepButton.setObjectName("sleepButton")
        self.sleepButton.clicked.connect(self.set_sleep_timer)
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        self.sleepButton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: transparent;
            }
        """)
        self.sleepTimerLabel = QtWidgets.QLabel(self.centralwidget)
        self.sleepTimerLabel.setGeometry(QtCore.QRect(380, 520, 40, 20))
        self.sleepTimerLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.sleepTimerLabel.setObjectName("sleepTimerLabel")
        self.sleepTimerLabel.hide()  # Скрыть метку по умолчанию


        font_id = QFontDatabase.addApplicationFont("Minecraft Rus/minecraft.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        minecraft_font3 = QFont(font_family, 9)
        self.sleepTimerLabel.setFont(minecraft_font3)

        # Таймер для вращения пластинки
        self.rotation_timer = QTimer(self.centralwidget)
        self.rotation_timer.timeout.connect(self.rotate_record)
        # создание списка с треками 
        self.current_songs = []

        # устанавливаем уровень громкости
        self.current_volume = 0

        self.current_songs_index = 0
        
        self.rotation_angle = 0
        self.current_song_title = ""

        self.is_dark_theme = False

        self.player = QtMultimedia.QMediaPlayer()
        self.player.setVolume(self.current_volume)

        self.player.mediaStatusChanged.connect(self.check_media_status)

        self.player.durationChanged.connect(self.updateDuration)
        self.player.positionChanged.connect(self.updatePosition)

        # Бегущая строка 
        self.timer = QTimer()
        self.timer.start(100)
        self.timer.timeout.connect(self.move_slider)

        self.Cover_label_ref = weakref.ref(self.Cover_label)
        self.player_ref = weakref.ref(self.player)

    
    def open_customization_dialog(self):
        dialog = CustomizationDialog(self.centralwidget)
        if dialog.exec_():
            selected_disc = dialog.get_selected_disc()
            # Установка новой обложки
            new_pixmap = QtGui.QPixmap(f"img/{selected_disc}.png")
            self.Cover_label.setPixmap(new_pixmap)
            self.record_image = new_pixmap
            # Обновление self.record_image
            self.Cover_label.update_record_image()

    def show_customization_button(self, event):
        self.customizationButton.setVisible(True)
        self.customizationButton.raise_()

    def hide_customization_button(self, event):
        self.customizationButton.setVisible(False)

    def on_window_icon_changed(self):
        self.is_background = not self.is_background
        if self.is_background:
            self.reduce_resource_usage()
        else:
            self.restore_resource_usage()

    
    def reduce_resource_usage(self):
        # Уменьшение частоты обновления таймеров
        self.update_timer.setInterval(500)  # Обновление каждые 500 мс
        self.rotation_timer.setInterval(100)  # Вращение каждые 100 мс

        # Приостановка некритичных задач
        self.rotation_timer.stop()

    def restore_resource_usage(self):
        # Восстановление частоты обновления таймеров
        self.update_timer.setInterval(2)  
        self.rotation_timer.setInterval(36)  # Вращение каждые 36 мс

        # Восстановление выполнения некритичных задач
        if self.player.state() == QMediaPlayer.PlayingState:
            self.rotation_timer.start()    


    
    def update_track_list(self):
        self.track_list_widget.clear()
        for track in self.current_songs:
            artist = self.get_artist_from_file(track)
            title = self.get_song_title(track)
            if artist and title:
                item_text = f"{artist} - {title}"
            else:
                item_text = os.path.basename(track)
            item = QtWidgets.QListWidgetItem(item_text)
            self.track_list_widget.addItem(item)  


    def toggle_dark_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        if self.is_dark_theme:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(28, 28, 28))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)

        QApplication.instance().setPalette(palette)

        # Изменение фона эквалайзера на темный
        self.equalizer.setBackgroundColor(QColor(28, 28, 28))

        self.repeatButton.setStyleSheet("""
            QPushButton {
                background-color: #1c1c1c;
                border: none;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:checked {
                border: 2px solid #4285f4;
            }
        """)
        self.track_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #333333;
                border: 1px solid #555555;
                color: white;
            }
            QListWidget::item {
                margin: 4px;
            }
        """)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555555;
            }
            QTabBar::tab {
                background: #333333;
                color: white;
                padding: 10px;
            }
            QTabBar::tab:selected {
                background: #444444;
            }
        """)
    
        self.sleepTimerLabel.setStyleSheet("""
            QLabel {
                background-color: #333333;
                border: 1px solid #555555;
                color: white;
            }
        """)




    def apply_light_theme(self):
        QApplication.instance().setPalette(QApplication.style().standardPalette())

        # Изменение фона эквалайзера на светлый
        self.equalizer.setBackgroundColor(QColor(240, 240, 240))

        # Изменение цвета кнопки повтора на светлый
        self.repeatButton.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)


    def get_cover_art(self, file_path):
        try:
            f = MP3(file_path)
            if f.tags:
                for frame in f.tags.getall("APIC"):
                    cover_data = frame.data
                    mime_type = frame.mime

                    # Создаем изображение из данных обложки
                    cover_image = Image.open(io.BytesIO(cover_data)).convert("RGBA")

                    # Обрабатываем изображение функцией create_circle_with_hole
                    processed_image = self.create_circle_with_hole(cover_image)

                    # Создаем QPixmap из обработанного изображения
                    processed_pixmap = self.pil_to_qpixmap(processed_image)

                    # Устанавливаем обработанное изображение в качестве обложки
                    self.Cover_label.setPixmap(processed_pixmap)
                    self.record_image = processed_pixmap
                    break
                else:
                    # Если обложки нет, устанавливаем изображение по умолчанию
                    default_pixmap = QPixmap("img/default_disc.png")
                    self.Cover_label.setPixmap(default_pixmap)
                    self.record_image = default_pixmap
            else:
                # Если обложки нет, устанавливаем изображение по умолчанию
                default_pixmap = QPixmap("img/default_disc.png")
                self.Cover_label.setPixmap(default_pixmap)
                self.record_image = default_pixmap
        except MutagenError as e:
            # Если произошла ошибка, устанавливаем изображение по умолчанию
            default_pixmap = QPixmap("img/default_disc.png")
            self.Cover_label.setPixmap(default_pixmap)
            self.record_image = default_pixmap
    
    def previous_song(self):
        if self.player.position() == 0:
            # Если текущее время трека равно 00:00, переключаем на предыдущий трек
            if self.current_songs:
                current_index = self.current_songs_index
                previous_index = (current_index - 1) % len(self.current_songs)

                previous_song_path = self.current_songs[previous_index]
                previous_song_url = QMediaContent(QUrl.fromLocalFile(previous_song_path))
                self.player.setMedia(previous_song_url)
                self.player.play()
                self.rotation_timer.start(36)

                self.Start_button.hide()
                self.Pausebutton.show()
                self.update_song_title(previous_song_path)
                self.current_songs_index = previous_index
        else:
            # Иначе, просто перемотаем трек на начало
            self.player.setPosition(0)


    def update_song_title(self, song_path):
        song_title = self.get_song_title(song_path)
        artist = self.get_artist_from_file(song_path)

        self.label.setText(song_title)  # Используем метод setText для обновления текста
        self.label.setToolTip(os.path.basename(song_path))

        self.artistLabel.setText(artist)

        # Вычисление вертикального смещения для метки артиста
        label_height = self.label.height()
        artist_label_height = self.artistLabel.height()
        vertical_offset = label_height + (artist_label_height // 2)

        # Установка новой геометрии для метки артиста
        self.artistLabel.setGeometry(QtCore.QRect(120, 310 + vertical_offset, 220, 30))

    


    def get_artist_from_file(self, file_path):
        try:
            audio = MP3(file_path)
            if 'TPE1' in audio:
                artist = audio['TPE1'].text[0]
                return artist
            else:
                return "Неизвестный исполнитель"
        except Exception as e:
            print(f"Ошибка при извлечении информации из файла: {e}")
            return "Неизвестный исполнитель"
        
    def get_song_title(self, song_path):
        try:
            audio = MP3(song_path)
            if 'TIT2' in audio:
                title = audio['TIT2'].text[0]
                return title
            else:
                return "Unknown Title"
        except Exception as e:
            print(f"Error reading file: {e}")
            return "Unknown Title"
        


    def rotate_record(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            # Увеличиваем угол поворота на фиксированное значение за каждый тик таймера
            self.rotation_angle += 3  # Увеличиваем угол на 1 градус

            if self.rotation_angle >= 360:
                self.rotation_angle -= 360  # Обнуляем угол, если он достиг 360 градусов
            # Устанавливаем центр вращения на центр изображения
            transform = QTransform()
            transform.translate(self.record_image.width() / 2, self.record_image.height() / 2)
            transform.rotate(self.rotation_angle)
            transform.translate(-self.record_image.width() / 2, -self.record_image.height() / 2)

            rotated_pixmap = self.record_image.transformed(transform)
            self.Cover_label.setPixmap(rotated_pixmap)

    def move_slider(self):
            if self.player.state() == QMediaPlayer.PlayingState:
                self.customSlider.setMinimum(0)
                self.customSlider.setMaximum(self.player.duration())
                slider_position = self.player.position()
                self.customSlider.setValue(slider_position)

    #таймер сна 
    def set_sleep_timer(self):
        dialog = QInputDialog(self.centralwidget)
        dialog.setWindowTitle("Таймер сна")
        dialog.setLabelText("Введите время в минутах:")
        dialog.setInputMode(QInputDialog.IntInput)
        dialog.setIntRange(1, 1440)  # Ограничение от 1 минуты до 24 часов (1440 минут)
        dialog.setIntValue(30)  # Значение по умолчанию: 30 минут
        if dialog.exec_() == QInputDialog.Accepted:
            minutes = dialog.intValue()
            self.start_sleep_timer(minutes)

    def start_sleep_timer(self, minutes):
        self.sleep_timer_duration = minutes * 60  # Длительность таймера в секундах
        self.sleep_timer_remaining = self.sleep_timer_duration  # Оставшееся время в секундах
        self.sleep_timer = QTimer()
        self.sleep_timer.timeout.connect(self.update_sleep_timer)
        self.sleep_timer.start(1000)  # Обновление каждую секунду
        self.sleepTimerLabel.setText(self.format_time(self.sleep_timer_remaining))
        self.sleepTimerLabel.show()  # Показать метку с обратным отсчетом

    def updateDuration(self, duration):
        # Обновление метки длительности трека
        duration_seconds = duration / 1000
        minutes, seconds = divmod(duration_seconds, 60)
        self.trackDurationLabel.setText(f"{int(minutes):02d}:{int(seconds):02d}")

    def updatePosition(self, position):
        # Обновление метки текущего времени трека
        position_seconds = position / 1000
        minutes, seconds = divmod(position_seconds, 60)
        self.trackPositionLabel.setText(f"{int(minutes):02d}:{int(seconds):02d}")

    def stop_playback(self):
        self.player.stop()
        self.Start_button.show()
        self.Pausebutton.hide()
        self.sleep_timer.stop()
        self.sleepTimerLabel.hide()  # Скрыть метку после остановки воспроизведения
    def single_click_action(self):
        self.player.setPosition(0)  # Перемотка текущего трека на начало

    def double_click_action(self):
        if self.current_songs:
            current_index = self.current_songs_index
            previous_index = (current_index - 1) % len(self.current_songs)

            previous_song_path = self.current_songs[previous_index]
            previous_song_url = QMediaContent(QUrl.fromLocalFile(previous_song_path))
            self.player.setMedia(previous_song_url)
            self.player.play()
            self.rotation_timer.start(36)

            self.Start_button.hide()
            self.Pausebutton.show()
            self.update_song_title(previous_song_path)
            self.current_songs_index = previous_index
            self.get_cover_art(previous_song_path)
            self.clear_analysis_data()
            self.analyze_audio(previous_song_path)
            
    def create_circle_with_hole(self, image, width=265, height=265):
        # Проверяем, что изображение имеет нужный размер
        if image.width != width or image.height != height:
            image = image.resize((width, height), Image.LANCZOS)

        # Создаем новое изображение с прозрачным фоном
        circle_image = Image.new('RGBA', (width, height), (255, 255, 255, 0))

        # Рисуем большой круг
        draw = ImageDraw.Draw(circle_image)
        circle_radius = min(width, height) // 2
        circle_center = (width // 2, height // 2)
        draw.ellipse((circle_center[0] - circle_radius, circle_center[1] - circle_radius,
                      circle_center[0] + circle_radius, circle_center[1] + circle_radius),
                     fill=(255, 255, 255, 255))

        # Рисуем маленький круг (отверстие)
        hole_radius = circle_radius // 16
        draw.ellipse((circle_center[0] - hole_radius, circle_center[1] - hole_radius,
                      circle_center[0] + hole_radius, circle_center[1] + hole_radius),
                     fill=(255, 255, 255, 0), outline=(255, 255, 255, 0))

        # Применяем маску к исходному изображению
        result_image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        result_image.paste(image, (0, 0), circle_image)

        return result_image

    def pil_to_qpixmap(self, pil_image):
        data = pil_image.tobytes("raw", "RGBA")
        qimage = QtGui.QImage(data, pil_image.width, pil_image.height, QtGui.QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimage)
    def update_sleep_timer(self):
        self.sleep_timer_remaining -= 1
        if self.sleep_timer_remaining <= 0:
            self.stop_playback()
            self.sleep_timer.stop()
            self.sleepTimerLabel.hide()  # Скрыть метку после окончания таймера
        else:
            self.sleepTimerLabel.setText(self.format_time(self.sleep_timer_remaining))

    def format_time(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MP3 Player"))
        self.label.setText(_translate("MainWindow", ""))

     
        
    #загрузка трека    
    def add_songs(self):
        try:
            # Открываем диалог выбора файлов
            files, _ = QtWidgets.QFileDialog.getOpenFileNames(
                None, "Выберите музыкальные файлы", "music", "Music Files (*.mp3 *.wav *.ogg)")

            if files:
                # Используем генератор для загрузки песен
                song_generator = load_songs_generator(files)
                for song_path in song_generator:
                    if song_path not in self.current_songs:
                        self.current_songs.append(song_path)
                        print(f"Добавлен трек: {os.path.basename(song_path)}")
                # Обновляем список треков
                self.update_track_list()
                # Убедитесь, что play_song вызывается только если это необходимо
                if self.current_songs and self.player.state() == QtMultimedia.QMediaPlayer.StoppedState:
                    self.play_song(self.current_songs[0])

        except Exception as e:
            print(f"Ошибка при добавлении песен: {e}")
    def play_track(self, track_path):

        song_url = QMediaContent(QUrl.fromLocalFile(track_path))
        self.player.setMedia(song_url)
        self.clear_analysis_data()  # Очищаем данные анализа перед новым анализом
        self.analyze_audio(track_path)
        self.player.play()
        self.rotation_timer.start(36)
        self.move_slider()

        self.Start_button.hide()
        self.Pausebutton.show()
        self.label.setText(self.get_song_title(track_path))  # Use the method get_song_title
        self.label.setToolTip(os.path.basename(track_path))

        artist = self.get_artist_from_file(track_path)
        self.artistLabel.setText(artist)

        # Use the saved disc image
        self.Cover_label.setPixmap(self.Cover_label.pixmap)

    def play_selected_track(self, item):
        index = self.track_list_widget.indexFromItem(item)
        track_path = self.current_songs[index.row()]
        self.play_track(track_path)
        
        artist = self.get_artist_from_file(track_path)
        self.update_song_title(track_path)
        self.current_songs_index = index.row()
        self.get_cover_art(track_path)

    
    def play_song(self, song_path):
        self.Start_button.hide()
        self.Pausebutton.show()
        if self.current_songs:
            current_song = song_path
            song_url = QMediaContent(QUrl.fromLocalFile(current_song))
            self.player.setMedia(song_url)
            if self.player.state() == QMediaPlayer.PlayingState:
                self.Pausebutton.hide()
                self.Start_button.show()
                self.rotation_timer.start(36)
                self.update_timer.stop()
            else:
                self.clear_analysis_data()  # Очищаем данные анализа перед новым анализом
                self.analyze_audio(song_path)  # Анализируем аудиофайл перед воспроизведением
                self.player.play()
                self.move_slider()
                self.Start_button.hide()
                self.Pausebutton.show()
                self.rotation_timer.start(36)
                self.update_timer.start(2)
            self.update_song_title(current_song)
            self.get_cover_art(song_path)  

    def analyze_audio(self, file_path):
        y, sr = librosa.load(file_path, sr=None)
        # Нормализация амплитуды
        y_normalized = librosa.util.normalize(y)

        self.stft = np.abs(librosa.stft(y_normalized))
        self.frequencies = librosa.fft_frequencies(sr=sr)
        self.times = librosa.frames_to_time(np.arange(self.stft.shape[1]), sr=sr)

    def clear_resources(self):
        # Очистка изображения обложки
        cover_label = self.Cover_label_ref()
        if cover_label:
            cover_label.clear()
        self.record_image = None

        # Очистка аудиоданных
        self.clear_analysis_data()    

    def clear_analysis_data(self):
        self.stft = None
        self.frequencies = None
        self.times = None

    def update_visualization(self):
        current_time = self.player.position() / 1000
        frame_index = np.argmin(np.abs(self.times - current_time))
        amplitudes = self.stft[:, frame_index]

        # Проверка диапазона частот
        min_frequency = 0
        max_frequency = 20000  # Максимальная частота, которую может обрабатывать человеческое ухо
        frequencies_of_interest = self.frequencies[(self.frequencies >= min_frequency) & (self.frequencies <= max_frequency)]
        amplitudes_of_interest = amplitudes[(self.frequencies >= min_frequency) & (self.frequencies <= max_frequency)]

        amplified_amplitudes = amplitudes_of_interest * self.sensitivity

        max_amplified_amplitude = np.max(amplified_amplitudes)
        if max_amplified_amplitude == 0:
            normalized_amplitudes = np.zeros_like(amplified_amplitudes)
        else:
            normalized_amplitudes = (amplified_amplitudes / max_amplified_amplitude) * 130

        # Использование правильного количества баров
        num_bars = 30
        if len(normalized_amplitudes) < num_bars:
            normalized_amplitudes = np.pad(normalized_amplitudes, (0, num_bars - len(normalized_amplitudes)), 'constant')
        else:
            normalized_amplitudes = normalized_amplitudes[:num_bars]

        smoothed_amplitudes = self.alpha * normalized_amplitudes + (1 - self.alpha) * self.previous_amplitudes

        self.equalizer.setValues(smoothed_amplitudes.tolist())

        self.previous_amplitudes = smoothed_amplitudes
            

    def check_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            if self.repeatButton.isChecked():
                # Если повтор включен, перезапускаем текущую песню
                self.player.play()
                self.rotation_timer.start(36)
            else:
                # Иначе переходим к следующей песне
                self.next_song()
            self.rotation_timer.start(36)

    def pause_and_unpause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.Pausebutton.hide()
            self.Start_button.show()
            self.rotation_timer.stop()
            # Если песня уже играет, то сохраняем текущую позицию и продолжаем воспроизведение
            current_position = self.player.position()
            self.player.pause()  # Останавливаем воспроизведение
            self.player.setPosition(current_position)  # Восстанавливаем позицию после паузы
        else:
            self.player.play()
            self.Start_button.hide()
            self.Pausebutton.show()
            self.rotation_timer.start(36)


    def toggle_track_list_tab(self):
        if self.tab_widget.isVisible():
            # Если вкладка уже видна, закрываем окно
            self.animation.setDirection(QPropertyAnimation.Backward)
            self.animation.start()
            QTimer.singleShot(500, self.do_close_track_list_tab)
        else:
            # Если вкладка скрыта, открываем окно
            self.animation.setDirection(QPropertyAnimation.Forward)
            self.animation.start()
            self.tab_widget.setVisible(True)
            self.tab_widget.raise_()

    def do_close_track_list_tab(self):
        self.tab_widget.setVisible(False)   


    #следующая песня 
    def next_song(self):
        try:
            self.clear_resources()  # Очистка ресурсов перед переключением песни

            current_selection = self.current_songs_index
            if current_selection + 1 == len(self.current_songs):
                next_index = 0
            else:
                next_index = current_selection + 1

            current_song = self.current_songs[next_index]
            song_url = QMediaContent(QUrl.fromLocalFile(current_song))
            player = self.player_ref()
            if player:
                player.setMedia(song_url)
            self.analyze_audio(current_song)
            if player:
                player.play()
            self.rotation_timer.start(36)
            self.move_slider()

            self.Start_button.hide()
            self.Pausebutton.show()
            self.update_song_title(current_song)
            self.current_songs_index = next_index
            self.get_cover_art(current_song)

        except Exception as e:
            raise e

        
    def update_song_title(self, song_path):
        self.label.setText(os.path.basename(song_path))
        self.label.setToolTip(os.path.basename(song_path))
        artist = self.get_artist_from_file(song_path)
        self.artistLabel.setText(artist)
        song_title = self.get_song_title(song_path)
        self.label.setText(song_title)
        

    def stop_song(self):
        self.player.stop()
        self.customSlider.setValue(0)
        self.player.play()
    
        
    # громкость 
    def volume_changed(self, value):
        self.current_volume = value
        self.player.setVolume(self.current_volume)
        self.update_volume_display()

    def update_volume_display(self):
        self.volume_label.setText(f"{self.current_volume}%")
    
            

def run_application():
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())