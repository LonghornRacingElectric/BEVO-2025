import can
import platform
from interfaces.simulator import CANGenerator


class CANInterface:
    """Manages CAN bus interface with platform detection"""
    
    def __init__(self):
        self.is_linux = platform.system() == "Linux"
        self.bus = None
        
    def initialize(self):
        """Initialize the appropriate CAN interface"""
        if self.is_linux:
            try:
                self.bus = can.interface.Bus(bustype="socketcan", channel="can0", bitrate=1000000)
                print("Using real CAN bus interface (Linux)")
                return True
            except Exception as e:
                print(f"Warning: Could not initialize real CAN bus: {e}")
                print("Falling back to CAN generator...")
                self.bus = CANGenerator()
                return False
        else:
            self.bus = CANGenerator()
            print(f"Using CAN generator (non-Linux platform: {platform.system()})")
            return False
    
    def recv(self, timeout=0.01):
        """Receive CAN message with timeout"""
        if self.bus:
            return self.bus.recv(timeout)
        return None
    
    def shutdown(self):
        """Clean shutdown of CAN interface"""
        if self.bus:
            try:
                self.bus.shutdown()
                print("CAN interface shutdown complete")
            except Exception as e:
                print(f"Error shutting down CAN interface: {e}")
    
    def is_real_bus(self):
        """Check if using real CAN bus vs generator"""
        return self.is_linux and not isinstance(self.bus, CANGenerator) 