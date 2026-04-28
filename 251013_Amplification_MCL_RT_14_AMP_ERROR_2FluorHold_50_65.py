#!/usr/bin/env python3
"""
Example usage of the ODrive python library to monitor and control ODrive devices
"""

########### ERROR INDUCTION ############
########################################
#odrv0.axis0.controller.config.vel_limit = 0 # 65 is normal
########################################

from __future__ import print_function

import os
import sys
import odrive
from odrive.enums import *
import time
import math
from odrive.utils import start_liveplotter
from odrive.utils import *
import pyautogui
import time


# Function to create a unique log file name
def create_log_file():
    date_str = time.strftime("%Y%m%d")
    base_name = f"{date_str}_OdriveLog"
    file_extension = ".txt"
    log_dir = "Odrive Position Logs"
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    file_path = os.path.join(log_dir, base_name + file_extension)
    counter = 1

    # Increment file name if it already exists
    while os.path.exists(file_path):
        file_path = os.path.join(log_dir, f"{base_name}_{counter}{file_extension}")
        counter += 1

    return open(file_path, "w")

# Open a log file with a unique name
log_file = create_log_file()

def save_current_axis_config(axis):
    cfg = {
        "input_mode": axis.controller.config.input_mode,
        "requested_state": axis.requested_state,
        "circular_setpoints": axis.controller.config.circular_setpoints,
        # Trap trajectory settings (only relevant in TRAP_TRAJ mode)
        "vel_limit": getattr(axis.trap_traj.config, "vel_limit", None),
        "accel_limit": getattr(axis.trap_traj.config, "accel_limit", None),
        "decel_limit": getattr(axis.trap_traj.config, "decel_limit", None),
        # Position filter settings (only relevant in POS_FILTER mode)
        "input_filter_bandwidth": getattr(axis.controller.config, "input_filter_bandwidth", None),
    }
    return cfg

def restore_axis_config(axis, cfg):
    axis.controller.config.input_mode = cfg["input_mode"]
    axis.requested_state = cfg["requested_state"]
    axis.controller.config.circular_setpoints = cfg["circular_setpoints"]
    
    # Restore TrapTraj settings if they exist
    if cfg["vel_limit"] is not None:
        axis.trap_traj.config.vel_limit = cfg["vel_limit"]
    if cfg["accel_limit"] is not None:
        axis.trap_traj.config.accel_limit = cfg["accel_limit"]
    if cfg["decel_limit"] is not None:
        axis.trap_traj.config.decel_limit = cfg["decel_limit"]
    
    # Restore Position Filter settings if they exist
    if cfg["input_filter_bandwidth"] is not None:
        axis.controller.config.input_filter_bandwidth = cfg["input_filter_bandwidth"]

