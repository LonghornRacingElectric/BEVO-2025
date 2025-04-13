package comm

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
)

type ResponseData struct {
	LastPacket string `json:"last_packet"`
}

func handshake() {
	resp, err := http.Get("https://lhrelectric.org/webtool/handshake/")
	if err != nil {
		log.Fatalf("Error making HTTP request: %v", err)
	}
	defer resp.Body.Close() // Ensure the response body is closed after we're done with it

	// Read the response body.
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatalf("Error reading response body: %v", err)
	}

	// Unmarshal the JSON response into a struct.
	var responseData ResponseData

	err = json.Unmarshal(body, &responseData)
	if err != nil {
		log.Fatalf("Error unmarshalling JSON: %v", err)
	}

	// Print the "last_packet" value.
	fmt.Println("Last Packet:", responseData.LastPacket)
}
