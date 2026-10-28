import os

from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from ninjalooter import logger

LOG = logger.getLogger(__name__)


class AlertSoundPlayer(QObject):
    """Plays alert sounds on the UI thread.

    Each alert gets its own player, so a new cue does not cut off one that is
    still playing. Players are released when playback ends or fails.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._players = []

    def play(self, soundfile: str) -> None:
        path = os.path.abspath(os.fspath(soundfile))
        if not os.path.isfile(path):
            LOG.error("Couldn't play soundfile, missing: %s", path)
            return
        try:
            player = QMediaPlayer(self)
            audio = QAudioOutput(player)
            audio.setVolume(1.0)
            player.setAudioOutput(audio)
            player.mediaStatusChanged.connect(lambda status, p=player: self._on_status(p, status))
            player.errorOccurred.connect(lambda error, message, p=player: self._on_error(p, error, message))
            self._players.append(player)
            player.setSource(QUrl.fromLocalFile(path))
            player.play()
        except Exception:
            LOG.exception("Couldn't play soundfile.")

    def _on_status(self, player: QMediaPlayer, status) -> None:
        if status in (QMediaPlayer.MediaStatus.EndOfMedia, QMediaPlayer.MediaStatus.InvalidMedia):
            self._discard(player)

    def _on_error(self, player: QMediaPlayer, error, message: str) -> None:
        if error == QMediaPlayer.Error.NoError:
            return
        LOG.error("Couldn't play soundfile: %s", message)
        self._discard(player)

    def _discard(self, player: QMediaPlayer) -> None:
        if player not in self._players:
            return
        self._players.remove(player)
        player.stop()
        player.deleteLater()
