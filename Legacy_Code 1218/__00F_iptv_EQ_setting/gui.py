import tkinter as tk
from PIL import Image, ImageTk
from audio import EQPlayer
from visualizer import AudioVisualizer

class EQPlayerGUI(EQPlayer):
    def __init__(self):
        super().__init__()
        self.setup_gui()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("실시간 이퀄라이저 프로그램")
        self.root.geometry("1200x900")
        self.root.configure(bg='#2b2b2b')

        # Main container
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Left frame for equalizer
        eq_frame = tk.Frame(main_frame, bg='#2b2b2b')
        eq_frame.pack(side='left', fill='y', padx=20)

        # Equalizer label
        eq_label = tk.Label(eq_frame, text="Equalizer", font=('Arial', 12, 'bold'), 
                           fg='white', bg='#2b2b2b')
        eq_label.pack(pady=(0,20))
        # Slider frame
        slider_frame = tk.Frame(eq_frame, bg='#2b2b2b')
        slider_frame.pack()


        # Right frame for visualizer and controls
        right_frame = tk.Frame(main_frame, bg='#2b2b2b')
        right_frame.pack(side='left', expand=True, fill='both')

        # Add visualizer
        self.visualizer = AudioVisualizer(right_frame, self.buffer_size)

        # Time and playback control frame
        control_frame = tk.Frame(right_frame, bg='#2b2b2b')
        control_frame.pack(fill='x', pady=20)

        # Button frame
        button_frame = tk.Frame(right_frame, bg='#2b2b2b')
        button_frame.pack(pady=20)

        # center frame for image buttons
        center_frame = tk.Frame(main_frame, bg='#2b2b2b')
        center_frame.pack(anchor='center' ,expand=True, fill='both')


        # Add sliders
        for i, label in enumerate(["100Hz", "300Hz", "1kHz", "3kHz", "10kHz"]):
            slider = tk.Scale(slider_frame, from_=100, to=0, orient='vertical',
                            label=label, length=300, width=20,
                            command=lambda val, idx=i: self.on_slider_change(idx, val),
                            bg='#2b2b2b', fg='white', troughcolor='#404040',
                            activebackground='#606060')
            slider.set(50)
            slider.pack(side='left', padx=10)
            self.sliders.append(slider)

        # Time labels
        self.current_time_label = tk.Label(control_frame, text="00:00", 
                                         fg='white', bg='#2b2b2b')
        self.current_time_label.pack(side='left', padx=10)

        self.total_time_label = tk.Label(control_frame, text="00:00", 
                                       fg='white', bg='#2b2b2b')
        self.total_time_label.pack(side='right', padx=10)

        # Playback bar
        self.playback_bar = tk.Scale(control_frame, from_=0, to=100, 
                                   orient='horizontal', showvalue=0,
                                   bg='#2b2b2b', fg='white', 
                                   troughcolor='#404040',
                                   activebackground='#606060')
        self.playback_bar.pack(fill='x', padx=10)

        # Control buttons
        button_style = {'bg': '#404040', 'fg': 'white', 
                       'width': 10, 'height': 2,
                       'relief': 'flat'}
        
        play_button = tk.Button(button_frame, text="재생",
                              command=lambda: self.load_and_play_audio("sound/Last Goodbye.mp3"),
                              **button_style)
        play_button.pack(side='left', padx=5)

        stop_button = tk.Button(button_frame, text="정지",
                              command=self.stop_audio,
                              **button_style)
        stop_button.pack(side='left', padx=5)

        category_button = tk.Button(button_frame, text="설정 적용",
                                  command=self.apply_category_settings,
                                  **button_style)
        category_button.pack(side='left', padx=5)

        # Image frame at bottom
        image_frame = tk.Frame(center_frame, bg='#2b2b2b')
        image_frame.pack(side='bottom', pady=20)
        self.load_image("image/Last Goodbye.jpg")
        
        # Load initial category
        self.load_categories("기본")

    def load_image(self, filename: str):
        img = Image.open(filename)
        # Resize image to fit the layout
        img = img.resize((1000, 400), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        label = tk.Label(self.root, image=img_tk, bg='#2b2b2b')
        label.image = img_tk
        label.pack(side='bottom', pady=20)

    def run(self):
        self.root.mainloop()

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def load_and_play_audio(self, file_path):
        if super().load_and_play_audio(file_path):
            print("Audio loaded and playing")
            self.visualizer.start_animation(self.get_current_audio_data)

    def stop_audio(self):
        super().stop_audio()
        self.visualizer.stop_animation()