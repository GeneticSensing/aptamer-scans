#!/usr/bin/env python3
import serial
import time
import os
from typing import Optional, Tuple, List

class TeensyController:
    """Handles communication with Teensy via USB serial."""
    
    def __init__(self, port: str = None, baudrate: int = 115200):
        """Initialize controller with optional port and baudrate."""
        self.ser = None          # Active serial connection
        self.port = port or self._auto_detect_port()  # Auto-detect if no port specified
        self.baudrate = baudrate  # Default matches Teensy code
        
    def _auto_detect_port(self) -> Optional[str]:
        """Attempt to find Teensy's USB serial port automatically.
        Returns:
            str: Path to port (e.g., '/dev/ttyACM0') or None if not found
        """
        common_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0']
        for port in common_ports:
            if os.path.exists(port):
                return port
        return None

    def connect(self) -> bool:
        """Establish serial connection to Teensy.
        Returns:
            bool: True if connection succeeded
        """
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            time.sleep(2)  # Allow Teensy to initialize
            self.ser.reset_input_buffer()  # Clear any residual data
            print("Connection sucessful")
            return True
        except Exception as e:
            print(f"Connection failed: {str(e)}")
            return False

    def send_message(self, message: str) -> bool:
        """Send raw string message to Teensy.
        Args:
            message: Text to send (without newline - added automatically)
        Returns:
            bool: True if send succeeded
        """
        if not self.ser or not self.ser.is_open:
            return False
            
        try:
            # Append newline and encode to bytes
            self.ser.write(f"{message}\n".encode())
            return True
        except Exception as e:
            print(f"Send failed: {str(e)}")
            return False

    def receive_message(self, timeout: float = 1.0) -> Optional[str]:
        """Wait for response from Teensy.
        Args:
            timeout: Max seconds to wait (default: 1.0)
        Returns:
            str: Received message or None if timeout/error
        """
        if not self.ser or not self.ser.is_open:
            return None
            
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.ser.in_waiting > 0:
                    # Read and clean up response
                    return self.ser.readline().decode().strip()
                time.sleep(0.01)  # Prevent CPU overuse
            return None  # Timeout reached
        except Exception as e:
            print(f"Receive failed: {str(e)}")
            return None

    def send_command(self, chip: int, we: int) -> Tuple[bool, str]:
        """Send formatted electrode switch command.
        Args:
            chip: Chip number (1-16)
            we: Working electrode number (1-4)
        Returns:
            tuple: (success, message) where:
                success: True if command succeeded
                message: Response from Teensy or error description
        """
        # Attempt to send command
        if not self.send_message(f"{chip} {we}"):
            return False, "Send failed"
            
        # Wait for acknowledgment
        response = self.receive_message()
        if not response:
            return False, "No response from Teensy"
            
        # Check for error indicators
        if "ERROR" in response:
            return False, response
        return True, response

    def disconnect(self):
        """Safely close serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()


# -------------------------------------------------------------------
# Test Sequence (Validates all major functionality)
# -------------------------------------------------------------------
if __name__ == "__main__":
    print("Starting Teensy Communication Test...")
    
    # Initialize controller
    controller = TeensyController()
    if not controller.connect():
        print("❌ Failed to connect to Teensy")
        exit(1)
        
    print("✅ Connected to Teensy")
    print("Running test sequence...\n")
    
    # Test cases cover valid/invalid inputs
    test_commands = [
        (5, 2),    # Valid command
        (16, 4),   # Valid command (boundary case)
        (0, 1),    # Invalid chip (too low)
        (5, 5),    # Invalid WE (too high)
        ("abc",),  # Invalid format (non-numeric)
        (3, 1)     # Valid command
    ]
    
    # Execute each test case
    for cmd in test_commands:
        if len(cmd) == 2:  # Normal electrode command
            chip, we = cmd
            print(f"Sent: {chip} {we}")
            success, response = controller.send_command(chip, we)
        else:  # Format test (invalid input)
            invalid_cmd = cmd[0]
            print(f"Sent: {invalid_cmd} (invalid format test)")
            controller.send_message(invalid_cmd)
            response = controller.receive_message()
            success = False if "ERROR" in response else True
            
        # Display results
        print(f"Received: {response}")
        print(f"Status: {'✅' if success else '❌'}\n")
        time.sleep(0.5)  # Brief pause between commands
    
    # Clean up
    controller.disconnect()
    print("Test completed.")
