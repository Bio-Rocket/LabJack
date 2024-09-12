import time

class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.previous_error = 0
        self.integral = 0

    def update(self, current_value):
        error = self.setpoint - current_value
        self.integral += error
        derivative = error - self.previous_error
        self.previous_error = error
        return self.Kp * error + self.Ki * self.integral + self.Kd * derivative

def pid_loop(pressure_sensor, valve, setpoint, Kp, Ki, Kd):
    pid = PIDController(Kp, Ki, Kd, setpoint)
    
    while True:
        current_pressure = pressure_sensor.read_pressure()
        pid_output = pid.update(current_pressure)
        
        if pid_output > 0:
            valve.open()
        else:
            valve.close()
        
        time.sleep(0.1)  # Adjust the sleep time as needed

# Example usage
class PressureSensor:
    def read_pressure(self):
        # Replace with actual sensor reading logic
        return 50

class Valve:
    def open(self):
        print("Valve opened")

    def close(self):
        print("Valve closed")

pressure_sensor = PressureSensor()
valve = Valve()
setpoint = 100  # Desired pressure
Kp = 1.0
Ki = 0.1
Kd = 0.05

pid_loop(pressure_sensor, valve, setpoint, Kp, Ki, Kd)