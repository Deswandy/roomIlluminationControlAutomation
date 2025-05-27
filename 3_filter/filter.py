import numpy as np
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import gc  # Helps ITOM clear old objects

# --- Load CSV Data ---
filename = r"C:\Users\emily\OneDrive\Desktop\light_data.csv"
signal_raw = np.loadtxt(filename, delimiter=",", skiprows=1)
Fs = 2_000_000  # 2 MHz sampling rate

def apply_lowpass(data, cutoff, fs=Fs, order=4):
    nyq = 0.5 * fs
    norm_cutoff = cutoff / nyq
    b, a = butter(order, norm_cutoff, btype='low')
    return filtfilt(b, a, data)

class LowPassApp:
    def __init__(self, master):
        self.master = master
        master.title("Low-Pass Filter Controller")

        self.cutoff_default = 50000

        self.label = ttk.Label(master, text=f"Cutoff Frequency: {self.cutoff_default:,} Hz")
        self.label.pack()

        self.slider = ttk.Scale(master, from_=1000, to=Fs // 2, orient="horizontal",
                                command=self.on_slider_change)
        self.slider.set(self.cutoff_default)
        self.slider.pack(fill="x", padx=10)

        # Create figure and axes
        self.fig = plt.Figure(figsize=(6, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master)
        self.canvas.get_tk_widget().pack()

        # Initial plot
        self.update_plot(self.cutoff_default)

    def on_slider_change(self, value):
        cutoff = int(float(value))
        self.label.config(text=f"Cutoff Frequency: {cutoff:,} Hz")
        self.update_plot(cutoff)

    def update_plot(self, cutoff):
        if not hasattr(self, "ax"):
            print("Axes not initialized yet.")
            return
        filtered = apply_lowpass(signal_raw, cutoff)
        self.ax.clear()
        self.ax.plot(filtered, lw=0.5)
        self.ax.set_title("Filtered Signal")
        self.ax.set_xlabel("Sample Index")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True)
        self.fig.tight_layout()
        self.canvas.draw()

def run_gui():
    gc.collect()  # Clear old Tkinter windows in ITOM
    root = tk.Tk()
    app = LowPassApp(root)
    root.mainloop()

# Run GUI in ITOM
run_gui()
