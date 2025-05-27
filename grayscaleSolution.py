import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.image import imread
import numpy as np
from scipy.ndimage import uniform_filter
from itom import ui

# --- Load Image using Itom File Dialog ---
filters = "Image files (*.png *.jpg *.bmp);;All files (*.*)"
filePath = ui.getOpenFileName("Select an image", "", filters)

if not filePath:
    print("No file selected.")
    exit()

# Load and normalize image
img = imread(filePath)
img = img.astype(np.float32)
if img.max() > 1.0:
    img = img / 255.0

original_img = img.copy()
edited_img = img.copy()

# --- Image Processing Function ---
def apply_effect(effect):
    global edited_img
    if effect == "grayscale":
        edited_img = np.mean(original_img, axis=2)
    elif effect == "invert":
        edited_img = 1.0 - original_img
    elif effect == "flip":
        edited_img = np.fliplr(original_img)
    elif effect == "blur":
        if original_img.ndim == 3:
            edited_img = np.zeros_like(original_img)
            for c in range(3):
                edited_img[:, :, c] = uniform_filter(original_img[:, :, c], size=5)
        else:
            edited_img = uniform_filter(original_img, size=5)
    else:
        edited_img = original_img
    update_plot()

# --- Update the Plot ---
def update_plot():
    ax1.clear()
    ax2.clear()

    ax1.imshow(original_img)
    ax1.set_title("Original Image")
    ax1.axis("off")

    ax2.imshow(edited_img, cmap='gray' if edited_img.ndim == 2 else None)
    ax2.set_title("Edited Image")
    ax2.axis("off")

    canvas.draw()

# --- GUI ---
root = tk.Tk()
root.title("Image Editor - ITOM Exercise")

# Control buttons
control_frame = ttk.Frame(root)
control_frame.pack(pady=10)

effect_var = tk.StringVar(value="none")
effects = [
    ("None", "none"),
    ("Grayscale", "grayscale"),
    ("Invert", "invert"),
    ("Flip Horizontal", "flip"),
]

for text, mode in effects:
    rb = ttk.Radiobutton(
        control_frame, text=text, variable=effect_var,
        value=mode, command=lambda: apply_effect(effect_var.get())
    )
    rb.pack(side=tk.LEFT, padx=5)

# Plotting area (no duplicate popup!)
fig = Figure(figsize=(8, 4))
ax1 = fig.add_subplot(1, 2, 1)
ax2 = fig.add_subplot(1, 2, 2)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# Show initial view
apply_effect("none")

root.mainloop()
