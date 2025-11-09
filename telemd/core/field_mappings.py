import statistics

# New conversion function to handle different operations
def process_can_data(data, start, end, signed=False, scale=1.0, operation='none', fallback=0.0):
    """
    Safely convert bytes to a value with a specified operation.
    Operations:
    - 'none', 'scaling': Treat bytes as a single integer and apply scaling.
    - 'mean', 'max', 'min': Treat each byte in the slice as a separate value
      and perform the specified operation. This is based on the interpretation
      that these operations apply to the byte values themselves.
    """
    try:
        if start >= len(data) or end > len(data):
            return fallback

        byte_slice = data[start:end]
        if not byte_slice:
            return fallback

        if operation in ['mean', 'max', 'min']:
            # Assumption: operation is on individual bytes in the slice.
            if signed:
                # Convert each byte to a signed integer
                values = [int.from_bytes([b], 'little', signed=True) for b in byte_slice]
            else:
                values = list(byte_slice)
            
            if not values:
                return fallback

            if operation == 'mean':
                result = statistics.mean(values)
            elif operation == 'max':
                result = max(values)
            else: # 'min'
                result = min(values)
            
            return result * scale

        else:  # 'none' or 'scaling'
            value = int.from_bytes(byte_slice, 'little', signed=signed)
            return value * scale
            
    except (ValueError, OverflowError, IndexError):
        return fallback

CAN_MAPPING = {
    0x0A0: [
        ("Inverter Temp", lambda d: process_can_data(d, 0, 2, signed=True, operation='mean')),
    ],
    0x0A2: [
        ("Motor Temp", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.1)),
    ],
    0x0A5: [
        ("Motor Angle", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.1)),
        ("RPM", lambda d: process_can_data(d, 2, 4, signed=True)),
        ("Inverter Frequency", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.1)),
        ("Resolver Angle", lambda d: process_can_data(d, 6, 8, signed=True, scale=0.1)),
    ],
    0x0A6: [
        ("Phase A Current", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.1)),
        ("Phase B Current", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.1)),
        ("Phase C Current", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.1)),
        ("Current Input into DC", lambda d: process_can_data(d, 6, 8, signed=True, scale=0.1)),
    ],
    0x0A7: [
        ("Voltage Input into DC", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.1)),
        ("Output Voltage", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.1)),
        ("AB Voltage", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.1)),
        ("BC Voltage", lambda d: process_can_data(d, 6, 8, signed=True, scale=0.1)),
    ],
    0x0AA: [
        ("State Vector", lambda d: process_can_data(d, 0, 8, signed=False)),
    ],
    0x0AB: [
        ("Fault Vector", lambda d: process_can_data(d, 0, 8, signed=False)),
    ],
    0x0AC: [
        ("Torque Command", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.1)),
        ("Actual Torque", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.1)),
    ],
    0x020: [
        ("IMD", lambda d: process_can_data(d, 0, 1, signed=False)),
        ("AMS", lambda d: process_can_data(d, 1, 2, signed=False)),
    ],
    0x220: [
        ("Voltage", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.01)),
        ("Current", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.01)),
        ("State of Charge", lambda d: process_can_data(d, 4, 5, signed=True, scale=0.01)),
        ("Pack Temp Maximum", lambda d: process_can_data(d, 5, 6, signed=True)),
        ("Pack Temp Minimum", lambda d: process_can_data(d, 6, 7, signed=True)),
    ],
    0x420: [
        ("Contactor Status", lambda d: process_can_data(d, 0, 1, signed=False)),
    ],
    0x230: [
        ("Volumetric Flow Rate", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.1)),
        ("Water Temp Motor", lambda d: process_can_data(d, 2, 3, signed=True)),
        ("Water Temp Inverter", lambda d: process_can_data(d, 3, 4, signed=True)),
        ("Water Temp Radiator", lambda d: process_can_data(d, 4, 5, signed=True)),
        ("Radiator Fan RPM Percentage", lambda d: process_can_data(d, 5, 6, signed=True)),
    ],
    0x330: [
        ("LV Voltage", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.01)),
        ("LV State of Charge", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.01)),
        ("LV Current", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.01)),
    ],
    0x340: [
        ("Front Right Wheel Speed", lambda d: process_can_data(d, 0, 4, signed=True, scale=0.0025)),
    ],
    0x344: [
        ("Front Left Wheel Speed", lambda d: process_can_data(d, 0, 4, signed=True, scale=0.0025)),
    ],
    0x348: [
        ("Back Right Wheel Speed", lambda d: process_can_data(d, 0, 4, signed=True, scale=0.0025)),
    ],
    0x34C: [
        ("Back Left Wheel Speed", lambda d: process_can_data(d, 0, 4, signed=True, scale=0.0025)),
    ],
    0x221: [
        ("HVC Acceleration X", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.01)),
        ("HVC Acceleration Y", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.01)),
        ("HVC Acceleration Z", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.01)),
    ],
    0x231: [
        ("PDU Acceleration X", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.01)),
        ("PDU Acceleration Y", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.01)),
        ("PDU Acceleration Z", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.01)),
    ],
    0x341: [
        ("Front Right Acceleration X", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.01)),
        ("Front Right Acceleration Y", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.01)),
        ("Front Right Acceleration Z", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.01)),
    ],
    0x345: [
        ("Front Left Acceleration X", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.01)),
        ("Front Left Acceleration Y", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.01)),
        ("Front Left Acceleration Z", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.01)),
    ],
    0x349: [
        ("Back Right Acceleration X", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.01)),
        ("Back Right Acceleration Y", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.01)),
        ("Back Right Acceleration Z", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.01)),
    ],
    0x34D: [
        ("Back Left Acceleration X", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.01)),
        ("Back Left Acceleration Y", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.01)),
        ("Back Left Acceleration Z", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.01)),
    ],
    **{
        i: [
            ("Cell Voltage Mean", lambda d: process_can_data(d, 0, 2, signed=True, operation='mean')),
            ("Cell Voltage Max", lambda d: process_can_data(d, 2, 4, signed=True, operation='max')),
            ("Cell Voltage Min", lambda d: process_can_data(d, 4, 6, signed=True, operation='min')),
        ]
        for i in range(0x370, 0x393)
    },
    **{
        i: [
            ("Cell Temps Mean", lambda d: process_can_data(d, 0, 2, signed=True, operation='mean')),
            ("Cell Temps Max", lambda d: process_can_data(d, 2, 4, signed=True)),
            ("Cell Temps Min", lambda d: process_can_data(d, 4, 6, signed=True)),
        ]
        for i in range(0x470, 0x487)
    }
}

