package model

import (
	"encoding/binary"
	"math"
	"time"
)

// CANMessage represents a single CAN frame.
type CANMessage struct {
	ID        uint32  `json:"id"`
	Timestamp float64 `json:"timestamp"`
	Data      []byte  `json:"data"`
}

const MaxCANDataBytes = 8

// Helper to create a CAN message similar to the Python example (for simulation/testing)
// Note: This assumes the value is scaled *before* being put into bytes.
func MakeCANMsg(arbitrationID uint32, value float64) CANMessage {
	scaled := int64(math.Round(value))
	data := make([]byte, 4)                             // Assuming 4 bytes based on example
	binary.LittleEndian.PutUint32(data, uint32(scaled)) // Assuming unsigned
	return CANMessage{
		ID:        arbitrationID,
		Timestamp: float64(time.Now().UnixNano()) / 1e9, // High-resolution timestamp
		Data:      data,
	}
}
