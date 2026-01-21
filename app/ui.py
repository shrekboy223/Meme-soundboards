from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QFont
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

SUPPORTED_EXTENSIONS = {".wav", ".mp3"}


class SoundButton(QPushButton):
    def __init__(self, label: str, emoji: str, filename: str, parent: Optional[QWidget] = None) -> None:
        display = f"{emoji} {label}".strip()
        super().__init__(display, parent)
        self.label = label
        self.emoji = emoji
        self.filename = filename
        self.is_missing = False
        self.setProperty("playing", False)
        self.setProperty("missing", False)
        self.setProperty("selected", False)
        self.setProperty("flash", False)
        self.setFocusPolicy(Qt.NoFocus)

    def set_playing(self, playing: bool) -> None:
        self.setProperty("playing", playing)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_missing(self, missing: bool) -> None:
        self.is_missing = missing
        self.setProperty("missing", missing)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def flash(self) -> None:
        self.setProperty("flash", True)
        self.style().unpolish(self)
        self.style().polish(self)
        QTimer.singleShot(180, self._clear_flash)

    def _clear_flash(self) -> None:
        self.setProperty("flash", False)
        self.style().unpolish(self)
        self.style().polish(self)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Meme Soundboard")
        self.setMinimumSize(980, 680)

        self.config_path = Path("config/sounds.json")
        self.sounds_dir = Path("sounds")
        self.sounds: list[SoundButton] = []
        self.columns = 4
        self.selected_index = 0
        self.last_sound: Optional[SoundButton] = None

        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.errorOccurred.connect(self._on_error)

        self._build_ui()
        self._load_config()
        self._refresh_selection()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(24)

        now_playing_frame = QFrame()
        now_playing_frame.setObjectName("NowPlaying")
        now_playing_layout = QVBoxLayout(now_playing_frame)
        now_playing_layout.setSpacing(8)
        now_playing_title = QLabel("Now Playing")
        now_playing_title.setObjectName("SectionTitle")
        self.now_playing_label = QLabel("—")
        self.now_playing_label.setObjectName("NowPlayingLabel")
        self.status_label = QLabel("")
        self.status_label.setObjectName("StatusLabel")
        now_playing_layout.addWidget(now_playing_title)
        now_playing_layout.addWidget(self.now_playing_label)
        now_playing_layout.addWidget(self.status_label)

        history_frame = QFrame()
        history_frame.setObjectName("History")
        history_layout = QVBoxLayout(history_frame)
        history_layout.setSpacing(8)
        history_title = QLabel("Recent")
        history_title.setObjectName("SectionTitle")
        self.history_list = QListWidget()
        self.history_list.setObjectName("HistoryList")
        self.history_list.setMaximumHeight(140)
        history_layout.addWidget(history_title)
        history_layout.addWidget(self.history_list)

        header_layout.addWidget(now_playing_frame, 2)
        header_layout.addWidget(history_frame, 1)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop)
        self.replay_button = QPushButton("Rejouer")
        self.replay_button.clicked.connect(self.replay_last)
        volume_label = QLabel("Volume")
        volume_label.setObjectName("VolumeLabel")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self._set_volume)
        self._set_volume(self.volume_slider.value())

        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.replay_button)
        controls_layout.addStretch(1)
        controls_layout.addWidget(volume_label)
        controls_layout.addWidget(self.volume_slider, 2)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(14)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        root_layout.addLayout(header_layout)
        root_layout.addLayout(controls_layout)
        root_layout.addWidget(self.grid_widget, 1)

        self.setCentralWidget(root)

    def _load_config(self) -> None:
        if not self.config_path.exists():
            self._set_status("Le fichier config/sounds.json est introuvable.")
            return

        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.columns = int(data.get("columns", 4))
        sounds = data.get("sounds", [])

        row = 0
        col = 0
        for entry in sounds:
            label = entry.get("label", "Sans titre")
            filename = entry.get("filename", "")
            emoji = entry.get("emoji", "")
            button = SoundButton(label=label, emoji=emoji, filename=filename)
            button.clicked.connect(lambda _, b=button: self.play_sound(b))

            sound_path = self.sounds_dir / filename
            extension = sound_path.suffix.lower()
            missing = not sound_path.exists()
            unsupported = extension not in SUPPORTED_EXTENSIONS
            if missing:
                button.set_missing(True)
                button.setToolTip("Fichier manquant dans sounds/")
            elif unsupported:
                button.set_missing(True)
                button.setToolTip("Format non supporté (WAV ou MP3)")
            else:
                button.setToolTip(str(sound_path))

            self.grid_layout.addWidget(button, row, col)
            self.sounds.append(button)

            col += 1
            if col >= self.columns:
                col = 0
                row += 1

    def _set_volume(self, value: int) -> None:
        self.audio_output.setVolume(value / 100)

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def play_sound(self, button: SoundButton) -> None:
        if button.is_missing:
            self._set_status(
                f"Erreur: '{button.filename}' est introuvable ou non supporté."
            )
            self.now_playing_label.setText("—")
            button.flash()
            return

        path = self.sounds_dir / button.filename
        if not path.exists():
            button.set_missing(True)
            self._set_status(
                f"Erreur: '{button.filename}' est introuvable dans sounds/."
            )
            return

        self._set_status("")
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self.player.play()

        self.now_playing_label.setText(button.text())
        self._push_history(button.text())
        self._set_playing_button(button)
        button.flash()
        self.last_sound = button

    def _push_history(self, label: str) -> None:
        self.history_list.insertItem(0, label)
        while self.history_list.count() > 6:
            self.history_list.takeItem(self.history_list.count() - 1)

    def _set_playing_button(self, active: SoundButton) -> None:
        for button in self.sounds:
            button.set_playing(button is active)

    def stop(self) -> None:
        self.player.stop()
        self.now_playing_label.setText("—")
        self._set_status("")
        for button in self.sounds:
            button.set_playing(False)

    def replay_last(self) -> None:
        if self.last_sound is None:
            self._set_status("Aucun son à rejouer.")
            return
        self.play_sound(self.last_sound)

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.StoppedState:
            for button in self.sounds:
                button.set_playing(False)

    def _on_error(self, error: QMediaPlayer.Error) -> None:
        if error == QMediaPlayer.NoError:
            return
        self._set_status("Erreur audio: impossible de lire ce fichier.")

    def _refresh_selection(self) -> None:
        if not self.sounds:
            return
        for index, button in enumerate(self.sounds):
            button.set_selected(index == self.selected_index)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if not self.sounds:
            return

        key = event.key()
        if key == Qt.Key_Space:
            self.stop()
            return

        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.play_sound(self.sounds[self.selected_index])
            return

        if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
            row = self.selected_index // self.columns
            col = self.selected_index % self.columns
            if key == Qt.Key_Left:
                col = max(0, col - 1)
            elif key == Qt.Key_Right:
                col = min(self.columns - 1, col + 1)
            elif key == Qt.Key_Up:
                row = max(0, row - 1)
            elif key == Qt.Key_Down:
                row = row + 1

            new_index = row * self.columns + col
            if new_index >= len(self.sounds):
                new_index = len(self.sounds) - 1

            self.selected_index = new_index
            self._refresh_selection()
            return

        super().keyPressEvent(event)