def dump_and_check_errors(odrv, max_retries=5):
    """
    Dumps ODrive errors, logs them, and attempts to automatically recover.
    Retries clearing and recalibrating until no errors remain or retry limit is reached.
    
    Args:
        odrv: ODrive object (e.g., odrv0)
        max_retries (int): Maximum number of retry attempts. Default = 5.
    
    Returns:
        bool: True if ODrive is healthy (no errors), False if unrecoverable.
    """
    attempt = 0
    while attempt <= max_retries:
        log_and_print(f"Checking ODrive errors... (Attempt {attempt + 1}/{max_retries})")
        odrive.utils.dump_errors(odrv, clear=False) # Don't clear because this then we can't log them
        
        system_errors = odrv.error
        axis0_errors = odrv.axis0.error
        motor_errors = odrv.axis0.motor.error
        encoder_errors = odrv.axis0.encoder.error
        controller_errors = odrv.axis0.controller.error
        #axis1_errors = getattr(odrv, "axis1", None)
        
        print("System", system_errors
              , "Axis 0 Errors:", axis0_errors
              , "Motor Errors:", motor_errors
              , "Encoder Errors:", encoder_errors
              , "Controller Errors:", controller_errors
              )
        
         # Check if any errors are present

        has_errors = any([
            system_errors,
            axis0_errors,
            motor_errors,
            encoder_errors,
            controller_errors
        ])

        print("Has Errors:", has_errors)

        if not has_errors:
            log_and_print(":) No ODrive errors detected.")
            return True  # Healthy, exit function

        # If errors were found, log and wait before retry
        log_and_print(f"(X) ODrive errors detected! (axis0: {axis0_errors}, motor: {motor_errors}, "
                      f"encoder: {encoder_errors}, controller: {controller_errors})")
        log_and_print("Pausing 5 seconds before retrying...")
        time.sleep(5)

        odrv0.axis0.controller.config.vel_limit = 65 # 65 is normal --- Add vel_limit = 0 somewhere to induce an error

        # Attempt recovery: clear and recalibrate
        log_and_print("Attempting to clear and recalibrate...")
        current_cfg = save_current_axis_config(odrv0.axis0) ######## SAVE CURRENT CONFIG before CALIBRATION
        odrv.clear_errors()
        odrv.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
        time.sleep(5)

        restore_axis_config(odrv0.axis0, current_cfg) ######## RESTORE CONFIG

        # Wait until calibration completes
        while odrv.axis0.current_state != AXIS_STATE_IDLE:
            time.sleep(0.5)

        attempt += 1

    # If still failing after all retries:
    log_and_print("(X) Unable to clear ODrive errors after maximum retries.")
    return False

def log_and_print(message):
    print(message)
    log_file.write(message + "\n")
    log_file.flush()  # Ensure each line is written immediately

def print_speed(input_speed):
    speed_message = (
        f"{time.time()}\t"
        f"{odrv0.axis0.controller.pos_setpoint}\t"
        f"{odrv0.axis0.encoder.pos_estimate}\t"
        f"{input_speed}\t"
        f"{odrv0.axis0.controller.input_pos}\t"
        f"{position_offset}\t"
        f"{odrv0.axis0.encoder.vel_estimate}"
    )
    log_and_print(speed_message)

def keep_awake(last_movement_time=None, interval=60):
    """
    Keeps the computer awake by moving the mouse slightly if the specified interval has passed.
    
    Parameters:
    last_movement_time (float): Timestamp of the last mouse movement.
    interval (int): Time in seconds to wait between each simulated mouse movement. Default is 60 seconds.
    
    Returns:
    float: Updated timestamp of the last mouse movement.
    """
    current_time = time.time()

    # If first call or interval has passed, move the mouse
    if last_movement_time is None or (current_time - last_movement_time >= interval):
        pyautogui.moveRel(0, 1)  # Move mouse 1 pixel down
        pyautogui.moveRel(0, -1) # Move mouse 1 pixel up
        last_movement_time = current_time  # Update last movement time
        print("Mouse moved to keep awake.")

    return last_movement_time

# Function to send and correct position
position_offset = 0.0

def send_and_correct_position(desired_position, velocity_limit=0.1, correct_delay=1.5):
    position_offset = 0.0
    
    # Send the position command
    odrv0.axis0.controller.input_pos = desired_position + position_offset
    time.sleep(0.25) # Delay to allow the disk to move
    # Wait until the disk has stopped
    # Wait until the disk stops or an error is detected
    while True:
        # Check velocity and break when nearly stopped
        if abs(odrv0.axis0.encoder.vel_estimate) <= velocity_limit:
            break
        
        # Inline error check
        if dump_and_check_errors(odrv0, max_retries=5) is False:
            log_and_print("(X) Persistent error detected during motion. Aborting move.")
            return  # Exit early
        
        time.sleep(0.1)  # Check every 100 ms
    
    time.sleep(correct_delay) # Delay to allow disk to stop
    # Calculate the offset
    actual_position = odrv0.axis0.encoder.pos_estimate
    position_offset = desired_position - actual_position
    time.sleep(0.5) # Delay to allow disk to stop

    # Send the corrected position
    odrv0.axis0.controller.input_pos = desired_position + position_offset
    time.sleep(0.25) # Delay to allow disk to stop
    
    # Log the correction
    print_speed(f"Desired: {desired_position}, Actual: {actual_position}, Offset: {position_offset}")

