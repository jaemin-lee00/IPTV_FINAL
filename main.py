import tkinter as tk
from PIL import Image, ImageTk
import mysql.connector
import numpy as np
from scipy import signal
import threading
import os
import sounddevice as sd
import soundfile as sf
import time
import queue

class EQPlayer:
    def __init__(self):
        self.is_playing = False
        self.sliders = []
        self.categories = []
        self.playback_start_time = 0
        self.total_duration = 0
        self.current_gains = [0, 0, 0, 0, 0]
        self.audio_queue = queue.Queue()
        self.audio_stream = None
        
        self.setup_gui()
        
    def connect_to_db(self):
        return mysql.connector.connect(
            host='192.168.101.227',
            user='Second',
            password='rkdwlsah12!*',
            database='second_pj',
            port=3306
        )

    def peak_filter(self, data, center_freq, fs, gain, Q=1.0):
        nyq = 0.5 * fs
        freq = center_freq / nyq
        b, a = signal.iirpeak(freq, Q)
        return signal.lfilter(b, a, data) * (10**(gain / 20))

    def equalizer(self, data, fs, freqs, gains, Q=1.0):
        try:
            filtered = np.zeros(len(data), dtype=np.float32)
            for freq, gain in zip(freqs, gains):
                filtered += self.peak_filter(data, freq, fs, gain, Q)
            return filtered
        except Exception as e:
            print(f"Error in equalizer function: {e}")
            return data

    def update_playback_bar(self):
        if self.is_playing:
            elapsed = time.time() - self.playback_start_time
            percentage = min((elapsed / self.total_duration) * 100, 100)
            self.playback_bar.set(percentage)
            if percentage < 100:
                self.root.after(1000, self.update_playback_bar)

    def load_and_play_audio(self, file_path):
        self.stop_audio()
        
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        if not self.is_playing:
            self.is_playing = True
            threading.Thread(target=self.play_audio, args=(file_path,)).start()
            self.root.after(1000, self.update_playback_bar)

    def play_audio(self, file_path):
        try:
            with sf.SoundFile(file_path) as f:
                audio = f.read(dtype="float32")
                if audio.ndim > 1:
                    audio = np.mean(audio, axis=1)
                samplerate = f.samplerate
                self.total_duration = len(audio) / samplerate

            self.playback_start_time = time.time()
            
            if self.audio_stream is not None:
                self.audio_stream.stop()
                self.audio_stream.close()
            
            self.audio_stream = sd.OutputStream(
                samplerate=samplerate,
                channels=1,
                callback=self.audio_callback,
                dtype='float32',
                blocksize=1024
            )
            self.audio_stream.start()

            chunk_size = 1024
            for i in range(0, len(audio), chunk_size):
                if not self.is_playing:
                    break
                chunk = audio[i:i + chunk_size]
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)), 'constant')
                self.audio_queue.put(chunk)

            while not self.audio_queue.empty() and self.is_playing:
                time.sleep(0.1)

        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            self.is_playing = False
            if self.audio_stream is not None:
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None

    def audio_callback(self, outdata, frames, time_info, status):
        try:
            data = self.audio_queue.get_nowait()
        except queue.Empty:
            outdata[:] = np.zeros((frames, 1), dtype='float32')
            return

        processed_data = self.equalizer(data, 44100, [100, 300, 1000, 3000, 10000], self.current_gains)
        
        if len(processed_data) < frames:
            processed_data = np.pad(processed_data, (0, frames - len(processed_data)), 'constant')
        elif len(processed_data) > frames:
            processed_data = processed_data[:frames]
        
        outdata[:] = processed_data.reshape(-1, 1)

    def stop_audio(self):
        self.is_playing = False
        
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        if self.audio_stream is not None:
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
        
        sd.stop()

    def load_categories(self):
        conn = self.connect_to_db()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT GNR_MLSFC_NM FROM watched_data")
        self.categories = [row[0] for row in cursor.fetchall()]
        conn.close()

    def load_equalizer_settings(self, category):
        conn = self.connect_to_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Hz_100, Hz_300, Hz_1k, Hz_3k, Hz_10k
            FROM watched_data
            WHERE GNR_MLSFC_NM = %s
            LIMIT 1
        """, (category,))
        settings = cursor.fetchone() or [50, 50, 50, 50, 50]

        for i, slider in enumerate(self.sliders):
            slider.set(settings[i])

        cursor.close()
        conn.close()

        adjusted_settings = [gain - 50 for gain in settings]
        return adjusted_settings

    def apply_category_settings(self):
        if self.categories:
            selected_category = self.categories[0]
            gains = self.load_equalizer_settings(selected_category)
            self.current_gains = gains

    def on_slider_change(self, index, value):
        self.current_gains[index] = int(value) - 50

    def load_image(self, filename: str):
        img = Image.open(filename)
        img_tk = ImageTk.PhotoImage(img)
        label = tk.Label(self.root, image=img_tk)
        label.image = img_tk
        label.pack()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("실시간 이퀄라이저 프로그램")
        self.root.geometry("800x600")

        for i, label in enumerate(["100Hz", "300Hz", "1kHz", "3kHz", "10kHz"]):
            slider = tk.Scale(self.root, from_=100, to=0, orient='vertical', 
                            label=label, command=lambda val, idx=i: self.on_slider_change(idx, val))
            slider.set(50)
            slider.pack(side='left', fill='y', expand=True)
            self.sliders.append(slider)

        self.playback_bar = tk.Scale(self.root, from_=0, to=100, orient='horizontal', length=600)
        self.playback_bar.pack(side='top', pady=10)

        play_button = tk.Button(self.root, text="재생", 
                              command=lambda: self.load_and_play_audio("sound/ROSE.mp3"))
        play_button.pack(side='left', padx=10)

        stop_button = tk.Button(self.root, text="정지", command=self.stop_audio)
        stop_button.pack(side='left', padx=10)

        category_button = tk.Button(self.root, text="카테고리 설정 적용", 
                                  command=self.apply_category_settings)
        category_button.pack(side='left', padx=10)

        self.load_image("image/img02.jpg")
        self.load_categories()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    player = EQPlayer()
    player.run()