def apply_theme(app) -> None:
    app.setFont(QFont("SF Pro Display", 11))
    app.setStyleSheet(
        """
        QWidget {
            background-color: #111217;
            color: #f4f5f7;
        }
        QFrame#NowPlaying, QFrame#History {
            background-color: #1a1c24;
            border: 1px solid #2a2d38;
            border-radius: 14px;
            padding: 12px;
        }
        QLabel#SectionTitle {
            font-size: 14px;
            text-transform: uppercase;
            color: #9aa3b2;
            letter-spacing: 1px;
        }
        QLabel#NowPlayingLabel {
            font-size: 20px;
            font-weight: 600;
        }
        QLabel#StatusLabel {
            color: #ff6b6b;
            font-size: 12px;
        }
        QPushButton {
            background-color: #1f222d;
            border: 1px solid #2a2f3d;
            border-radius: 14px;
            padding: 18px;
            font-size: 15px;
        }
        QPushButton:hover {
            background-color: #2a2e3b;
            border-color: #3a4154;
        }
        QPushButton[playing="true"] {
            background-color: #2b3a4f;
            border: 1px solid #4d6ea8;
            color: #cfe2ff;
        }
        QPushButton[selected="true"] {
            border: 1px solid #7c5cff;
        }
        QPushButton[missing="true"] {
            background-color: #2b1f1f;
            border: 1px solid #5b2b2b;
            color: #ffb3b3;
        }
        QPushButton[flash="true"] {
            background-color: #3a3f4f;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #2a2d38;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
            background: #7c5cff;
        }
        QListWidget#HistoryList {
            background-color: #14161d;
            border: 1px solid #2a2d38;
            border-radius: 10px;
            padding: 6px;
        }
        """
    )
