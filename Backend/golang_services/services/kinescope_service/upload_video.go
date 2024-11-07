package main


import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"
	"sync"
)

const (
	KINESCOPE_API_TOKEN = "-*************-*************-*************"
	KINESCOPE_UPLOAD_INIT_URL = "https://uploader.kinescope.io/v2/init"
)

type Result struct {
	Data struct {
		ID       string `json:"id"`
		Endpoint string `json:"endpoint"`
	} `json:"data"`
}

func main() {
	http.HandleFunc("/upload-kinescope-video", func(w http.ResponseWriter, r *http.Request) {
		if origin := r.Header.Get("Origin"); origin != "" {
			var header = w.Header()

			header.Set("Access-Control-Allow-Origin", origin)
			header.Set("Access-Control-Allow-Credentials", "true")
			if r.Method == "OPTIONS" {
				header.Set("Access-Control-Max-Age", "86400")
				header.Add("Access-Control-Allow-Headers", "Origin, Content-Type, Tus-Resumable, Upload-Length, Upload-Metadata")
				header.Add("Access-Control-Allow-Methods", "POST, GET, HEAD, PATCH, DELETE, OPTIONS")
				return
			}

			header.Add("Access-Control-Expose-Headers", "Location")
		}

		meta := ParseMetadataHeader(r.Header.Get("Upload-Metadata"))

		size, err := strconv.ParseUint(r.Header.Get("Upload-Length"), 10, 64)
		if err != nil {
			renderError(w, errors.New("bad header Upload-Length"))
			return
		}

		parentID := meta["parent_id"]
		var wg sync.WaitGroup
		wg.Add(1)
		go func() {
			defer wg.Done()
			uploadVideo(parentID, meta["filename"], size, w, r)
		}()
		wg.Wait()

	})

	log.Fatal(http.ListenAndServe(":8080", nil))
}

func uploadVideo(parentID, filename string, size uint64, w http.ResponseWriter, r *http.Request) {
	data, err := json.Marshal(map[string]interface{}{
		"client_ip": "8.8.8.8",
		"parent_id": parentID,
		"type":      "video",
		"title":     filename,
		"filename":  filename,
		"filesize":  size,
	})
	if err != nil {
		renderError(w, err)
		return
	}

	req, err := http.NewRequest(http.MethodPost, KINESCOPE_UPLOAD_INIT_URL, bytes.NewReader(data))
	if err != nil {
		renderError(w, err)
		return
	}
	req.Header.Set("Authorization", "Bearer "+KINESCOPE_API_TOKEN)
	req.Header.Set("Content-Type", "application/json")

	client := http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		renderError(w, err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		renderError(w, errors.New(fmt.Sprintf("kinescope api response status=%d", resp.StatusCode)))
		return
	}

	fmt.Println("Видео успешно передано в Kinescope!")

	var kinescopeResult Result
	if err := json.NewDecoder(resp.Body).Decode(&kinescopeResult); err != nil {
		renderError(w, err)
		return
	}

	fmt.Printf("Ответ от Kinescope API: ID = %s, Endpoint = %s\n", kinescopeResult.Data.ID, kinescopeResult.Data.Endpoint)

	http.Redirect(w, r, kinescopeResult.Data.Endpoint, http.StatusCreated)
}

func ParseMetadataHeader(header string) map[string]string {
	meta := make(map[string]string)

	for _, element := range strings.Split(header, ",") {
		element := strings.TrimSpace(element)

		parts := strings.Split(element, " ")

		if len(parts) != 2 {
			continue
		}

		value, err := base64.StdEncoding.DecodeString(parts[1])
		if err != nil {
			continue
		}

		meta[parts[0]] = string(value)
	}

	return meta
}

func renderError(w http.ResponseWriter, err error) error {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusBadRequest)
	return json.NewEncoder(w).Encode(map[string]interface{}{
		"error": err.Error(),
	})
}
