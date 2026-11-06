"""Arc-reactor HUD built on tkinter (no extra dependencies)."""
import math
import queue
import threading
import tkinter as tk

COLORS = {"idle": "#00d4ff", "listening": "#39ff88", "thinking": "#ffb300", "speaking": "#4da3ff"}
BG = "#05080f"


class HUD:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S.")
        self.root.geometry("560x780")
        self.root.configure(bg=BG)
        self.canvas = tk.Canvas(self.root, width=540, height=400, bg=BG, highlightthickness=0)
        self.canvas.pack(pady=(10, 0))
        self.status = tk.Label(self.root, text="ONLINE", fg=COLORS["idle"], bg=BG,
                               font=("Consolas", 14, "bold"))
        self.status.pack()
        self.box = tk.Text(self.root, height=14, bg="#0a111c", fg="#bfefff", bd=0, wrap="word",
                           font=("Consolas", 11), state="disabled")
        self.box.pack(fill="both", expand=True, padx=14, pady=10)
        self.box.tag_config("you", foreground="#9aa7b4")
        self.box.tag_config("jarvis", foreground="#00d4ff")
        self.entry = tk.Entry(self.root, bg="#0a111c", fg="#ffffff", insertbackground="#00d4ff",
                              bd=0, font=("Consolas", 12))
        self.entry.pack(fill="x", padx=14, pady=(0, 14), ipady=8)
        self.entry.bind("<Return>", self._submit)

        self.on_submit = None
        self.on_close = None
        self.q = queue.Queue()
        self.mode = "idle"
        self.angle = 0.0
        self.root.protocol("WM_DELETE_WINDOW", self._closing)
        self._tick()
        self._poll()

    # --- thread-safe API ---
    def log(self, who, text):
        self.q.put(("log", who, text))

    def set_state(self, s):
        self.q.put(("state", s, None))

    def close(self):
        try:
            self.root.after(0, self.root.destroy)
        except Exception:
            pass

    def run(self, worker):
        threading.Thread(target=worker, daemon=True).start()
        self.root.mainloop()

    # --- internals ---
    def _submit(self, _):
        text = self.entry.get().strip()
        self.entry.delete(0, "end")
        if text and self.on_submit:
            self.on_submit(text)

    def _closing(self):
        if self.on_close:
            self.on_close()
        else:
            self.root.destroy()

    def _poll(self):
        while not self.q.empty():
            kind, a, b = self.q.get()
            if kind == "state":
                self.mode = a
                self.status.config(text=a.upper(), fg=COLORS.get(a, COLORS["idle"]))
            else:
                self.box.config(state="normal")
                self.box.insert("end", f"{'YOU' if a == 'you' else 'JARVIS'}: {b}\n", a)
                self.box.see("end")
                self.box.config(state="disabled")
        self.root.after(100, self._poll)

    def _tick(self):
        c, col = self.canvas, COLORS.get(self.mode, COLORS["idle"])
        c.delete("all")
        cx, cy = 270, 200
        speed = {"idle": 1.2, "listening": 2.5, "thinking": 6, "speaking": 3.5}.get(self.mode, 1.2)
        self.angle = (self.angle + speed) % 360
        for i, r in enumerate((165, 135, 105, 75)):
            direction = 1 if i % 2 == 0 else -1
            for k in range(3):
                start = direction * self.angle * (1 + i * 0.25) + k * 120
                c.create_arc(cx - r, cy - r, cx + r, cy + r, start=start, extent=75,
                             style="arc", outline=col, width=3 if i % 2 == 0 else 2)
        pulse = 26 + 6 * math.sin(math.radians(self.angle * 4))
        c.create_oval(cx - pulse, cy - pulse, cx + pulse, cy + pulse, fill=col, outline="")
        c.create_oval(cx - 12, cy - 12, cx + 12, cy + 12, fill="#ffffff", outline="")
        self.root.after(33, self._tick)