# Function to send position without correction and wait until near target
def send_position(desired_position):
    odrv0.axis0.controller.input_pos = desired_position
    print_speed(desired_position)
    
    # Wait until the disk is near the desired position
    while abs(odrv0.axis0.encoder.pos_estimate - desired_position) > 0.25:
        time.sleep(0.1)  # Check every 100ms
    print(f"Position reached near {desired_position}.")

# Define CSV headers for logging
Headers = (
    "Time\t"
    "Position Setpoint\t"
    "Encoder Position Estimate\t"
    "Input Speed\t"
    "Controller Input Position\t"
    "Position Offset\t"
    "Encoder Velocity Estimate"
)
log_and_print(Headers)

######## CALIBRATION and SETUP ########

# Initialize a variable to track the current position
current_position = 0.0
spin_distance = 15

# Example of using the function in a main program loop
last_movement_time = None

# Find a connected ODrive (this will block until you connect one)
print("finding an odrive...")
odrv0 = odrive.find_any()

print("Bus voltage is " + str(odrv0.vbus_voltage) + "V")
odrv0.axis0.requested_state = AXIS_STATE_IDLE
time.sleep(2)
# odrv0.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
print("Calibration...")
while odrv0.axis0.current_state != AXIS_STATE_IDLE:
    time.sleep(0.1)

dump_and_check_errors(odrv0)

#### New parameters -- stick with old ones for now
# odrv0.axis0.controller.config.pos_gain = 8
# odrv0.axis0.controller.config.vel_gain = 0.11
# odrv0.axis0.controller.config.vel_integrator_gain = 0.55

#### OLD Parameters
odrv0.axis0.controller.config.pos_gain = 5
odrv0.axis0.controller.config.vel_gain = 0.25
odrv0.axis0.controller.config.vel_integrator_gain = 1

odrv0.config.dc_bus_overvoltage_trip_level = 30 ## 56V board so this is ok

print("Amplification with 15 second hold at each well. [1] Spin to 50 and back to 0. [2] Alternate mixing between 0 and 10 for 15 minutes for RT at 50˚C. [3] Hold at each well for 15 seconds for 1 hour with every 13 wells, spin.")

######### BUBBLE TRAP #########
# Trajectory position control
odrv0.axis0.controller.config.input_mode = INPUT_MODE_TRAP_TRAJ
odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
odrv0.axis0.trap_traj.config.vel_limit = 10
odrv0.axis0.trap_traj.config.decel_limit = 2
odrv0.axis0.trap_traj.config.accel_limit = 2
odrv0.axis0.controller.config.circular_setpoints = False
time.sleep(2)

spin_distance = 50
current_position += spin_distance
print("Spin to 50")
send_and_correct_position(current_position)
time.sleep(0.25)  # Optional pause for spinning visualization

# Spin back to 0
spin_distance = -50
current_position += spin_distance
print("Spin to 0")
send_and_correct_position(current_position)
time.sleep(0.25)  # Optional pause for spinning visualization

dump_and_check_errors(odrv0)

############ RT STEP ALTERNATIVE MIXING ##############
odrv0.axis0.controller.config.input_mode = INPUT_MODE_TRAP_TRAJ
odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
odrv0.axis0.trap_traj.config.vel_limit = 12
odrv0.axis0.trap_traj.config.decel_limit = 20
odrv0.axis0.trap_traj.config.accel_limit = 20
odrv0.axis0.controller.config.circular_setpoints = False

print("Move to position zero to start RT step")
target_position = 10
current_position = 0
send_and_correct_position(current_position)  # Start at position 0
start_time = time.time()  # Record the start time
duration = 15 * 60  # Duration in seconds (15 minutes)
#duration = 30  # Duration in seconds (30 seconds for testing)

zero_pos = [0, 0.25, 0.5, 0.75]
i = 0