# Mapping from server field names to CSV column names

CSV_PROTBUF_MAPPING = {
    "time" : "Time",
    "torque_request": "Inverter Torque Request",
    "vcu_position": ["Vehicle Displacement X", "Vehicle Displacement Y", "Vehicle Displacement Z"],
    "vcu_velocity": ["Vehicle Velocity X", "Vehicle Velocity Y", "Vehicle Velocity Z"],
    "vcu_accel": ["Vehicle Acceleration X", "Vehicle Acceleration Y", "Vehicle Acceleration Z"],
    "gps": ["Longitude", "Latitude"],
    "gps_velocity": "Speed",
    "gps_heading": "Heading",
    "body1_accel": ["VCU Acceleration X", "VCU Acceleration Y", "VCU Acceleration Z"],
    "body2_accel": ["HVC Acceleration X", "HVC Acceleration Y", "HVC Acceleration Z"],
    "body3_accel": ["PDU Acceleration X", "PDU Acceleration Y", "PDU Acceleration Z"],
    "flw_accel": ["Front Left Acceleration X", "Front Left Acceleration Y", "Front Left Acceleration Z"],
    "frw_accel": ["Front Right Acceleration X", "Front Right Acceleration Y", "Front Right Acceleration Z"],
    "blw_accel": ["Back Left Acceleration X", "Back Left Acceleration Y", "Back Left Acceleration Z"],
    "brw_accel": ["Back Right Acceleration X", "Back Right Acceleration Y", "Back Right Acceleration Z"],
    "body1_gyro": ["VCU Gyro X", "VCU Gyro Y", "VCU Gyro Z"],
    "body2_gyro": ["HVC Gyro X", "HVC Gyro Y", "HVC Gyro Z"],
    "body3_gyro": ["PDU Gyro X", "PDU Gyro Y", "PDU Gyro Z"],
    "flw_speed": "Front Left Wheel Speed",
    "frw_speed": "Front Right Wheel Speed",
    "blw_speed": "Back Left Wheel Speed",
    "brw_speed": "Back Right Wheel Speed",
    "inverter_v": "Voltage",
    "inverter_c": "Current",
    "inverter_rpm": "RPM",
    "inverter_torque": "Actual Torque",
    "apps1_v": "APPS 1 Voltage",
    "apps2_v": "APPS 2 Voltage",
    "bse1_v": "BSE 1 Voltage",
    "bse2_v": "BSE 2 Voltage",
    "sus1_v": "Suspension 1 Voltage",
    "sus2_v": "Suspension 2 Voltage",
    "steer_v": "Steer Voltage",
    "hv_pack_v": "Pack Voltage Mean",
    "hv_tractive_v": "Voltage Input into DC",
    "hv_c": "Current Input into DC",
    "lv_v": "LV Voltage",
    "lv_c": "LV Current",
    "contactor_state": "Contactor Status",
    "avg_cell_v": "Cell Voltage Mean",
    "avg_cell_temp": "Cell Temps Mean",
    "hv_charge_state": "State of Charge",
    "lv_charge_state": "LV State of Charge",
    "cells_temp": ["Segment 1 Max", "Segment 1 Min", "Segment 2 Max", "Segment 2 Min", 
                "Segment 3 Max", "Segment 3 Min", "Segment 4 Max", "Segment 4 Min"],
    "inverter_temp": "Inverter Temp",
    "motor_temp": "Motor Temp",
    "water_motor_temp": "Water Temp Motor",
    "water_inverter_temp": "Water Temp Inverter",
    "water_rad_temp": "Water Temp Radiator",
    "rad_fan_rpm": "Radiator Fan RPM Percentage",
    "flow_rate": "Volumetric Flow Rate"
}

