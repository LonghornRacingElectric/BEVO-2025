package transport

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
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
func handleConnection(w http.ResponseWriter, r *http.Request, dataMutex *sync.RWMutex, data *map[string]interface{}) { // Receive mutex and pointer
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println(err)
		return
	}
	defer conn.Close()

	log.Println("Client connected")

	for {
		// Read the data safely using the mutex.
		dataMutex.RLock()                    // Acquire read lock
		jsonData, err := json.Marshal(*data) // Dereference the pointer
		dataMutex.RUnlock()                  // Release read lock
		if err != nil {
			log.Println("Error marshalling JSON:", err)
			return
		}

		err = conn.WriteMessage(websocket.TextMessage, jsonData)
		if err != nil {
			log.Println(err)
			return
		}
		// log.Printf("[WEBSOCKET SERVER] Sent message: %s", jsonData)
		time.Sleep(25 * time.Millisecond)
	}
}

func StartWebSocketServer(addr string, dataMutex *sync.RWMutex, data *map[string]interface{}) error { // Add mutex and pointer
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		handleConnection(w, r, dataMutex, data) // Pass them to handleConnection
	})
	err := http.ListenAndServe(addr, nil)
	if err != nil {
		log.Println("ListenAndServe Error:", err)
		return err
	}
	return nil
}
