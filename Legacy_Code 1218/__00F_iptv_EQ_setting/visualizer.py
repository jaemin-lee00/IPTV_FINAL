import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation

class AudioVisualizer:
    def __init__(self, master, chunk_size):
        self.chunk_size = chunk_size
        self.previous_data = np.zeros(chunk_size)
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        self.x = np.arange(0, self.chunk_size//2)
        self.line, = self.ax.plot(self.x, np.zeros(self.chunk_size//2), 
                                 color='#2196f3', linewidth=2)
        
        # Configure plot
        self.ax.set_ylim(0, 40)  # 더 낮은 범위로 조정
        self.ax.set_xlim(0, int(self.chunk_size* 0.4))
        self.ax.grid(True, alpha=0.3)
        self.ax.set_facecolor('#f0f0f0')
        self.fig.patch.set_facecolor('#f0f0f0')
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side='top', fill='x', padx=10, pady=5)
        
        self.animation = None

    def update_plot(self, frame, data):
        if data is None:
            data = np.zeros(self.chunk_size)
        
        # FFT 변환 및 스케일 조정
        fft_data = np.abs(np.fft.fft(data))[:self.chunk_size//2]
        fft_data = np.log10(fft_data + 1) * 10  # 로그 스케일로 변환
        
        # 스무딩 적용
        smoothed_data = 0.6 * fft_data + 0.4 * self.previous_data[:self.chunk_size//2]
        self.previous_data[:self.chunk_size//2] = smoothed_data
        
        # 라인 업데이트
        self.line.set_ydata(smoothed_data)
        
        # 진폭에 따른 색상 변경
        amplitude = np.mean(smoothed_data)
        self.line.set_color(plt.cm.viridis(amplitude/10))
        
        return self.line,

    def start_animation(self, data_func):
        def animation_frame(frame):
            data = data_func()  # 매 프레임마다 새로운 데이터 가져오기
            return self.update_plot(frame, data)

        self.animation = FuncAnimation(
            self.fig,
            animation_frame,
            interval=20,  # Faster refresh rate
            blit=True,
            cache_frame_data=False
        )
        self.canvas.draw()

    def stop_animation(self):
        if self.animation:
            self.animation.event_source.stop
