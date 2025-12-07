import statistics

# New conversion function to handle different operations
def process_can_data(data, start, end, signed=False, scale=1.0, operation='none', chunk_size=None, fallback=0.0):
    """
    Safely convert bytes to a value with a specified operation.
    Operations:
    - 'none', 'scaling': Treat bytes as a single integer and apply scaling.
    - 'mean', 'max', 'min': Treat each byte in the slice as a separate value
      and perform the specified operation. This is based on the interpretation
      that these operations apply to the byte values themselves.
      If chunk_size is specified, the operation is performed on multi-byte chunks.
    """
    try:
        if start >= len(data) or end > len(data):
            return fallback

        byte_slice = data[start:end]
        if not byte_slice:
            return fallback

        if operation in ['mean', 'max', 'min']:
            values = []
            if chunk_size:
                if len(byte_slice) % chunk_size != 0:
                    return fallback
                for i in range(0, len(byte_slice), chunk_size):
                    chunk = byte_slice[i:i+chunk_size]
                    values.append(int.from_bytes(chunk, 'little', signed=signed))
            else:
                # Original behavior: operation on individual bytes
                if signed:
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
        ("thermal.inverter_temp", lambda d: process_can_data(d, 0, 6, signed=True, operation='mean', chunk_size=2)),
    ],
    0x0A2: [
        ("thermal.motor_temp", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.1)),
    ],
    0x0A5: [
        # ("dynamics.motor_angle", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.1)), // not sending in protobuf template but data available
        ("dynamics.inverter_rpm", lambda d: process_can_data(d, 2, 4, signed=True)),
        # ("dynamics.inverter_frequency", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.1)),
        # ("dynamics.resolver_angle", lambda d: process_can_data(d, 6, 8, signed=True, scale=0.1)),
    ],
    0x0A6: [
        # ("dynamics.phase_a_current", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.1)),
        # ("dynamics.phase_b_current", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.1)),
        # ("dynamics.phase_c_current", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.1)),
        ("dynamics.inverter_c", lambda d: process_can_data(d, 6, 8, signed=True, scale=0.1)),
    ],
    0x0A7: [
        ("dynamics.inverter_v", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.1)),
        # ("dynamics.output_voltage", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.1)),
        # ("dynamics.ab_voltage", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.1)),
        # ("dynamics.bc_voltage", lambda d: process_can_data(d, 6, 8, signed=True, scale=0.1)),
    ],
    # Telemetry unused with flag data and error data
    # 0x0AA: [
    #     ("controls.vcu_flags", lambda d: process_can_data(d, 0, 8, signed=False)),
    # ],
    # 0x0AB: [
    #     ("diagnostics.current_errors", lambda d: process_can_data(d, 0, 8, signed=False)),
    # ],
    # 0x0AC: [
    #     #("dynamics.torque_request", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.1)),
    #     ("dynamics.inverter_torque", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.1)),
    # ],
    0x0C0: [
        ("dynamics.torque_request", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.1)),
        ("dynamics.inverter_torque", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.1)),
    ],
    # 0x020: [
    #     ("diagnostics.imd", lambda d: process_can_data(d, 0, 1, signed=False)),
    #     ("diagnostics.ams", lambda d: process_can_data(d, 1, 2, signed=False)),
    # ],
    0x220: [
        ("pack.hv_pack_v", lambda d: process_can_data(d, 0, 2, signed=False, scale=0.01)),
        ("pack.hv_c", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.01)),
        ("diagnostics.hv_charge_state", lambda d: process_can_data(d, 4, 6, signed=False, scale=0.01)),
        ("thermal.pack_temp_max", lambda d: process_can_data(d, 6, 7, signed=False)),
        ("thermal.pack_temp_min", lambda d: process_can_data(d, 7, 8, signed=False)),
    ],
    0x420: [
        ("pack.contactor_state", lambda d: process_can_data(d, 0, 1, signed=False)),
    ],
    0x230: [
        ("thermal.flow_rate", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.1)),
        ("thermal.water_motor_temp", lambda d: process_can_data(d, 2, 3, signed=True)),
        ("thermal.water_inverter_temp", lambda d: process_can_data(d, 3, 4, signed=True)),
        ("thermal.water_rad_temp", lambda d: process_can_data(d, 4, 5, signed=True)),
        ("thermal.rad_fan_rpm", lambda d: process_can_data(d, 5, 6, signed=True)),
    ],
    0x330: [
        ("pack.lv_v", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.01)),
        ("diagnostics.lv_charge_state", lambda d: process_can_data(d, 2, 4, signed=False, scale=0.01)),
        ("pack.lv_c", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.01)),
    ],
    0x340: [
        ("dynamics.frw_speed", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.0025)),
    ],
    0x344: [
        ("dynamics.flw_speed", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.0025)),
    ],
    0x348: [
        ("dynamics.brw_speed", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.0025)),
    ],
    0x34C: [
        ("dynamics.blw_speed", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.0025)),
    ],
    0x221: [
        ("HVC Acceleration X", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.01)),
        ("HVC Acceleration Y", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.01)),
        ("HVC Acceleration Z", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.01)),
    ],
    0x222:[
        ("HVC Gyro X", lambda d: process_can_data(d, 0, 2, signed=True, scale = 0.01)),
        ("HVC Gyro Y", lambda d: process_can_data(d, 2, 4, signed=True, scale = 0.01)),
        ("HVC Gyro Z", lambda d: process_can_data(d, 4, 6, signed=True, scale = 0.01)),
    ],
    0x231: [
        ("PDU Acceleration X", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.01)),
        ("PDU Acceleration Y", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.01)),
        ("PDU Acceleration Z", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.01)),
    ],
    0x232:[
        ("PDU Gyro X", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.01)),
        ("PDU Gyro Y", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.01)),
        ("PDU Gyro Z", lambda d: process_can_data(d, 4, 6, signed=True, scale=0.01)),
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
    0x600:[
        ("Latitude", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.001)), 
        ("Longitude", lambda d: process_can_data(d, 2, 4, signed=True, scale=0.001)),
           ], # unpack csv name to protobuf
    #0x601:[("Longitude", lambda d: process_can_data(d, 0, 2, signed=True, scale=0.001))]
}

