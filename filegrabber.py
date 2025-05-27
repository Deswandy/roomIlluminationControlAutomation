from itom import ui
from matplotlib.image import imread
import matplotlib.pyplot as plt

# --- Open File Dialog (images only) ---
filters = "Image files (*.png *.jpg *.bmp);;All files (*.*)"
filePath = ui.getOpenFileName("Select an image", "", filters)

if filePath:
    try:
        img = imread(filePath)
        print("Image loaded successfully.")

        # --- Display with matplotlib ---
        plt.figure()
        plt.imshow(img)
        plt.title("Loaded Image")
        plt.axis("off")
        plt.show()

    except Exception as e:
        print("Error loading image:", e)
else:
    print("No file selected.")