print("Alternative Mixing")
while time.time() - start_time < duration:
    current_position = target_position
    send_position(current_position)
    # Check if the current position is close to the target
    if abs(odrv0.axis0.encoder.pos_estimate - target_position) < 0.1:
        # Switch the target position
        target_position = 0 if target_position == 10 else 10
        if target_position == 0:
            set_position = target_position + zero_pos[i]
            i = i + 1 
            if i > 3: i = 0
        current_position = set_position
        send_and_correct_position(current_position)
        if target_position == 0:
            last_movement_time = keep_awake(last_movement_time, interval=60)
            time.sleep(10) # Wait at each side of the rotation

    print_speed(target_position)
    dump_and_check_errors(odrv0)
    # Small delay to avoid overloading the system
    time.sleep(0.1)

dump_and_check_errors(odrv0)

######### AMPLIFICATION STEP ##############
# Return to initial position after 10 minutes
current_position = 0
send_and_correct_position(current_position)
print("Returning to Position 0 for the beginning of Amplification")
time.sleep(5)

print("Amplification begins")
####### Amplification wells
odrv0.axis0.controller.config.input_mode = INPUT_MODE_POS_FILTER
odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
odrv0.axis0.controller.config.input_filter_bandwidth = 3.0
odrv0.axis0.controller.config.circular_setpoints = False

## Go to position 0 and wait for 5 seconds
zeroPoint = 0
print(zeroPoint)
current_position = zeroPoint
print("Returning to Position 0/Well 1 to start Amplification")
send_and_correct_position(current_position)
time.sleep(5)

dump_and_check_errors(odrv0)

# Set initial position and increment
positionWell = 0
position_increment = 0.25  # Increment step for each iteration

# Set sleep time per iteration (seconds)
sleep_time = 14

# Calculate the number of iterations to make the total time exactly one hour
total_time = 60*60+30*60  # total time in seconds (1 hour)
iterations = total_time // sleep_time

print("All wells for 15 seconds each")
#### Position Hold for an hour (3600 seconds)
for i in range(iterations):
    odrv0.axis0.controller.config.input_mode = INPUT_MODE_POS_FILTER
    odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
    odrv0.axis0.controller.config.input_filter_bandwidth = 3.0
    odrv0.axis0.controller.config.circular_setpoints = False
    #odrv0.axis0.controller.config.circular_setpoints = True

    # Increment to 0.75 and then reset to 0
    if positionWell >= 0.75:
        positionWell = 0
    else:
        positionWell += position_increment

    current_position = zeroPoint + positionWell
    send_and_correct_position(current_position, 0.075, 2)  # Use a tighter velocity limit for final approach since the disk moves so slowly
    print_speed(positionWell)
    last_movement_time = keep_awake(last_movement_time, interval=60)

    time.sleep(sleep_time) # Time at each well

    # Spin to 15 and then back to 0 every 13 wells
    if (i + 1) % 13 == 0:  # i + 1 because iteration starts at 0
        odrv0.axis0.controller.config.input_mode = INPUT_MODE_TRAP_TRAJ
        odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        odrv0.axis0.trap_traj.config.vel_limit = 10
        odrv0.axis0.trap_traj.config.decel_limit = 0.5
        odrv0.axis0.trap_traj.config.accel_limit = 2
        odrv0.axis0.controller.config.circular_setpoints = False

        # Spin to 15
        spin_distance = 30
        current_position += spin_distance
        send_and_correct_position(current_position)
        print(f"Spinning disk to {current_position} after iteration {i + 1}")
        time.sleep(0.25)  # Optional pause for spinning visualization
        
        # Spin back to 0
        spin_distance = -30
        current_position += spin_distance
        send_and_correct_position(current_position)
        print(f"Spinning disk back to {current_position} after iteration {i + 1}")
        time.sleep(0.25)  # Optional pause for spinning visualization

        dump_and_check_errors(odrv0)

#### Shut off
odrv0.axis0.requested_state = AXIS_STATE_IDLE
dump_errors(odrv0)
exit()