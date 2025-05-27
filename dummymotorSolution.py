from itom import actuator, dataObject
import itom
import time
import threading
import tkinter as tk

# Create dummy motor
motor = actuator("DummyMotor")
if "speed" in motor.getParamList():
    motor.setParam("speed", 2.0)

# Wait for motor to complete motion
def wait_for_motor_done(motor, axis=0, timeout=5.0):
    start_time = time.time()
    while motor.getStatus(axis) == 1:
        if time.time() - start_time > timeout:
            print("Timeout waiting for motor.")
            break
        time.sleep(0.05)

# GUI setup
root = tk.Tk()
root.title("Motor Position Control with Moving Figure")

# Canvas to draw figure
canvas_width = 400
canvas_height = 100
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="white")
canvas.pack(pady=10)

# Create a simple oval (the "figure")
figure_radius = 10
initial_x = canvas_width // 2
figure = canvas.create_oval(
    initial_x - figure_radius, 40 - figure_radius,
    initial_x + figure_radius, 40 + figure_radius,
    fill="blue"
)

# Map motor position to canvas x-coordinate
def position_to_canvas_x(pos):
    motor_min = -10
    motor_max = 10
    # Normalize to 0..1, then scale to canvas width
    norm = (float(pos) - motor_min) / (motor_max - motor_min)
    return int(norm * canvas_width)

# Move motor + move figure
def move_motor_to(pos):
    def _move():
        print(f"Moving to {pos}...")
        motor.setPosAbs(0, float(pos))
        wait_for_motor_done(motor)
        current_pos = motor.getPos(0)
        print("Current Position:", current_pos)

        # Update figure position on canvas
        x = position_to_canvas_x(current_pos)
        canvas.coords(
            figure,
            x - figure_radius, 40 - figure_radius,
            x + figure_radius, 40 + figure_radius
        )
    threading.Thread(target=_move).start()

# Label and slider
label = tk.Label(root, text="Motor Position")
label.pack()

slider = tk.Scale(
    root, from_=-10, to=10, resolution=0.5,
    orient="horizontal", length=300,
    command=move_motor_to
)
slider.set(0)
slider.pack(pady=10)

# Run GUI
root.mainloop()

# Cleanup
del motor
