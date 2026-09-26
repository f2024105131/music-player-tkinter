
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import random
import os

from player import MusicPlayer
from utils import format_song_name, format_time, validate_audio_file

# ── Palette ──────────────────────────────────────────────────────────────────
BG          = "#1a1a2e"   # deep navy
SURFACE     = "#16213e"   # card surface
ACCENT      = "#0f3460"   # mid-blue
HIGHLIGHT   = "#e94560"   # red-pink highlight
TEXT        = "#eaeaea"
SUBTEXT     = "#8892a4"
SLIDER_TRK  = "#2a2a4a"
FONT_TITLE  = ("Helvetica Neue", 14, "bold")
FONT_BODY   = ("Helvetica Neue", 11)
FONT_SMALL  = ("Helvetica Neue", 9)
FONT_MONO   = ("Courier New", 10)
BTN_W       = 5   # character-width of icon buttons


class MusicPlayerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.player = MusicPlayer()

        # Playlist state
        self.playlist: list[str] = []
        self.current_index: int = -1
        self.shuffle_on: bool = False
        self.repeat_on: bool = False

        self._build_window()
        self._build_ui()
        self._start_progress_loop()

    # ── Window setup ─────────────────────────────────────────────────────────

    def _build_window(self):
        self.root.title("Music Player")
        self.root.geometry("480x620")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_now_playing()
        self._build_progress()
        self._build_controls()
        self._build_volume()
        self._build_playlist_panel()

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=20, pady=(18, 0))

        tk.Label(
            header, text="♪  Music Player",
            font=("Helvetica Neue", 18, "bold"),
            bg=BG, fg=HIGHLIGHT
        ).pack(side="left")

        # Shuffle / Repeat toggles
        toggle_frame = tk.Frame(header, bg=BG)
        toggle_frame.pack(side="right")

        self.shuffle_btn = tk.Button(
            toggle_frame, text="⇌", font=FONT_BODY,
            bg=SURFACE, fg=SUBTEXT, relief="flat", bd=0,
            width=BTN_W, cursor="hand2",
            command=self._toggle_shuffle
        )
        self.shuffle_btn.pack(side="left", padx=4)

        self.repeat_btn = tk.Button(
            toggle_frame, text="↺", font=FONT_BODY,
            bg=SURFACE, fg=SUBTEXT, relief="flat", bd=0,
            width=BTN_W, cursor="hand2",
            command=self._toggle_repeat
        )
        self.repeat_btn.pack(side="left", padx=4)

    def _build_now_playing(self):
        card = tk.Frame(self.root, bg=SURFACE, pady=18, padx=20)
        card.pack(fill="x", padx=20, pady=(14, 0))

        tk.Label(card, text="NOW PLAYING", font=FONT_SMALL,
                 bg=SURFACE, fg=SUBTEXT).pack()

        self.song_label = tk.Label(
            card, text="— no track loaded —",
            font=FONT_TITLE, bg=SURFACE, fg=TEXT,
            wraplength=400, justify="center"
        )
        self.song_label.pack(pady=(6, 0))

        self.file_info_label = tk.Label(
            card, text="", font=FONT_SMALL, bg=SURFACE, fg=SUBTEXT
        )
        self.file_info_label.pack()

    def _build_progress(self):
        prog_frame = tk.Frame(self.root, bg=BG)
        prog_frame.pack(fill="x", padx=20, pady=(14, 0))

        # Time labels
        time_row = tk.Frame(prog_frame, bg=BG)
        time_row.pack(fill="x")
        self.current_time_label = tk.Label(
            time_row, text="0:00", font=FONT_MONO, bg=BG, fg=SUBTEXT
        )
        self.current_time_label.pack(side="left")
        self.total_time_label = tk.Label(
            time_row, text="0:00", font=FONT_MONO, bg=BG, fg=SUBTEXT
        )
        self.total_time_label.pack(side="right")

        # Progress bar (Canvas-based)
        self.progress_canvas = tk.Canvas(
            prog_frame, height=6, bg=SLIDER_TRK,
            highlightthickness=0, cursor="hand2"
        )
        self.progress_canvas.pack(fill="x", pady=(4, 0))
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 0, 6, fill=HIGHLIGHT, outline=""
        )
        self.progress_canvas.bind("<Button-1>", self._on_seek)

    def _build_controls(self):
        ctrl = tk.Frame(self.root, bg=BG)
        ctrl.pack(pady=20)

        btn_cfg = dict(font=("Helvetica Neue", 16), relief="flat",
                       bd=0, cursor="hand2", width=4, pady=6)

        self.prev_btn = tk.Button(
            ctrl, text="⏮", bg=SURFACE, fg=TEXT,
            command=self._prev_song, **btn_cfg
        )
        self.prev_btn.grid(row=0, column=0, padx=6)

        self.stop_btn = tk.Button(
            ctrl, text="⏹", bg=SURFACE, fg=TEXT,
            command=self._stop, **btn_cfg
        )
        self.stop_btn.grid(row=0, column=1, padx=6)

        self.play_btn = tk.Button(
            ctrl, text="▶", bg=HIGHLIGHT, fg=TEXT,
            command=self._play_pause, **btn_cfg
        )
        self.play_btn.grid(row=0, column=2, padx=6)

        self.next_btn = tk.Button(
            ctrl, text="⏭", bg=SURFACE, fg=TEXT,
            command=self._next_song, **btn_cfg
        )
        self.next_btn.grid(row=0, column=3, padx=6)

        # Browse button
        tk.Button(
            self.root, text="+ Add Songs", font=FONT_BODY,
            bg=ACCENT, fg=TEXT, relief="flat", bd=0,
            padx=14, pady=6, cursor="hand2",
            command=self._browse_files
        ).pack(pady=(0, 4))

    def _build_volume(self):
        vol_frame = tk.Frame(self.root, bg=BG)
        vol_frame.pack(fill="x", padx=28, pady=(0, 10))

        tk.Label(vol_frame, text="🔈", bg=BG, fg=SUBTEXT,
                 font=FONT_BODY).pack(side="left")

        self.volume_var = tk.DoubleVar(value=0.7)
        vol_slider = tk.Scale(
            vol_frame, variable=self.volume_var,
            from_=0.0, to=1.0, resolution=0.01,
            orient="horizontal", showvalue=False,
            bg=BG, fg=HIGHLIGHT, troughcolor=SLIDER_TRK,
            highlightthickness=0, bd=0, sliderlength=14,
            command=lambda v: self.player.set_volume(float(v))
        )
        vol_slider.pack(side="left", fill="x", expand=True, padx=6)

        tk.Label(vol_frame, text="🔊", bg=BG, fg=SUBTEXT,
                 font=FONT_BODY).pack(side="left")

        self.player.set_volume(0.7)

    def _build_playlist_panel(self):
        tk.Label(self.root, text="Playlist", font=FONT_BODY,
                 bg=BG, fg=SUBTEXT).pack(anchor="w", padx=20)

        list_frame = tk.Frame(self.root, bg=SURFACE)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(4, 16))

        scrollbar = tk.Scrollbar(list_frame, bg=SURFACE, troughcolor=BG)
        scrollbar.pack(side="right", fill="y")

        self.playlist_box = tk.Listbox(
            list_frame, bg=SURFACE, fg=TEXT,
            selectbackground=ACCENT, selectforeground=TEXT,
            font=FONT_BODY, relief="flat", bd=0,
            yscrollcommand=scrollbar.set,
            activestyle="none"
        )
        self.playlist_box.pack(fill="both", expand=True)
        scrollbar.config(command=self.playlist_box.yview)
        self.playlist_box.bind("<Double-Button-1>", self._on_playlist_double_click)

    # ── Playback Actions ─────────────────────────────────────────────────────

    def _browse_files(self):
        paths = filedialog.askopenfilenames(
            title="Add songs",
            filetypes=[("Audio files", "*.mp3 *.wav *.ogg *.flac"), ("All files", "*.*")]
        )
        for path in paths:
            ok, err = validate_audio_file(path)
            if ok:
                self._add_to_playlist(path)
            else:
                messagebox.showerror("Invalid file", err)

        # Auto-load first song if nothing was loaded yet
        if self.current_index == -1 and self.playlist:
            self._load_track(0)

    def _add_to_playlist(self, filepath: str):
        self.playlist.append(filepath)
        self.playlist_box.insert("end", format_song_name(filepath))

    def _load_track(self, index: int):
        if index < 0 or index >= len(self.playlist):
            return
        self.current_index = index
        filepath = self.playlist[index]
        self.player.load_song(filepath)

        self.song_label.config(text=format_song_name(filepath))
        duration = self.player.get_duration()
        self.total_time_label.config(text=format_time(duration))
        self.current_time_label.config(text="0:00")
        self._reset_progress_bar()

        size = self._get_size_label(filepath)
        self.file_info_label.config(text=size)

        # Highlight in list
        self.playlist_box.selection_clear(0, "end")
        self.playlist_box.selection_set(index)
        self.playlist_box.see(index)

    def _play_pause(self):
        if not self.playlist:
            messagebox.showinfo("No songs", "Add songs first using '+ Add Songs'.")
            return

        if self.current_index == -1:
            self._load_track(0)

        if self.player.is_playing and not self.player.is_paused:
            self.player.pause_song()
            self.play_btn.config(text="▶")
        elif self.player.is_paused:
            self.player.unpause_song()
            self.play_btn.config(text="⏸")
        else:
            self.player.play_song()
            self.play_btn.config(text="⏸")

    def _stop(self):
        self.player.stop_song()
        self.play_btn.config(text="▶")
        self.current_time_label.config(text="0:00")
        self._reset_progress_bar()

    def _next_song(self):
        if not self.playlist:
            return
        if self.shuffle_on:
            next_idx = random.randint(0, len(self.playlist) - 1)
        else:
            next_idx = (self.current_index + 1) % len(self.playlist)
        self._load_track(next_idx)
        self.player.play_song()
        self.play_btn.config(text="⏸")

    def _prev_song(self):
        if not self.playlist:
            return
        prev_idx = (self.current_index - 1) % len(self.playlist)
        self._load_track(prev_idx)
        self.player.play_song()
        self.play_btn.config(text="⏸")

    def _on_playlist_double_click(self, event):
        selection = self.playlist_box.curselection()
        if selection:
            self._load_track(selection[0])
            self.player.play_song()
            self.play_btn.config(text="⏸")

    # ── Toggle Modes ─────────────────────────────────────────────────────────

    def _toggle_shuffle(self):
        self.shuffle_on = not self.shuffle_on
        color = HIGHLIGHT if self.shuffle_on else SUBTEXT
        self.shuffle_btn.config(fg=color)

    def _toggle_repeat(self):
        self.repeat_on = not self.repeat_on
        color = HIGHLIGHT if self.repeat_on else SUBTEXT
        self.repeat_btn.config(fg=color)

    # ── Seek ─────────────────────────────────────────────────────────────────

    def _on_seek(self, event):
        duration = self.player.get_duration()
        if duration <= 0:
            return
        canvas_w = self.progress_canvas.winfo_width()
        ratio = event.x / canvas_w
        seek_sec = ratio * duration
        self.player.stop_song()
        self.player.play_song()
        # pygame doesn't support direct seeking on music streams without
        # restarting; update UI position immediately
        self.current_time_label.config(text=format_time(seek_sec))

    # ── Progress Loop ─────────────────────────────────────────────────────────

    def _start_progress_loop(self):
        """Poll playback position every 500 ms on a background thread."""
        def loop():
            while True:
                self._update_progress()
                threading.Event().wait(0.5)

        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def _update_progress(self):
        """Update progress bar and time labels; auto-advance on song end."""
        try:
            if not self.player.is_playing or self.player.is_paused:
                return

            if self.player.is_song_over():
                if self.repeat_on:
                    self.root.after(0, lambda: (self.player.play_song(),))
                else:
                    self.root.after(0, self._next_song)
                return

            pos = self.player.get_position()
            duration = self.player.get_duration()

            self.root.after(0, lambda p=pos, d=duration: self._draw_progress(p, d))
        except Exception:
            pass

    def _draw_progress(self, pos: float, duration: float):
        self.current_time_label.config(text=format_time(pos))
        if duration > 0:
            ratio = min(pos / duration, 1.0)
            w = self.progress_canvas.winfo_width()
            h = 6
            self.progress_canvas.coords(self.progress_bar, 0, 0, w * ratio, h)

    def _reset_progress_bar(self):
        self.progress_canvas.coords(self.progress_bar, 0, 0, 0, 6)

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _get_size_label(filepath: str) -> str:
        try:
            size = os.path.getsize(filepath)
            return f"{size / 1_048_576:.1f} MB" if size >= 1_048_576 else f"{size / 1024:.1f} KB"
        except OSError:
            return ""

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def _on_close(self):
        self.player.quit()
        self.root.destroy()