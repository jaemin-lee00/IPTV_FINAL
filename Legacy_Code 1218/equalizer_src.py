import numpy as np
from scipy import signal
import soundfile as sf

def bandpass_filter(data, lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band')
    return signal.lfilter(b, a, data)

def equalizer(data, fs, gains):
    bands = [(20, 50), (50, 100), (100, 200), (200, 500), (500, 1000), (1000, 2000), (2000, 5000), (5000, 10000), (10000, 20000)]
    filtered = np.zeros_like(data)
    for (low, high), gain in zip(bands, gains):
        filtered += bandpass_filter(data, low, high, fs) * (10**(gain/20))
    return filtered

# 오디오 파일 로드
data, fs = sf.read('sound/ROSE.mp3')

# 각 밴드의 게인 설정 (dB)
gains = [0, 3, -2, 1, 0, 2, -1, 4, -3]

# 이퀄라이저 적용
equalized_data = equalizer(data, fs, gains)

# 결과 저장
sf.write('output_audio.wav', equalized_data, fs)
