# Telemetry Data System

A modular system for processing CAN bus data with MQTT publishing and CSV logging. Supports both real CAN hardware and simulated data for development/testing.

## 📁 Project Structure

```
telemd/
├── main.py                 # 🚀 Main entry point
├── __init__.py            # 📦 Package initialization  
├── README.md              # 📖 Documentation
│
├── core/                  # 🧠 Core system components
│   ├── __init__.py
│   ├── backend.py         # Main orchestrator (clean & simple)
│   └── field_mappings.py  # CAN field mappings
│
├── interfaces/            # 🔌 Hardware interfaces
│   ├── __init__.py
│   ├── interface.py       # Platform-aware CAN interface
│   └── simulator.py       # CAN data simulation
│
├── logging/               # 📊 Data logging
│   ├── __init__.py
│   └── logger.py          # CSV logging functionality
│
├── networking/            # 🌐 Network communication
│   ├── __init__.py
│   └── client.py          # MQTT connection management
│
├── protobuf/              # 📋 Message definitions
│   ├── __init__.py
│   ├── template.proto     # Protobuf schema definition
│   ├── generated.py       # Generated protobuf code
│   └── interface.py       # Message publishing interface
│
└── tests/                 # 🧪 Test files
    ├── __init__.py
    ├── interface_test.py  # CAN interface tests
    ├── test.py            # General tests
    └── mock_backend.py    # Mock implementation
```

## 🚀 Quick Start

### Run the System
```bash
# From the telemd directory
python main.py

# Or directly
python core/backend.py
```

### Platform Support
- **Linux**: Uses real CAN bus hardware (socketcan)
- **macOS/Windows**: Uses simulated CAN data generator
- **Automatic fallback**: Falls back to generator if real CAN fails

## 🔧 Components

### Core (`core/`)
- **`backend.py`**: Main orchestrator that coordinates all components
- **`field_mappings.py`**: Defines CAN ID to protobuf field mappings

### Interfaces (`interfaces/`)
- **`interface.py`**: Platform detection and CAN bus initialization
- **`simulator.py`**: Realistic CAN data simulation for development

### Logging (`logging/`)
- **`logger.py`**: CSV file logging with configurable intervals

### Networking (`networking/`)
- **`client.py`**: MQTT broker connection and message publishing

### Protobuf (`protobuf/`)
- **`template.proto`**: Protobuf schema definition for telemetry data
- **`generated.py`**: Generated protobuf code from schema
- **`interface.py`**: Message publishing interface and serialization

### Tests (`tests/`)
- **`interface_test.py`**: CAN interface testing utilities
- **`test.py`**: General system tests
- **`mock_backend.py`**: Mock implementation for testing

## 📊 Features

- **Real-time CAN processing**: Processes CAN messages at full speed
- **MQTT publishing**: Publishes telemetry data to MQTT broker
- **CSV logging**: Saves latest values to CSV file every 2 seconds
- **WebSocket server**: Provides real-time data to web clients
- **Cross-platform**: Works on Linux, macOS, and Windows
- **Error handling**: Graceful degradation when components fail

## 🔌 Configuration

### MQTT Settings
- Broker: `192.168.1.109:1883`
- Topic: `data`
- Automatic reconnection on failure

### CSV Logging
- File: `can_telemetry_latest.csv`
- Interval: 2 seconds
- Format: Timestamp + all CAN field values

### WebSocket
- Port: `8001`
- Real-time data streaming to connected clients

## 🛠️ Development

### Adding New CAN Fields
1. Add mapping in `core/field_mappings.py`
2. Update protobuf schema if needed
3. Test with generator data

### Modifying Data Generation
Edit `interfaces/simulator.py` to change simulated data patterns and frequencies.

### Custom Logging
Extend `logging/logger.py` or create new logging modules.

## 📝 Dependencies

- `python-can`: CAN bus interface
- `websockets`: WebSocket server
- `paho-mqtt`: MQTT client
- `requests`: HTTP requests for handshake
- `protobuf_i`: Custom protobuf interface

## 🤝 Contributing

1. Follow the modular structure
2. Add appropriate `__init__.py` files
3. Update this README for new components
4. Test on both Linux and non-Linux platforms 