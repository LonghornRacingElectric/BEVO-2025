package main

import (
	"fmt"
	"log"
	"runtime"
	"sync"
	"time"

	"src/socketcan"
	"src/transport"
)

// mutex to keep dash data safe between threads

var dashMutex sync.RWMutex
var dashData map[string]interface{}

func main() {
	dashData := map[string]interface{}{
		"id":         275,
		"time_stamp": time.Now().UnixNano(),
		"data":       []float64{40.0},
	}

	// Start the WebSocket server in a goroutine.
	go func() {
		log.Println("Starting WebSocket server on :8001")
		if err := transport.StartWebSocketServer(":8001", &dashMutex, &dashData); err != nil {
			log.Fatalf("Failed to start WebSocket server: %v", err)
		}
	}()

	// Start the CAN interface in a goroutine.
	go func() {
		listener := socketcan.NewListener("can0")

		err := listener.Listen(func(f socketcan.CANFrame) {
			dashMutex.Lock()
			dashData["time_stamp"] = time.Now().UnixNano()
			dashData["data"] = f.Data

			dashMutex.Unlock()
		})
		if err != nil {
			panic(err)
		}
	}()

	log.Println("Main application running...")
	for {
		buf := make([]byte, 1024)
		runtime.Stack(buf, true)
		fmt.Println("Goroutine stack traces:")
		fmt.Println(string(buf))
	}

}
