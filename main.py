import tkinter as tk
from PIL import Image, ImageTk
import mysql.connector

categories = []

Hz_Settings = ["Hz_100", "Hz_300", "Hz_1k", "Hz_3k", "Hz_10k"]

def load_categories():
    global categories
    conn = mysql.connector.connect(
        host='192.168.101.227',
        user='Second',
        password='rkdwlsah12!*',
        database='second_pj',
        port=3306
    )
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT GNR_MLSFC_NM FROM watched_data")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()

def load_image(filename: str):
    img = Image.open(f"image/{filename}")  # 지정한 파일 이름으로 이미지 열기
    img_tk = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=img_tk)
    label.image = img_tk  # 가비지 컬렉션 방지용 참조 유지
    label.pack()

def sound_setting():
    # Create a frame to hold the buttons
    button_frame = tk.Frame(root)
    button_frame.place(relwidth=0.6, relheight=0.3, relx=0.2, rely=0.25)

    # Update the frame to get its dimensions
    button_frame.update_idletasks()
    frame_width = button_frame.winfo_width()
    frame_height = button_frame.winfo_height()

    # Create '예' and '아니오' buttons with adjusted size
    yes_button = tk.Button(button_frame, text="예", width=int(frame_width * 0.6 * 0.1), height=int(frame_height * 0.05), command=lambda: open_equalizer(button_frame, categories[0]))
    yes_button.place(relx=0.25, rely=0.5, anchor='center')
    no_button = tk.Button(button_frame, text="아니오", width=int(frame_width * 0.6 * 0.1), height=int(frame_height * 0.05), command=button_frame.destroy)
    no_button.place(relx=0.75, rely=0.5, anchor='center')

def open_equalizer(parent_frame, category):
    parent_frame.destroy()
    
    # Create a frame to hold the equalizer settings within the main window
    eq_frame = tk.Frame(root)
    eq_frame.place(relwidth=0.6, relheight=0.6, relx=0.1, rely=0.2)

    # Add category name at the top with adjusted font size
    category_label = tk.Label(eq_frame, text=category, font=("Arial", 12))
    category_label.pack(pady=10)

    # Connect to the database
    conn = mysql.connector.connect(
        host='192.168.101.227',
        user='Second',
        password='rkdwlsah12!*',
        database='second_pj',
        port=3306
    )
    cursor = conn.cursor()

    # Fetch equalizer settings for the selected category from the database
    cursor.execute("""
        SELECT Hz_100, Hz_300, Hz_1k, Hz_3k, Hz_10k
        FROM watched_data
        WHERE GNR_MLSFC_NM = %s
    """, (category,))
    settings = cursor.fetchall()

    # Create 5 vertical lines (rectangles) for equalizer settings
    for i, setting_value in enumerate(settings[0]):
        int_setting_value = int(setting_value)

        line_frame = tk.Frame(eq_frame)
        line_frame.place(relx=0.1 + i * 0.15, rely=0.1, relwidth=0.15, relheight=0.8)

        # Add a label for the setting name
        setting_label = tk.Label(line_frame, text= Hz_Settings[i], width=10)
        setting_label.pack(pady=5)

        # Add a scale (slider) for the setting value
        setting_scale = tk.Scale(line_frame, from_=100, to=0, orient='vertical')
        setting_scale.set(int_setting_value)
        setting_scale.pack(fill='y', expand=True)

        # Add an entry to display the current value
        setting_value_entry = tk.Entry(line_frame, width=5)
        setting_value_entry.insert(0, int_setting_value)
        setting_value_entry.pack(pady=5)

        # Update the entry value when the scale is moved
        setting_scale.config(command=lambda val, entry=setting_value_entry: entry.delete(0, tk.END) or entry.insert(0, val))

    # Close the database connection
    cursor.close()
    conn.close()

def key_input(event):
    if event.keysym == 's':
        sound_setting()

root = tk.Tk()
root.title("Tkinter 예제 프로그램")
root.geometry("800x600")  # 창 크기 설정

root.bind('<Key>', key_input)  # 키 이벤트 바ㄴ인딩

load_image("img02.jpg")  # 프로그램 메인 이미지 전체 이미지 생각
load_categories()

root.mainloop()