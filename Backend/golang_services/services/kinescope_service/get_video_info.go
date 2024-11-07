package main


import (
	"encoding/json"
	"fmt"
	"net/http"
)

// URL для Kinescope API
const KINESCOPE_API_URL = "https://api.kinescope.io/v1/videos/"

func getVideoInfo(videoID, token string) error {
	url := KINESCOPE_API_URL + videoID
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return fmt.Errorf("ошибка при создании запроса: %v", err)
	}
	req.Header.Set("Authorization", "Bearer "+token)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("ошибка при выполнении запроса: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("ошибка: статус ответа %d", resp.StatusCode)
	}

	var videoInfo map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&videoInfo); err != nil {
		return fmt.Errorf("ошибка при декодировании ответа: %v", err)
	}

	if playLink, ok := videoInfo["data"].(map[string]interface{})["play_link"].(string); ok {
		fmt.Printf("Play link: %s\n", playLink)
	} else {
		fmt.Println("play_link не найден в ответе.")
	}

	return nil
}
