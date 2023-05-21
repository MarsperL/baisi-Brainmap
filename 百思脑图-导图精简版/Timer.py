import tkinter as tk
from tkinter import ttk
import time
import ctypes

myappid = "专注记录"
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


def run_timer():
    class Timer:
        def __init__(self, master):
            self.master = master
            master.title("专注计时")
            master.resizable(False, False)  # 禁止调整窗口大小
            x, y = master.winfo_pointerxy()  # 获取鼠标坐标
            master.geometry(f"+{x}+{y}")  # 将窗口定位到鼠标坐标处
            master.iconbitmap("./icons/baisi.ico")
            master.iconbitmap(default='./icons/baisi.ico')
            # 设置样式
            self.style = ttk.Style()
            self.style.configure("TButton", font=("宋体", 12))
            self.style.configure("TLabel", font=("Arial", 36))
            # 计时器标签
            self.time_label = ttk.Label(master, text="00:00:00", style="TLabel")
            self.time_label.pack(side=tk.TOP, pady=30)
            # 按钮框架
            self.button_frame = ttk.Frame(master)
            self.button_frame.pack()
            # 开始按钮
            self.start_button = ttk.Button(self.button_frame, text="开始计时", command=self.start_timer, style="TButton")
            self.start_button.pack(side=tk.LEFT, padx=10, pady=5)
            # 停止按钮
            self.stop_button = ttk.Button(self.button_frame, text="停止计时", command=self.stop_timer, state="disabled",
                                          style="TButton")
            self.stop_button.pack(side=tk.LEFT, padx=10)
            # 重置按钮
            self.reset_button = ttk.Button(self.button_frame, text="重置计时", command=self.reset_timer, state="disabled",
                                           style="TButton")
            self.reset_button.pack(side=tk.LEFT, padx=10)
            # 初始化
            self.running = False
            self.elapsed_time = 0
            self.last_start_time = 0
            self.update_time()

            # 窗口置顶按钮
            self.top_button = ttk.Button(self.master, text="置顶", command=self.set_window_topmost,
                                         style="TButton")
            self.top_button.pack(side=tk.LEFT, padx=10)
            self.top_button.place(x=290, y=5)
            # 取消置顶按钮
            self.untop_button = ttk.Button(self.master, text="取消置顶", command=self.cancel_window_topmost,
                                           style="TButton")
            self.untop_button.pack(side=tk.LEFT, padx=10)
            self.untop_button.place(x=290, y=5)

            # 窗口透明按钮
            self.button_alpha_on = ttk.Button(self.master, text="透明模式", command=self.button_alpha_on_mes,
                                         style="TButton")
            self.button_alpha_on.pack(side=tk.LEFT, padx=10)
            self.button_alpha_on.place(x=10, y=5)
            # 窗口不透明按钮
            self.button_alpha = ttk.Button(self.master, text="普通模式", command=self.button_alpha_off_mes,
                                           style="TButton")
            self.button_alpha.pack(side=tk.LEFT, padx=10)
            self.button_alpha.place(x=10, y=5)
        def update_time(self):
            if self.running:
                self.elapsed_time = time.time() - self.last_start_time
            minutes, seconds = divmod(int(self.elapsed_time), 60)
            hours, minutes = divmod(minutes, 60)
            time_str = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
            self.time_label.configure(text=time_str)
            self.master.after(1000, self.update_time)

        def start_timer(self):
            if not self.running:
                self.running = True
                self.last_start_time = time.time()
                self.start_button.config(state="disabled")
                self.stop_button.config(state="normal")
                self.reset_button.config(state="normal")

        def stop_timer(self):
            if self.running:
                self.running = False
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")

        def reset_timer(self):
            self.elapsed_time = 0
            self.running = False
            self.time_label.configure(text="00:00:00")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.reset_button.config(state="disabled")

        # 窗口置顶按钮指令
        def set_window_topmost(self):
            self.master.attributes("-topmost", True)
            self.top_button.place_forget()
            self.untop_button.place(x=290, y=5)

        # 取消置顶按钮指令
        def cancel_window_topmost(self):
            self.master.attributes("-topmost", False)
            self.untop_button.place_forget()
            self.top_button.place(x=290, y=5)

            # 透明模式关闭按钮指令

        def button_alpha_off_mes(self):
            self.master.wm_attributes("-alpha", 1)
            self.button_alpha.place_forget()
            self.button_alpha_on.place(x=10, y=5)

            # 透明模式开启按钮指令

        def button_alpha_on_mes(self):
            self.master.wm_attributes("-alpha", 0.7)
            self.button_alpha_on.place_forget()
            self.button_alpha.place(x=10, y=5)


    root = tk.Tk()
    timer = Timer(root)
    root.mainloop()