class CellDataAggregator:
    """A stateful class to aggregate and average cell voltage and temperature data."""
    def __init__(self):
        self.voltages = {}
        self.temperatures = {}

    def _parse_data(self, data):
        """Parses an 8-byte payload into 4 signed 16-bit integers."""
        values = []
        for i in range(0, 8, 2):
            val = int.from_bytes(data[i:i+2], 'little', signed=False)
            values.append(val)
        return values

    def process_voltage(self, can_id, data):
        """Processes a voltage CAN message, updates state, and returns aggregated data."""
        self.voltages[can_id] = self._parse_data(data)
        all_voltages = [v * 0.0001 for id_vals in self.voltages.values() for v in id_vals]
        avg_voltage = statistics.mean(all_voltages) if all_voltages else 0.0
        return all_voltages, avg_voltage

    def process_temperature(self, can_id, data):
        """Processes a temperature CAN message, updates state, and returns aggregated data."""
        self.temperatures[can_id] = self._parse_data(data)
        all_temps = [int(t * 0.1) for id_vals in self.temperatures.values() for t in id_vals]
        avg_temp = statistics.mean(all_temps) if all_temps else 0.0
        return all_temps, avg_temp

# Mapping from server field names to CSV column names

CSV_PROTBUF_MAPPING = {
    "time" : "Time",
    "dynamics.torque_request": "Inverter Torque Request",
    "dynamics.vcu_position": ["Vehicle Displacement X", "Vehicle Displacement Y", "Vehicle Displacement Z"],
    "dynamics.vcu_velocity": ["Vehicle Velocity X", "Vehicle Velocity Y", "Vehicle Velocity Z"],
    "dynamics.vcu_accel": ["Vehicle Acceleration X", "Vehicle Acceleration Y", "Vehicle Acceleration Z"],
    "dynamics.gps": ["Longitude", "Latitude"],
    "dynamics.gps_velocity": "Speed",
    "dynamics.gps_heading": "Heading",
    "dynamics.body1_accel": ["VCU Acceleration X", "VCU Acceleration Y", "VCU Acceleration Z"],
    "dynamics.body2_accel": ["HVC Acceleration X", "HVC Acceleration Y", "HVC Acceleration Z"],
    "dynamics.body3_accel": ["PDU Acceleration X", "PDU Acceleration Y", "PDU Acceleration Z"],
    "dynamics.flw_accel": ["Front Left Acceleration X", "Front Left Acceleration Y", "Front Left Acceleration Z"],
    "dynamics.frw_accel": ["Front Right Acceleration X", "Front Right Acceleration Y", "Front Right Acceleration Z"],
    "dynamics.blw_accel": ["Back Left Acceleration X", "Back Left Acceleration Y", "Back Left Acceleration Z"],
    "dynamics.brw_accel": ["Back Right Acceleration X", "Back Right Acceleration Y", "Back Right Acceleration Z"],
    "dynamics.body1_gyro": ["VCU Gyro X", "VCU Gyro Y", "VCU Gyro Z"],
    "dynamics.body2_gyro": ["HVC Gyro X", "HVC Gyro Y", "HVC Gyro Z"],
    "dynamics.body3_gyro": ["PDU Gyro X", "PDU Gyro Y", "PDU Gyro Z"],
    "dynamics.flw_speed": "Front Left Wheel Speed",
    "dynamics.frw_speed": "Front Right Wheel Speed",
    "dynamics.blw_speed": "Back Left Wheel Speed",
    "dynamics.brw_speed": "Back Right Wheel Speed",
    "dynamics.inverter_v": "Voltage",
    "dynamics.inverter_c": "Current",
    "dynamics.inverter_rpm": "RPM",
    "dynamics.inverter_torque": "Actual Torque",
    "controls.apps1_v": "APPS 1 Voltage",
    "controls.apps2_v": "APPS 2 Voltage",
    "controls.bse1_v": "BSE 1 Voltage",
    "controls.bse2_v": "BSE 2 Voltage",
    "controls.sus1_v": "Suspension 1 Voltage",
    "controls.sus2_v": "Suspension 2 Voltage",
    "controls.steer_v": "Steer Voltage",
    "pack.hv_pack_v": "Pack Voltage Mean",
    "pack.hv_tractive_v": "Voltage Input into DC",
    "pack.hv_c": "Current Input into DC",
    "pack.lv_v": "LV Voltage",
    "pack.lv_c": "LV Current",
    "pack.contactor_state": "Contactor Status",
    "pack.avg_cell_v": "Cell Voltage Mean",
    "pack.avg_cell_temp": "Cell Temps Mean",
    "diagnostics.hv_charge_state": "State of Charge",
    "diagnostics.lv_charge_state": "LV State of Charge",
    "thermal.cells_temp": ["Segment 1 Max", "Segment 1 Min", "Segment 2 Max", "Segment 2 Min", 
                "Segment 3 Max", "Segment 3 Min", "Segment 4 Max", "Segment 4 Min"],
    "thermal.inverter_temp": "Inverter Temp",
    "thermal.motor_temp": "Motor Temp",
    "thermal.water_motor_temp": "Water Temp Motor",
    "thermal.water_inverter_temp": "Water Temp Inverter",
    "thermal.water_rad_temp": "Water Temp Radiator",
    "thermal.rad_fan_rpm": "Radiator Fan RPM Percentage",
    "thermal.flow_rate": "Volumetric Flow Rate"
}

# Create a reverse mapping from CSV column name to protobuf field name
CSV_TO_PROTOBUF_MAPPING = {}
for proto_field, csv_field in CSV_PROTBUF_MAPPING.items():
    if isinstance(csv_field, list):
        size = len(csv_field)
        for i, item in enumerate(csv_field):
            CSV_TO_PROTOBUF_MAPPING[item] = (proto_field, i, size)
    else:
        CSV_TO_PROTOBUF_MAPPING[csv_field] = (proto_field, None, None)

def get_protobuf_field_and_index(csv_field_name):
    """Get the protobuf field name, index, and size from the CSV field name."""
    return CSV_TO_PROTOBUF_MAPPING.get(csv_field_name)
