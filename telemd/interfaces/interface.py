import can
import platform
from can.notifier import Notifier
from can.listener import BufferedReader
from interfaces.simulator import CANGenerator


class CANInterface:
    """Manages CAN bus interface with platform detection and background buffering"""

    def __init__(self):
        self.is_linux = platform.system() == "Linux"
        self.bus = None
        self.buffer = None
        self.notifier = None
        
    def initialize(self):
        """Initialize the appropriate CAN interface"""
        if self.is_linux:
            self.bus = can.interface.Bus(
                bustype="socketcan",
                channel="can0",
                bitrate=1000000
            )
            print("Using real CAN bus interface (Linux)")

            # Create a background buffer (VERY important)
            self.buffer = BufferedReader()
            self.notifier = Notifier(self.bus, [self.buffer])

            return True
        else:
            self.bus = CANGenerator()
            print(f"Using CAN generator (non-Linux platform: {platform.system()})")
            return False
    
    def recv(self, timeout=0.01):
        """Return one CAN message from buffered background queue"""
        if self.buffer:
            return self.buffer.get_message(timeout)
        elif self.bus:
            # Fallback for generator
            return self.bus.recv(timeout)
        return None
    
    def shutdown(self):
        """Clean shutdown"""
        if self.notifier:
            self.notifier.stop()
        
        if self.bus:
            try:
                self.bus.shutdown()
                print("CAN interface shutdown complete")
            except Exception as e:
                print(f"Error shutting down CAN interface: {e}")
    
    def is_real_bus(self):
        return self.is_linux and not isinstance(self.bus, CANGenerator)
