import pyaudio
import wave
import datetime

def record_audio(seconds=10):
    # 오디오 설정
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000  # 음성인식에 적합한 16kHz로 변경

    # PyAudio 객체 생성
    p = pyaudio.PyAudio()

    # 스트림 열기
    stream = p.open(format=FORMAT,
                   channels=CHANNELS,
                   rate=RATE,
                   input=True,
                   frames_per_buffer=CHUNK)

    print("녹음을 시작합니다...")
    frames = []

    # 녹음
    for i in range(0, int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("녹음이 완료되었습니다.")

    # 스트림 정리
    stream.stop_stream()
    stream.close()
    p.terminate()

    # 현재 시간을 파일명으로 사용
    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".wav"

    # WAV 파일로 저장
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    print(f"파일이 {filename}으로 저장되었습니다.")

if __name__ == "__main__":
    # 5초 동안 녹음
    record_audio(10)