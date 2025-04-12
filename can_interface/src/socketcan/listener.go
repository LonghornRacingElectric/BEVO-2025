package socketcan

import (
	"fmt"
	"log"
	"runtime"
	"time"
	"math/rand"

	"github.com/brutella/can"
)

type CANFrame struct {
	ID     uint32
	Length uint8
	Data   [8]byte
}

type Listener interface {
	Listen(handler func(CANFrame)) error
}

type LinuxListener struct {
	Interface string
}

type SimListener struct{}

func (l *LinuxListener) Listen(handler func(CANFrame)) error {
	// Create a CAN bus using the interface name (e.g., "can0")
	bus, err := can.NewBusForInterfaceWithName(l.Interface)
	if err != nil {
		return fmt.Errorf("failed to create CAN bus: %w", err)
	}

	// Set up channel to receive CAN frames
	c := make(chan can.Frame)
	bus.SubscribeFunc(func(f can.Frame) {
		c <- f
	})

	if err := bus.ConnectAndPublish(); err != nil {
		return fmt.Errorf("failed to connect CAN bus: %w", err)
	}
	defer bus.Disconnect()

	log.Printf("Listening on CAN interface %s...\n", l.Interface)

	for frame := range c {
		var data [8]byte
		copy(data[:], frame.Data[:])
		handler(CANFrame{
			ID:     frame.ID,
			Length: frame.Length,
			Data:   data,
		})
	}
	return nil
}

func (s *SimListener) Listen(handler func(CANFrame)) error {
	log.Println("Simulating CAN bus with random data...")

	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()

	for range ticker.C {
		frame := CANFrame{
			ID:     uint32(0x100 + rand.Intn(0x700)), // IDs from 0x100 to 0x7FF
			Length: uint8(rand.Intn(9)),              // 0 to 8 bytes
		}

		for i := 0; i < int(frame.Length); i++ {
			frame.Data[i] = byte(rand.Intn(256)) // Random byte [0-255]
		}

		handler(frame)
	}

	return nil
}
func NewListener(interfaceName string) Listener {
	if runtime.GOOS == "linux" {
		return &LinuxListener{Interface: interfaceName}
	}
	return &SimListener{}
}