
import pygame
import os


class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_song = None
        self.is_paused = False
        self.is_playing = False

    # ── Core Playback ────────────────────────────────────────────────────────

    def load_song(self, filepath: str) -> bool:
        """Load an audio file into the mixer. Returns True on success."""
        if not os.path.isfile(filepath):
            return False
        try:
            pygame.mixer.music.load(filepath)
            self.current_song = filepath
            self.is_paused = False
            self.is_playing = False
            return True
        except pygame.error:
            return False

    def play_song(self) -> bool:
        """Play the currently loaded song from the beginning."""
        if self.current_song is None:
            return False
        try:
            pygame.mixer.music.play()
            self.is_playing = True
            self.is_paused = False
            return True
        except pygame.error:
            return False

    def pause_song(self):
        """Pause playback (can be resumed)."""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True

    def unpause_song(self):
        """Resume a paused song from where it stopped."""
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False

    def stop_song(self):
        """Stop playback completely and reset state."""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False

    # ── Volume ───────────────────────────────────────────────────────────────

    def set_volume(self, volume: float):
        """Set volume level (0.0 to 1.0)."""
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    def get_volume(self) -> float:
        """Return current volume (0.0 to 1.0)."""
        return pygame.mixer.music.get_volume()

    # ── Playback Position ────────────────────────────────────────────────────

    def get_position(self) -> float:
        """Return current playback position in seconds."""
        if self.is_playing and not self.is_paused:
            return pygame.mixer.music.get_pos() / 1000.0
        return 0.0

    def get_duration(self) -> float:
        """Return total duration of the current song in seconds using mutagen."""
        if self.current_song is None:
            return 0.0
        try:
            from mutagen.mp3 import MP3
            audio = MP3(self.current_song)
            return audio.info.length
        except Exception:
            return 0.0

    def is_song_over(self) -> bool:
        """Check if the song has finished playing naturally."""
        return self.is_playing and not self.is_paused and not pygame.mixer.music.get_busy()

    # ── Cleanup ──────────────────────────────────────────────────────────────

    def quit(self):
        """Release mixer resources on app exit."""
        pygame.mixer.quit()