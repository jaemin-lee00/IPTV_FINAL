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

# 전역 변수 초기화
is_playing = False
sliders = []
categories = []
playback_start_time = 0
total_duration = 0
current_gains = [0, 0, 0, 0, 0]  # 슬라이더 기준 변동값
audio_queue = queue.Queue()
audio_stream = None  # 전역 스트림 변수 추가

# Database connection function
def connect_to_db():
    return mysql.connector.connect(
        host='192.168.101.227',
        user='Second',
        password='rkdwlsah12!*',
        database='second_pj',
        port=3306
    )

def peak_filter(data, center_freq, fs, gain, Q=1.0):
    nyq = 0.5 * fs
    freq = center_freq / nyq
    b, a = signal.iirpeak(freq, Q)
    return signal.lfilter(b, a, data) * (10**(gain / 20))

def equalizer(data, fs, freqs, gains, Q=1.0):
    try:
        filtered = np.zeros(len(data), dtype=np.float32)
        for freq, gain in zip(freqs, gains):
            filtered += peak_filter(data, freq, fs, gain, Q)
        return filtered
    except Exception as e:
        print(f"Error in equalizer function: {e}")
        return data  # 필요에 따라 오류 처리


# 재생바 업데이트
def update_playback_bar():
    if is_playing:
        elapsed = time.time() - playback_start_time
        percentage = min((elapsed / total_duration) * 100, 100)
        playback_bar.set(percentage)
        if percentage < 100:
            root.after(1000, update_playback_bar)

# 오디오 파일 로드 및 스트림 시작
def load_and_play_audio(file_path):
    global is_playing, audio_stream
    
    # 이전 재생 중지
    stop_audio()
    
    # 큐 초기화
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break
    
    if not is_playing:
        is_playing = True
        threading.Thread(target=play_audio, args=(file_path,)).start()
        root.after(1000, update_playback_bar)

def play_audio(file_path):
    global is_playing, playback_start_time, total_duration, audio_stream
    try:
        with sf.SoundFile(file_path) as f:
            audio = f.read(dtype="float32")
            if audio.ndim > 1:
                audio = np.mean(audio, axis=1)  # 모노로 변환
            samplerate = f.samplerate
            total_duration = len(audio) / samplerate

        playback_start_time = time.time()
        
        # 이전 스트림이 있다면 종료
        if audio_stream is not None:
            audio_stream.stop()
            audio_stream.close()
        
        audio_stream = sd.OutputStream(
            samplerate=samplerate,
            channels=1,
            callback=audio_callback,
            dtype='float32',
            blocksize=1024  # blocksize를 1024로 고정
        )
        audio_stream.start()

        chunk_size = 1024
        for i in range(0, len(audio), chunk_size):
            if not is_playing:
                break
            chunk = audio[i:i + chunk_size]
            if len(chunk) < chunk_size:
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)), 'constant')
            audio_queue.put(chunk)

        # 재생이 끝날 때까지 대기
        while not audio_queue.empty() and is_playing:
            time.sleep(0.1)

    except Exception as e:
        print(f"Error playing audio: {e}")
    finally:
        is_playing = False
        if audio_stream is not None:
            audio_stream.stop()
            audio_stream.close()
            audio_stream = None

def audio_callback(outdata, frames, time_info, status):
    try:
        data = audio_queue.get_nowait()
    except queue.Empty:
        outdata[:] = np.zeros((frames, 1), dtype='float32')
        return

    # 이퀄라이저 적용
    processed_data = equalizer(data, 44100, [100, 300, 1000, 3000, 10000], current_gains)
    
    # 프레임 수 일치 여부 확인 및 제로 패딩
    if len(processed_data) < frames:
        processed_data = np.pad(processed_data, (0, frames - len(processed_data)), 'constant')
    elif len(processed_data) > frames:
        processed_data = processed_data[:frames]
    
    outdata[:] = processed_data.reshape(-1, 1)

# 오디오 정지 함수 수정 (필요 시 스트림 종료)
def stop_audio():
    global is_playing, audio_stream
    is_playing = False
    
    # 큐 비우기
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break
    
    # 스트림 정리
    if audio_stream is not None:
        audio_stream.stop()
        audio_stream.close()
        audio_stream = None
    
    sd.stop()

# Load categories from database
def load_categories():
    global categories
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT GNR_MLSFC_NM FROM watched_data")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()

# Load equalizer settings from database for a specific category
def load_equalizer_settings(category):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Hz_100, Hz_300, Hz_1k, Hz_3k, Hz_10k
        FROM watched_data
        WHERE GNR_MLSFC_NM = %s
        LIMIT 1
    """, (category,))
    settings = cursor.fetchone() or [50, 50, 50, 50, 50]  # 기본값 50

    for i, slider in enumerate(sliders):
        slider.set(settings[i])  # 슬라이더에 실제 게인 값 설정

    cursor.close()  
    conn.close()

    # 기본값 50을 기준으로 게인 조정
    adjusted_settings = [gain - 50 for gain in settings]
    return adjusted_settings  # 상대적 게인 반환

def apply_category_settings():
    if categories:
        selected_category = categories[0]  # 예시: 첫 번째 카테고리 선택
        gains = load_equalizer_settings(selected_category)
        global current_gains
        current_gains = gains  # 전역 게인 업데이트

# Add slider event binding to update current_gains in real-time
def on_slider_change(index, value):
    global current_gains
    current_gains[index] = int(value) - 50  # 50을 기준으로 조정

# GUI 초기화
root = tk.Tk()
root.title("실시간 이퀄라이저 프로그램")
root.geometry("800x600")

# 이미지 로드 함수
def load_image(filename: str):
    img = Image.open(filename)
    img_tk = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=img_tk)
    label.image = img_tk  # 가비지 컬렉션 방지용 참조 유지
    label.pack()

# 이퀄라이저 슬라이더 GUI 생성
for i, label in enumerate(["100Hz", "300Hz", "1kHz", "3kHz", "10kHz"]):
    slider = tk.Scale(root, from_=100, to=0, orient='vertical', label=label, command=lambda val, idx=i: on_slider_change(idx, val))
    slider.set(50)  # 기본값 50 설정
    slider.pack(side='left', fill='y', expand=True)
    sliders.append(slider)

# 재생바
playback_bar = tk.Scale(root, from_=0, to=100, orient='horizontal', length=600)
playback_bar.pack(side='top', pady=10)

# 재생 버튼
play_button = tk.Button(root, text="재생", command=lambda: load_and_play_audio("sound/ROSE.mp3"))
play_button.pack(side='left', padx=10)

# 정지 버튼
stop_button = tk.Button(root, text="정지", command=stop_audio)
stop_button.pack(side='left', padx=10)

# 카테고리 선택 버튼 (데이터베이스의 이퀄라이저 설정 적용)
category_button = tk.Button(root, text="카테고리 설정 적용", command=apply_category_settings)
category_button.pack(side='left', padx=10)

# GUI 이벤트 바인딩 및 초기 설정
load_image("image/img02.jpg")
load_categories()
root.mainloop()
