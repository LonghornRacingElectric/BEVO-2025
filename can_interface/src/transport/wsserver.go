package transport

import (
	"encoding/json"
	"log"
	"net/http"
	"time"

	"github.com/gorilla/websocket"
)

// Define a global upgrader.
var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin:     func(r *http.Request) bool { return true },
}

// Define a handler function for WebSocket connections.
func handleConnection(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println(err)
		return
	}
	defer conn.Close()

	log.Println("Client connected")

	data := map[string]interface{}{
		"id":         0x113,
		"time_stamp": time.Now().UnixNano(),
		"data":       []float64{40.0},
	}

	jsonData, err := json.Marshal(data)
	if err != nil {
		log.Println("Error marshalling JSON:", err)
		return
	}

	for {
		err = conn.WriteMessage(websocket.TextMessage, jsonData)
		if err != nil {
			log.Println(err)
			return
		}
		log.Printf("Sent message: %s", jsonData)
		// time.Sleep(100 * time.Millisecond)
	}
}

func StartWebSocketServer(addr string) error {
	http.HandleFunc("/", handleConnection) // Use the local handleConnection
	err := http.ListenAndServe(addr, nil)
	if err != nil {
		log.Println("ListenAndServe Error:", err) // Log the error.
		return err
	}
	return nil
}
