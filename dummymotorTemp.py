from itom import actuator, dataObject
import itom
import time
import threading
import tkinter as tk

# Create dummy motor
motor = actuator("DummyMotor")
if "speed" in motor.getParamList():
    motor.setParam("speed", 2.0)

# Function to wait for motor to finish moving
def wait_for_motor_done(motor, axis=0, timeout=5.0):
    start_time = time.time()
    while motor.getStatus(axis) == 1:
        if time.time() - start_time > timeout:
            print("Timeout waiting for motor.")
            break
        time.sleep(0.05)

# --- Tkinter GUI Setup ---
root = tk.Tk()
root.title("Motor Position Control with Figure")

label = tk.Label(root, text="Motor Position")
label.pack(pady=10)

# --- Canvas Setup ---
canvas_width = 400
canvas_height = 100
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="white")
canvas.pack(pady=10)

# TODO: Create a circle (or rectangle) on the canvas to represent the motor position
# HINT: Use canvas.create_oval(x0, y0, x1, y1, fill="color")
figure_radius = 10
initial_x = canvas_width // 2
figure = canvas.create_oval(
    initial_x - figure_radius, 40 - figure_radius,
    initial_x + figure_radius, 40 + figure_radius,
    fill="blue"
)

# --- Position Conversion ---
# Converts motor position (-10 to 10) to canvas x-coordinate (0 to canvas_width)
def position_to_canvas_x(pos):
    motor_min = -10
    motor_max = 10
    norm = (float(pos) - motor_min) / (motor_max - motor_min)
    return int(norm * canvas_width)

# --- Motor Movement Function ---
def move_motor_to(pos):
    def _move():
        print(f"Moving to {pos}...")

        # TODO: Move the motor to the selected position
        motor.setPosAbs(0, float(pos))

        # Wait until movement is complete
        wait_for_motor_done(motor)

        # TODO: Get current position from motor
        current_pos = motor.getPos(0)
        print("Current Position:", current_pos)

        # TODO: Convert motor position to canvas X coordinate
        x = position_to_canvas_x(current_pos)

        # TODO: Update the figure position on the canvas
        canvas.coords(
            figure,
            x - figure_radius, 40 - figure_radius,
            x + figure_radius, 40 + figure_radius
        )

    threading.Thread(target=_move).start()

# --- Slider Control ---
slider = tk.Scale(
    root, from_=-10, to=10,
    orient="horizontal", length=300,
    resolution=0.5, command=move_motor_to
)
slider.set(0)
slider.pack(padx=20, pady=10)

# Run the GUI
root.mainloop()

# Cleanup
del motor
