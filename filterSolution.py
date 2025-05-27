import numpy as np
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import gc

# --- Load CSV Data ---
filename = r"C:\Users\emily\OneDrive\Desktop\light_data.csv"
signal_raw = np.loadtxt(filename, delimiter=",", skiprows=1)
Fs = 2_000_000  # 2 MHz sampling rate

# --- High-pass filter implementation ---
def apply_highpass(data, cutoff, fs=Fs, order=4):
    nyq = 0.5 * fs
    norm_cutoff = cutoff / nyq
    b, a = butter(order, norm_cutoff, btype='high')
    return filtfilt(b, a, data)

class HighPassApp:
    def __init__(self, master):
        self.master = master
        master.title("High-Pass Filter Viewer")

        self.cutoff_default = 50000

        self.label = ttk.Label(master, text=f"Cutoff Frequency: {self.cutoff_default:,} Hz")
        self.label.pack()

        self.slider = ttk.Scale(master, from_=1000, to=Fs // 2, orient="horizontal",
                                command=self.on_slider_change)
        self.slider.set(self.cutoff_default)
        self.slider.pack(fill="x", padx=10)

        self.fig = plt.Figure(figsize=(6, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master)
        self.canvas.get_tk_widget().pack()

        self.update_plot(self.cutoff_default)

    def on_slider_change(self, value):
        cutoff = int(float(value))
        self.label.config(text=f"Cutoff Frequency: {cutoff:,} Hz")
        self.update_plot(cutoff)

    def update_plot(self, cutoff):
        if not hasattr(self, "ax"):
            return

        filtered = apply_highpass(signal_raw, cutoff)

        self.ax.clear()
        self.ax.plot(filtered, lw=0.5, label="High-pass Filtered")
        self.ax.set_title("High-pass Filter Output")
        self.ax.set_xlabel("Sample Index")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True)
        self.ax.legend()
        self.fig.tight_layout()
        self.canvas.draw()

def run_gui():
    gc.collect()
    root = tk.Tk()
    app = HighPassApp(root)
    root.mainloop()

run_gui()
