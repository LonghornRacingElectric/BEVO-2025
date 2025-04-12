// package main

// import (
// 	// "fmt"

// 	// "src/socketcan"
// 	"src/transport"
// 	"log"
// )

// func main() {
// 	go transport.StartServer(":8001")

// 	log.Println("WebSocket broadcaster example started.")

// 	// listener := socketcan.NewListener("can0")

// 	// err := listener.Listen(func(f socketcan.CANFrame) {
// 	// 	ws.Send(map[string]any{
// 	// 		"id":     fmt.Sprintf("0x%03X", f.ID),
// 	// 		"length": f.Length,
// 	// 		"data":   f.Data[:f.Length],
// 	// 	})
// 	// })

// 	// if err != nil {
// 	// 	panic(err)
// 	// }
// }

// package main

// import (
// 	"encoding/json"
// 	"log"
// 	"net/http"
// 	"time"

// 	"github.com/gorilla/websocket"
// )

// // Define a global upgrader.  This handles upgrading the HTTP connection to a WebSocket.
// var upgrader = websocket.Upgrader{
// 	ReadBufferSize:  1024,
// 	WriteBufferSize: 1024,
// 	CheckOrigin:     func(r *http.Request) bool { return true },
// }

// // New connection handler
// func handleConnection(w http.ResponseWriter, r *http.Request) {
// 	// HTTP stuff to upgrade to websocket
// 	conn, err := upgrader.Upgrade(w, r, nil)
// 	if err != nil {
// 		log.Println(err)
// 		return
// 	}
// 	defer conn.Close()

// 	log.Println("Client connected")

// 	data := map[string]interface{}{
// 		"id":         224,
// 		"time_stamp": time.Now().UnixNano(),
// 		"data":       []float64{40.0},
// 	}

// 	//data to JSON
// 	jsonData, err := json.Marshal(data)
// 	if err != nil {
// 		log.Println("Error marshalling JSON:", err)
// 		return
// 	}

// 	// Main loop for sending messages.  This loop will continue
// 	for {
// 		err = conn.WriteMessage(websocket.TextMessage, jsonData)
// 		if err != nil {
// 			log.Println(err)
// 			return
// 		}
// 		log.Printf("Sent message: %s", jsonData)
// 	}
// }

// func main() {
// 	http.HandleFunc("/", handleConnection)

// 	log.Println("Starting WebSocket server on :8001")
// 	err := http.ListenAndServe(":8001", nil)
// 	if err != nil {
// 		log.Fatal("ListenAndServe: ", err)
// 	}
// }

package main

import (
	"log"
	// "net/http"
	"time"

	"src/transport"
)

func main() {
	// Start the WebSocket server in a goroutine.
	go func() {
		log.Println("Starting WebSocket server on :8001")
		if err := transport.StartWebSocketServer(":8001"); err != nil {
			log.Fatalf("Failed to start WebSocket server: %v", err)
		}
	}()

	log.Println("Main application running...")
	for {
		log.Println("Doing some main application work...")
		time.Sleep(5 * time.Second) // Simulate work with a 5-second sleep
	}

}
