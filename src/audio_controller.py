"""音频控制：进入新状态时播放对应台词，带冷却与静音。

优先使用 Qt 的 QSoundEffect（QtMultimedia）；
QtMultimedia 不可用时回退到 macOS afplay。
缺少音频文件时静默跳过并写日志，不崩溃。
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import time
from pathlib import Path

log = logging.getLogger("pet.audio")

STATE_AUDIO = {
    "RISE": "mama_niulai.wav",
    "SURGE": "wo_shi_baola.wav",
    "FALL": "mama_xionglai.wav",
}


class AudioController:
    def __init__(self, audio_dir: str | Path, cooldown_seconds: float = 120.0, muted: bool = False):
        self.dir = Path(audio_dir)
        self.cooldown = cooldown_seconds
        self.muted = muted
        self._last_play: dict[str, float] = {}
        self._engine = "none"
        self._effects: dict[str, object] = {}
        try:
            from PySide6.QtMultimedia import QSoundEffect  # noqa: F401
            self._engine = "qsoundeffect"
        except Exception as e:  # noqa: BLE001
            if shutil.which("afplay"):
                self._engine = "afplay"
            else:
                log.warning("无可用音频引擎: %s", e)

    def play_for_state(self, state_name: str) -> bool:
        """进入新状态时调用。返回是否实际播放。"""
        fname = STATE_AUDIO.get(state_name)
        if not fname:
            return False
        if self.muted:
            return False
        path = self.dir / fname
        if not path.exists():
            log.warning("缺少音频文件: %s（静默跳过）", path)
            return False
        now = time.monotonic()
        if now - self._last_play.get(state_name, 0.0) < self.cooldown:
            return False
        self._last_play[state_name] = now
        try:
            if self._engine == "qsoundeffect":
                self._play_qt(path)
            elif self._engine == "afplay":
                subprocess.Popen(
                    ["afplay", str(path)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            return True
        except Exception as e:  # noqa: BLE001
            log.warning("播放失败 %s: %s", path, e)
            return False

    def duration(self, state_name: str) -> float:
        """该状态台词音频时长（秒）；无音频返回 0。"""
        fname = STATE_AUDIO.get(state_name)
        if not fname:
            return 0.0
        path = self.dir / fname
        if not path.exists():
            return 0.0
        try:
            import wave
            with wave.open(str(path), "rb") as w:
                return w.getnframes() / w.getframerate()
        except Exception:  # noqa: BLE001
            return 0.0

    def _play_qt(self, path: Path) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtMultimedia import QSoundEffect
        eff = self._effects.get(str(path))
        if eff is None:
            eff = QSoundEffect()
            eff.setSource(QUrl.fromLocalFile(str(path)))
            eff.setVolume(0.9)
            self._effects[str(path)] = eff
        eff.play()

    def shutdown(self) -> None:
        for eff in self._effects.values():
            try:
                eff.stop()
            except Exception:  # noqa: BLE001
                pass
