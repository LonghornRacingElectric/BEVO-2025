#define lambdas outside to avoid recompliations
CAN_MAPPING = {
    # Dynamics - Steering and angles
    0xA05: ("dynamics.steer_col_angle", lambda d: int.from_bytes(d[0:2], 'little', signed=True) * 0.004),
    0x400: ("dynamics.fl_steer_angle", lambda d: int.from_bytes(d[0:2], 'little', signed=True) * 0.001),
    0x401: ("dynamics.fr_steer_angle", lambda d: int.from_bytes(d[0:2], 'little', signed=True) * 0.001),
    
    # Dynamics - Wheel speeds
    0x406: ("dynamics.flw_speed", lambda d: int.from_bytes(d[0:2], 'little', signed=True) * 0.01),
    0x407: ("dynamics.frw_speed", lambda d: int.from_bytes(d[0:2], 'little', signed=True) * 0.01),
    0x408: ("dynamics.blw_speed", lambda d: int.from_bytes(d[0:2], 'little', signed=True) * 0.01),
    0x409: ("dynamics.brw_speed", lambda d: int.from_bytes(d[0:2], 'little', signed=True) * 0.01),
    
    # Dynamics - Ride heights
    0x500: ("dynamics.fl_ride_height", lambda d: int.from_bytes(d[6:8], 'little') * 0.002),
    0x501: ("dynamics.fr_ride_height", lambda d: int.from_bytes(d[6:8], 'little') * 0.002),
    0x502: ("dynamics.bl_ride_height", lambda d: int.from_bytes(d[6:8], 'little') * 0.002),
    0x503: ("dynamics.br_ride_height", lambda d: int.from_bytes(d[6:8], 'little') * 0.002),
    
    # Dynamics - Strain gauge voltages
    0x406: ("dynamics.fl_strain_gauge_v", lambda d: int.from_bytes(d[2:4], 'little', signed=True) * 0.0002),
    0x407: ("dynamics.fr_strain_gauge_v", lambda d: int.from_bytes(d[2:4], 'little', signed=True) * 0.0002),
    0x408: ("dynamics.bl_strain_gauge_v", lambda d: int.from_bytes(d[2:4], 'little', signed=True) * 0.0002),
    0x409: ("dynamics.br_strain_gauge_v", lambda d: int.from_bytes(d[2:4], 'little', signed=True) * 0.0002),
    
    # Dynamics - Pushrod stress
    0x406: ("dynamics.fl_pushrod_stress", lambda d: int.from_bytes(d[4:6], 'little', signed=True) * 0.5),
    0x407: ("dynamics.fr_pushrod_stress", lambda d: int.from_bytes(d[4:6], 'little', signed=True) * 0.5),
    0x408: ("dynamics.bl_pushrod_stress", lambda d: int.from_bytes(d[4:6], 'little', signed=True) * 0.5),
    0x409: ("dynamics.br_pushrod_stress", lambda d: int.from_bytes(d[4:6], 'little', signed=True) * 0.5),
    
    # Dynamics - Spring displacement
    0x406: ("dynamics.fl_spring_displace", lambda d: int.from_bytes(d[6:8], 'little') * 0.001),
    0x407: ("dynamics.fr_spring_displace", lambda d: int.from_bytes(d[6:8], 'little') * 0.001),
    0x408: ("dynamics.bl_spring_displace", lambda d: int.from_bytes(d[6:8], 'little') * 0.001),
    0x409: ("dynamics.br_spring_displace", lambda d: int.from_bytes(d[6:8], 'little') * 0.001),
    
    # Dynamics - Sprung acceleration vectors (3D)
    0x500: ("dynamics.fl_sprung_accel", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.001,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.001,
        int.from_bytes(d[4:6], 'little', signed=True) * 0.001
    ]),
    0x501: ("dynamics.fr_sprung_accel", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.001,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.001,
        int.from_bytes(d[4:6], 'little', signed=True) * 0.001
    ]),
    0x502: ("dynamics.bl_sprung_accel", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.001,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.001,
        int.from_bytes(d[4:6], 'little', signed=True) * 0.001
    ]),
    0x503: ("dynamics.br_sprung_accel", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.001,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.001,
        int.from_bytes(d[4:6], 'little', signed=True) * 0.001
    ]),
    
    # Dynamics - Unsprung acceleration vectors (3D)
    0x402: ("dynamics.fl_unsprung_accel", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.001,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.001,
        int.from_bytes(d[4:6], 'little', signed=True) * 0.001
    ]),
    0x403: ("dynamics.fr_unsprung_accel", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.001,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.001,
        int.from_bytes(d[4:6], 'little', signed=True) * 0.001
    ]),
    0x404: ("dynamics.bl_unsprung_accel", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.001,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.001,
        int.from_bytes(d[4:6], 'little', signed=True) * 0.001
    ]),
    0x405: ("dynamics.br_unsprung_accel", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.001,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.001,
        int.from_bytes(d[4:6], 'little', signed=True) * 0.001
    ]),
    
    # Dynamics - Angular rate vectors (3D)
    0x504: ("dynamics.fl_sprung_ang_rate", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.03,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.03,
        int.from_bytes(d[4:6], 'little', signed=True) * 0.03
    ]),
    0x505: ("dynamics.fr_sprung_ang_rate", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.03,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.03,
        int.from_bytes(d[4:6], 'little', signed=True) * 0.03
    ]),
    0x506: ("dynamics.bl_sprung_ang_rate", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.03,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.03,
        int.from_bytes(d[4:6], 'little', signed=True) * 0.03
    ]),
    0x507: ("dynamics.br_sprung_ang_rate", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.03,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.03,
        int.from_bytes(d[4:6], 'little', signed=True) * 0.03
    ]),
    
    # Dynamics - Center mass (placeholder for now)
    0x111: ("dynamics.cent_mass_accel", lambda d: [0.0, 0.0, 0.0]),
    0x112: ("dynamics.cent_mass_ang_rate", lambda d: [0.0, 0.0, 0.0]),
    
    # Controls - BSE voltages
    0x100: ("controls.bse1_v", lambda d: int.from_bytes(d[0:2], 'little') * 0.0001),
    0x100: ("controls.bse2_v", lambda d: int.from_bytes(d[2:4], 'little') * 0.0001),
    0x100: ("controls.bse3_v", lambda d: int.from_bytes(d[4:6], 'little') * 0.0001),
    
    # Controls - Brake pressures
    0xA04: ("controls.brake_pressure_f", lambda d: int.from_bytes(d[0:2], 'little') * 0.05),
    0xA04: ("controls.brake_pressure_rbll", lambda d: int.from_bytes(d[2:4], 'little') * 0.05),
    0xA04: ("controls.brake_pressure_rall", lambda d: int.from_bytes(d[4:6], 'little') * 0.05),
    0xA04: ("controls.brake_bias", lambda d: d[6] * 0.01),
    
    # Pack - Battery pack status
    0x200: ("pack.hv_pack_v", lambda d: int.from_bytes(d[0:2], 'little') * 0.01),
    0x200: ("pack.hv_c", lambda d: int.from_bytes(d[2:4], 'little') * 0.01),
    0x200: ("pack.hv_soc", lambda d: int.from_bytes(d[4:6], 'little') * 0.01),
    
    # Diagnostics High - APPS faults (bitfield)
    0xF1: ("diagnostics_high.apps1_disconnect", lambda d: bool(d[2] & 0x01)),
    0xF1: ("diagnostics_high.apps2_disconnect", lambda d: bool(d[2] & 0x02)),
    0xF1: ("diagnostics_high.apps1_out_range", lambda d: bool(d[2] & 0x04)),
    0xF1: ("diagnostics_high.apps2_out_range", lambda d: bool(d[2] & 0x08)),
    0xF1: ("diagnostics_high.apps_mismatch", lambda d: bool(d[2] & 0x10)),
    0xF1: ("diagnostics_high.apps_implause", lambda d: bool(d[2] & 0x20)),
    
    # Diagnostics High - BPPS faults (bitfield)
    0xF3: ("diagnostics_high.bpps1_disconnect", lambda d: bool(d[2] & 0x01)),
    0xF3: ("diagnostics_high.bpps2_disconnect", lambda d: bool(d[2] & 0x02)),
    0xF3: ("diagnostics_high.bpps1_out_range", lambda d: bool(d[2] & 0x04)),
    0xF3: ("diagnostics_high.bpps2_out_range", lambda d: bool(d[2] & 0x08)),
    0xF3: ("diagnostics_high.bpps_mismatch", lambda d: bool(d[2] & 0x10)),
    
    # Diagnostics High - BSE faults (bitfield)
    0xA04: ("diagnostics_high.bse1_disconnect", lambda d: bool(d[7] & 0x01)),
    0xA04: ("diagnostics_high.bse2_disconnect", lambda d: bool(d[7] & 0x02)),
    0xA04: ("diagnostics_high.bse1_out_range", lambda d: bool(d[7] & 0x04)),
    0xA04: ("diagnostics_high.bse2_out_range", lambda d: bool(d[7] & 0x08)),
    
    # Diagnostics Low - Shutdown legs
    0x202: ("diagnostics_low.shutdown_leg1", lambda d: bool(d[2])),
    0x202: ("diagnostics_low.shutdown_leg2", lambda d: bool(d[3])),
    0x202: ("diagnostics_low.shutdown_leg3", lambda d: bool(d[4])),
    0x202: ("diagnostics_low.shutdown_leg4", lambda d: bool(d[5])),
    
    # Diagnostics Low - BMS and IMD errors
    0x202: ("diagnostics_low.bmb_comm_error", lambda d: bool(d[0])),
    0x202: ("diagnostics_low.imd_gnd_isolation_error", lambda d: bool(d[1])),
    
    # Thermal - Motor cooling
    0x102: ("thermal.motor_loop_motor_temp", lambda d: int.from_bytes(d[0:2], 'little', signed=True) * 0.01),
    0x102: ("thermal.motor_loop_inverter_temp", lambda d: int.from_bytes(d[2:4], 'little', signed=True) * 0.01),
    0x102: ("thermal.motor_loop_rad_temp", lambda d: int.from_bytes(d[4:6], 'little', signed=True) * 0.01),
    0x102: ("thermal.motor_loop_rad_fan_speed", lambda d: int.from_bytes(d[6:8], 'little') * 0.2),
    
    # Thermal - Battery cooling
    0x103: ("thermal.batt_loop_batt_temp", lambda d: int.from_bytes(d[0:2], 'little', signed=True) * 0.01),
    0x103: ("thermal.batt_loop_rad_temp", lambda d: int.from_bytes(d[2:4], 'little', signed=True) * 0.01),
    0x103: ("thermal.batt_loop_rad_fan_speed", lambda d: int.from_bytes(d[4:6], 'little') * 0.2),
    
    # Thermal - Component temperatures
    0x104: ("thermal.motor_temp", lambda d: int.from_bytes(d[2:4], 'little', signed=True) * 0.01),
    0x104: ("thermal.inverter_temp", lambda d: int.from_bytes(d[0:2], 'little', signed=True) * 0.01),
    0x104: ("thermal.ambient_temp", lambda d: int.from_bytes(d[4:6], 'little', signed=True) * 0.01),
    0x104: ("thermal.discharge_r_temp", lambda d: int.from_bytes(d[6:8], 'little', signed=True) * 0.01),
    
    # Thermal - Bus bar temperatures
    0x201: ("thermal.bus_bar_temp1", lambda d: int.from_bytes(d[0:2], 'little') * 0.1),
    0x201: ("thermal.bus_bar_temp2", lambda d: int.from_bytes(d[2:4], 'little') * 0.1),
    0x201: ("thermal.bus_bar_temp3", lambda d: int.from_bytes(d[4:6], 'little') * 0.1),
    0x201: ("thermal.precharge_r_temp", lambda d: int.from_bytes(d[6:8], 'little') * 0.1),
    
    # GPS data
    0x101: ("dynamics.b_gps", lambda d: [
        int.from_bytes(d[0:2], 'little', signed=True) * 0.001,
        int.from_bytes(d[2:4], 'little', signed=True) * 0.001
    ]),
    0x101: ("dynamics.b_gps_velocity", lambda d: int.from_bytes(d[4:6], 'little') * 0.001),
    0x101: ("dynamics.b_gps_heading", lambda d: int.from_bytes(d[6:8], 'little') * 0.001),
    
    # Legacy mapping for shutdown_leg1 (0x6CA)
    0x6CA: ("diagnostics_low.shutdown_leg1", lambda d: bool(d[0]) if len(d) > 0 else False)
}
