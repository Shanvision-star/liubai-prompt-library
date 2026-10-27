"""首次准备素材时显示简洁进度窗口，避免文件事务期间像是没有启动。"""
import logging
import threading


class StartupNotice:
    def __init__(self):
        self.done = threading.Event()
        self.cancelled = False
        threading.Thread(target=self._show, daemon=True).start()

    def _show(self):
        try:
            import tkinter as tk
            from tkinter import ttk
            window = tk.Tk()
            window.title("留白")
            window.configure(bg="#ffffff")
            window.resizable(False, False)
            x, y = (window.winfo_screenwidth() - 360) // 2, (window.winfo_screenheight() - 170) // 2
            window.geometry(f"360x170+{x}+{y}")
            tk.Label(window, text="留白", bg="#ffffff", fg="#333333", font=("Microsoft YaHei UI", 20)).pack(pady=(22, 8))
            tk.Label(window, text="正在准备内置素材，完成后自动打开", bg="#ffffff", fg="#666666", font=("Microsoft YaHei UI", 10)).pack()
            style = ttk.Style(window)
            style.theme_use("clam")
            style.configure("Liubai.Horizontal.TProgressbar", background="#a5a5a5", troughcolor="#f3f3f3", bordercolor="#ffffff", lightcolor="#a5a5a5", darkcolor="#a5a5a5")
            progress = ttk.Progressbar(window, mode="indeterminate", style="Liubai.Horizontal.TProgressbar", length=260)
            progress.pack(pady=18)
            progress.start(25)
            def cancel():
                self.cancelled = True
                window.destroy()
            def check():
                if self.done.is_set():
                    window.destroy()
                else:
                    window.after(100, check)
            window.protocol("WM_DELETE_WINDOW", cancel)
            window.after(100, check)
            window.mainloop()
        except Exception:
            logging.exception("准备窗口不可用，继续初始化")

    def close(self):
        self.done.set()
