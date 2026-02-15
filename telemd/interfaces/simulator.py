import time
import random
import math
import platform


class CANGenerator:
    """Simulates CAN messages for speed, pack SoC, and max cell temp"""
    
    def __init__(self):
        self.start_time = time.time()
        self.message_count = 0
        self.last_speed_time = 0
        self.last_pack_time = 0
        self.last_shutdown_time = 0
        # Simulate 12 shutdown legs
        self.shutdown_legs = [True] * 12
        
    def recv(self, timeout=0.01):
        """Generate simulated CAN messages"""
        time.sleep(timeout)  # Simulate timeout
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Generate different messages at different frequencies
        messages = []
        
        # Speed messages (wheel speeds) at 100Hz
        if current_time - self.last_speed_time >= 0.01:  # 100Hz
            messages.append(self._generate_wheel_speeds(elapsed))
            self.last_speed_time = current_time
        
        # Pack SoC and cell temp at 10Hz
        if current_time - self.last_pack_time >= 0.1:  # 10Hz
            messages.append(self._generate_pack_soc(elapsed))
            self.last_pack_time = current_time
        
        # Shutdown legs at 10Hz
        if current_time - self.last_shutdown_time >= 0.1:
            messages.append(self._generate_shutdown_legs(elapsed))
            messages.append(self._generate_shutdown_legs_2(elapsed))
            self.last_shutdown_time = current_time
        
        # Return all available messages
        if messages:
            self.message_count += len(messages)
            return messages
        
        return None
    
    def _generate_wheel_speeds(self, elapsed):
        """Generate wheel speed data (CAN ID 0x406) - Speed only"""
        # Simulate realistic speed pattern: oscillating between 10-50 km/h
        base_speed = 30 + 20 * math.sin(elapsed * 0.1)  # Oscillating between 10-50 km/h
        speed = max(0, base_speed + random.uniform(-2, 2))  # Add some noise
        
        # Convert to raw value (0.01 scaling factor) - ensure positive and within range
        speed_raw = max(0, min(32767, int(speed / 0.01)))  # 16-bit signed max
        
        # Fill rest of packet with zeros for other fields (strain gauge, pushrod, spring)
        data = speed_raw.to_bytes(2, 'little', signed=True) + b'\x00' * 6
        
        class MockCANMessage:
            def __init__(self, arbitration_id, data, timestamp):
                self.arbitration_id = arbitration_id
                self.data = data
                self.timestamp = timestamp
        
        return MockCANMessage(0x406, data, time.time())
    
    def _generate_pack_soc(self, elapsed):
        """Generate pack SoC and cell temp data (CAN ID 0x200) - Battery Pack Status"""
        # Simulate battery SoC: oscillating between 70-90%
        base_soc = 80 + 10 * math.sin(elapsed * 0.05)  # Oscillating between 70-90%
        soc = max(0, min(100, base_soc + random.uniform(-1, 1)))
        
        # Simulate cell temperatures: oscillating around 25-40°C
        cell_top_temp = max(0, min(255, int(25 + 10 * math.sin(elapsed * 0.2) + random.uniform(-2, 2))))
        cell_bottom_temp = max(0, min(255, int(28 + 8 * math.cos(elapsed * 0.15) + random.uniform(-2, 2))))
        
        # Pack voltage (correlated with SoC) - ensure reasonable ranges
        pack_v = int(max(0, min(65535, 400 + soc * 0.5 + random.uniform(-5, 5))))  # 400-450V range
        tractive_c = max(0, min(65535, int(random.uniform(-50, 50) + 32768)))  # Can be positive (charging) or negative (discharging), offset to unsigned
        
        # Ensure all values are within their respective ranges before conversion
        pack_v_raw = max(0, min(65535, int(pack_v / 0.01)))
        tractive_c_raw = max(0, min(65535, int(tractive_c / 0.01)))
        soc_raw = max(0, min(65535, int(soc / 0.01)))  # 0-100% * 100 = 0-10000
        
        data = (
            pack_v_raw.to_bytes(2, 'little') +
            tractive_c_raw.to_bytes(2, 'little') +
            soc_raw.to_bytes(2, 'little') +
            cell_top_temp.to_bytes(1, 'little') +
            cell_bottom_temp.to_bytes(1, 'little')
        )
        
        class MockCANMessage:
            def __init__(self, arbitration_id, data, timestamp):
                self.arbitration_id = arbitration_id
                self.data = data
                self.timestamp = timestamp
        
        return MockCANMessage(0x200, data, time.time())
    
    def _generate_shutdown_legs(self, elapsed):
        """Generate shutdown leg status (CAN ID 0x202)"""
        # All legs default to True
        self.shutdown_legs = [True] * 12
        # With small probability, trip a random leg and all after it
        if random.random() < 0.05:
            trip_index = random.randint(0, 11)
            for i in range(trip_index, 12):
                self.shutdown_legs[i] = False
        # Compose 8 bytes: first 2 bytes for errors, next 6 for shutdown_leg1-6
        data = bytearray(8)
        for i in range(6):
            data[2 + i] = 1 if self.shutdown_legs[i] else 0
        
        class MockCANMessage:
            def __init__(self, arbitration_id, data, timestamp):
                self.arbitration_id = arbitration_id
                self.data = data
                self.timestamp = timestamp
        
        return MockCANMessage(0x202, bytes(data), time.time())
    
    def _generate_shutdown_legs_2(self, elapsed):
        """Generate shutdown leg status for legs 7-12 (CAN ID 0x204)"""
        data = bytearray(8)
        for i in range(6):
            data[i] = 1 if self.shutdown_legs[6 + i] else 0
        
        class MockCANMessage:
            def __init__(self, arbitration_id, data, timestamp):
                self.arbitration_id = arbitration_id
                self.data = data
                self.timestamp = timestamp
        
        return MockCANMessage(0x204, bytes(data), time.time())
    
    def shutdown(self):
        """Clean shutdown"""
        print(f"CAN Generator shutdown. Generated {self.message_count} messages.") 