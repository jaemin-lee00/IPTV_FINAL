import numpy as np
from scipy import signal
import threading
import sounddevice as sd
import soundfile as sf
import time
import queue
from db import connect_to_db

class EQPlayer:
    def __init__(self):
        self.is_playing = False
        self.sliders = []
        self.categories = []
        self.total_duration = 0
        self.current_gains = [0, 0, 0, 0, 0]
        self.audio_queue = queue.Queue(maxsize=64)
        self.audio_stream = None
        self.current_position = 0
        self.audio_data = None
        self.samplerate = None
        self.buffer_size = 4096 ## set buffer size to self.frames
        self.freqs = [100, 300, 1000, 3000, 10000]
        self.category = None
        self.channels = 2
        self.GAIN_RANGE = 50.0  # Keep UI range consistent
        # Define max peak dB per frequency band
        self.MAX_PEAK_DB_PER_FREQ = {
            100: 6.0,    # Sub-bass: more restricted
            300: 9.0,    # Bass: slightly more headroom
            1000: 12.0,  # Mids: standard headroom
            3000: 12.0,  # Upper mids
            10000: 9.0   # Highs: slightly restricted to prevent harshness
        }
        

    def peak_filter(self, data, center_freq, fs, gain, Q=1.0):
        # Get frequency-specific max peak dB
        max_peak_db = self.MAX_PEAK_DB_PER_FREQ[center_freq]
        # Scale gain from [-50,50] range to frequency-specific max peak dB
        scaled_gain = (gain / self.GAIN_RANGE) * max_peak_db
        
        nyq = 0.5 * fs
        freq = center_freq / nyq
        b, a = signal.iirpeak(freq, Q)
        return signal.lfilter(b, a, data) * (10**(scaled_gain/20))

    def equalizer(self, data, fs, freqs, gains, Q=1.0):
        filtered = np.zeros_like(data)
        
        # Clip gains to allowed range
        limited_gains = np.clip(gains, -self.GAIN_RANGE, self.GAIN_RANGE)
        
        for freq, gain in zip(freqs, limited_gains):
            filtered += self.peak_filter(data, freq, fs, gain, Q)

    ## if you wnat to use RMS normalization, uncomment the following lines
        # # RMS normalization
        # original_rms = np.sqrt(np.mean(data**2))
        # filtered_rms = np.sqrt(np.mean(filtered**2))

        # if filtered_rms > 0:
        #     scaling_factor = original_rms / filtered_rms
        #     filtered *= scaling_factor

        return filtered

    def update_playback_bar(self):
        if self.is_playing and self.audio_data is not None:
            current_seconds = (self.current_position / self.samplerate)
            total_seconds = len(self.audio_data) / self.samplerate
            position_percentage = (self.current_position / len(self.audio_data)) * 100

            self.playback_bar.set(position_percentage)
            self.current_time_label.config(text=self.format_time(current_seconds))
            self.total_time_label.config(text=self.format_time(total_seconds))

            if position_percentage < 100:
                self.root.after(100, self.update_playback_bar)

    def load_and_play_audio(self, file_path):
        if self.is_playing:
            '''If audio is already playing, pass this function'''
            return False
        
        if not hasattr(self, 'current_file') or self.current_file != file_path:
            try:
                self.audio_data, self.samplerate = sf.read(file_path)
                if len(self.audio_data.shape) > 1:
                    self.audio_data = self.audio_data[:, 0]
                self.total_duration = len(self.audio_data) / self.samplerate
                self.current_file = file_path
                self.current_position = 0
            except Exception as e: 
                print(f"Error loading audio file: {e}")
                return False

        self.is_playing = True
        self.current_position = (self.current_position // self.buffer_size) * self.buffer_size
        
        threading.Thread(target=self.play_audio_from_position, daemon=True).start()
        self.root.after(100, self.update_playback_bar)
        return True

    def play_audio_from_position(self):
        try:
            if self.audio_stream is not None:
                self.audio_stream.stop()
                self.audio_stream.close()
            
            self.audio_stream = sd.OutputStream(
                samplerate=self.samplerate,
                callback=self.audio_callback,
                channels=self.channels,
                blocksize=self.buffer_size
            )
            
            self.audio_stream.start()
            print("Audio stream started")

            chunk_size = self.buffer_size

            for i in range(self.current_position, len(self.audio_data), chunk_size):
                if not self.is_playing:
                    break
                
                chunk = self.audio_data[i:i + chunk_size]

                if len(chunk) < chunk_size:
                    padded_chunk = np.zeros(chunk_size)
                    padded_chunk[:len(chunk)] = chunk
                    chunk = padded_chunk
                
                while self.is_playing and self.audio_queue.full():
                    time.sleep(0.0001)
                
                self.audio_queue.put(chunk)

        except Exception as e:
            print(f"Error in play_audio_from_position: {e}")

    def audio_callback(self, outdata, frames, time_info, status):
        try:
            data = self.audio_queue.get_nowait()
            if any(gain != 0 for gain in self.current_gains):
                processed_data = self.equalizer(data, self.samplerate, self.freqs, self.current_gains)
            else:
                processed_data = data
                
            if self.channels == 1:
                outdata[:] = processed_data.reshape(-1, 1)
            else:
                outdata[:] = np.column_stack((processed_data, processed_data))
            
            # Update current position based on frames processed
            self.current_position += frames

        except queue.Empty:
            outdata.fill(0)
            print("Buffer underrun")
        except Exception as e:
            print(f"Error in audio callback: {e}")
            outdata.fill(0)

    def stop_audio(self):
        if self.is_playing:
            self.is_playing = False
            if self.audio_data is not None:
                self.current_position = min(self.current_position, len(self.audio_data))
                
            with self.audio_queue.mutex:
                self.audio_queue.queue.clear()
            
            if self.audio_stream is not None:
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None
        
        sd.stop()

    def load_categories(self, category=None):
        if category:
            self.category = category
            self.categories = [category]
            print(f"Category loaded: {self.category}")

    def load_equalizer_settings(self, category=None):
        settings = {
            "액션": [60, 55, 50, 45, 40],
            "기본": [50, 50, 50, 50, 50]
        }
        
        category_to_use = category or self.category or "기본"
        selected_settings = settings.get(category_to_use, settings["기본"])

        for i, slider in enumerate(self.sliders):
            slider.set(selected_settings[i])

        print(selected_settings)

        adjusted_settings = [gain - 50 for gain in selected_settings]
        return adjusted_settings

    def apply_category_settings(self):
        if self.categories:
            selected_category = self.categories[0]
            gains = self.load_equalizer_settings(selected_category)
            self.current_gains = gains

    def on_slider_change(self, index, value):
        self.current_gains[index] = int(value) - 50
        print(f"Frequency {self.freqs[index]}Hz: Gain {self.current_gains[index]}dB")

    def get_current_audio_data(self):
        try:
            if self.is_playing and self.audio_data is not None:
                start_pos = self.current_position
                end_pos = min(start_pos + self.buffer_size, len(self.audio_data))
                
                data = self.audio_data[start_pos:end_pos]

                if len(data) < self.buffer_size:
                    padded_data = np.zeros(self.buffer_size)
                    padded_data[:len(data)] = data
                    data = padded_data

                # 이퀄라이저 적용
                if any(gain != 0 for gain in self.current_gains):
                    data = self.equalizer(data, self.samplerate, self.freqs, self.current_gains)
                
                return data
            
            return np.zeros(self.buffer_size)
        except Exception as e:
            print(f"Error in get_current_audio_data: {e}")
            return np.zeros(self.buffer_size)
