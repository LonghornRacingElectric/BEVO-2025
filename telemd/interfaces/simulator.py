import time
import random
import math
import platform


class CANGenerator:
    """Simulates CAN messages for non-Linux systems"""
    
    def __init__(self):
        self.start_time = time.time()
        self.message_count = 0
        
    def recv(self, timeout=0.01):
        """Generate simulated CAN messages"""
        time.sleep(timeout)  # Simulate timeout
        
        # Generate messages at different frequencies
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Only generate 0x400 (front left steering angle) at 333Hz
        interval = 0.003  # 333Hz
        
        if int(elapsed / interval) > int((elapsed - timeout) / interval):
            # Time to generate 0x400 message
            data = self._generate_fl_steering(elapsed)
            self.message_count += 1
            
            # Create a mock CAN message
            class MockCANMessage:
                def __init__(self, arbitration_id, data, timestamp):
                    self.arbitration_id = arbitration_id
                    self.data = data
                    self.timestamp = timestamp
            
            return MockCANMessage(0x400, data, current_time)
        
        return None
    
    def _generate_fl_steering(self, elapsed):
        """Generate front left steering angle"""
        angle = 8 * math.sin(elapsed * 0.5 + 0.1)  # Oscillating steering angle
        value = int(angle / 0.001)  # Convert to raw value (0.001 scaling factor)
        return value.to_bytes(2, 'little', signed=True) + b'\x00' * 6
    
    def shutdown(self):
        """Clean shutdown"""
        print(f"CAN Generator shutdown. Generated {self.message_count} messages.") 