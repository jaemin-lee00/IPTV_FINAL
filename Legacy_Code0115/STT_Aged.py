import speech_recognition as sr
import pyaudio
import wave
import datetime
import numpy as np

def record_audio(seconds=10, volume_multiplier=2.0):  # 볼륨 증폭 파라미터 추가
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000  # 음성인식에 적합한 16kHz

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                   channels=CHANNELS,
                   rate=RATE,
                   input=True,
                   frames_per_buffer=CHUNK)

    print("녹음을 시작합니다...")
    frames = []

    for i in range(0, int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("녹음이 완료되었습니다.")
    print("볼륨을 증폭하는 중...")

    # 오디오 데이터를 numpy 배열로 변환하고 볼륨 증폭
    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
    
    # 클리핑을 방지하면서 볼륨 증폭
    audio_data = audio_data.astype(np.float32)
    audio_data = audio_data * volume_multiplier
    
    # 클리핑 방지
    audio_data = np.clip(audio_data, -32768, 32767)
    audio_data = audio_data.astype(np.int16)

    stream.stop_stream()
    stream.close()
    p.terminate()

    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".wav"
    
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(audio_data.tobytes())
    wf.close()

    print(f"증폭된 파일이 {filename}으로 저장되었습니다.")
    return filename

def speech_to_text(audio_file):
    recognizer = sr.Recognizer()
    
    with sr.AudioFile(audio_file) as source:
        print("음성을 텍스트로 변환 중...")
        audio = recognizer.record(source)
        
        try:
            text = recognizer.recognize_google(audio, language='ko-KR')
            print("변환된 텍스트:")
            print(text)
            return text
        except sr.UnknownValueError:
            print("음성을 인식할 수 없습니다.")
            return None
        except sr.RequestError as e:
            print(f"구글 API 요청 오류: {e}")
            return None

if __name__ == "__main__":
    # 10초 동안 음성 녹음, 볼륨 2배 증폭
    audio_file = record_audio(10, volume_multiplier=2.0)
    # 녹음된 음성을 텍스트로 변환
    speech_to_text(audio_file)
