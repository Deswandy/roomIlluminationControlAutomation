from itom import actuator, dataObject
import itom
import time
import threading
import tkinter as tk

# Create dummy motor
motor = actuator("DummyMotor")
if "speed" in motor.getParamList():
    motor.setParam("speed", 2.0)

# Wait for motion to complete
def wait_for_motor_done(motor, axis=0, timeout=5.0):
    start_time = time.time()
    while motor.getStatus(axis) == 1:
        if time.time() - start_time > timeout:
            print("Timeout waiting for motor.")
            break
        time.sleep(0.05)

# Move motor safely in thread
def move_motor_to(pos):
    def _move():
        print(f"Moving to {pos}...")
        motor.setPosAbs(0, float(pos))
        wait_for_motor_done(motor)
        print("Current Position:", motor.getPos(0))
    threading.Thread(target=_move).start()

# Tkinter GUI
root = tk.Tk()
root.title("Motor Position Control")

label = tk.Label(root, text="Motor Position")
label.pack(pady=10)

# Slider
slider = tk.Scale(
    root, from_=-10, to=10,
    orient="horizontal", length=300,
    resolution=0.5, command=move_motor_to
)
slider.set(0)
slider.pack(padx=20, pady=10)

# Run GUI loop
root.mainloop()

# Release motor after window closed
del motor
