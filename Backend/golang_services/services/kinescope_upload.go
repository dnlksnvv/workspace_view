// kinescope_upload.go
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strings"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo/options"
)

const (
	KINESCOPE_API_TOKEN = "-*************-*************-*************"

	KINESCOPE_UPLOAD_INIT_URL = "https://uploader.kinescope.io/v2/init"
	KINESCOPE_API_URL         = "https://api.kinescope.io/v1/videos"
)


type Result struct {
	Data struct {
		ID       string `json:"id"`
		Endpoint string `json:"endpoint"`
	} `json:"data"`
}

type VideoInfo struct {
	ID    string `json:"id"`
	Title string `json:"title"`
}

func uploadToKinescope(fileData []byte, filename string, folderID string) (string, error) {
	data, err := json.Marshal(map[string]interface{}{
		"client_ip": "8.8.8.8",
		"parent_id": folderID,
		"type":      "video",
		"title":     filename,
		"filename":  filename,
		"filesize":  len(fileData),
	})
	if err != nil {
		return "", fmt.Errorf("Ошибка сериализации данных: %v", err)
	}

	req, err := http.NewRequest(http.MethodPost, KINESCOPE_UPLOAD_INIT_URL, bytes.NewReader(data))
	if err != nil {
		return "", fmt.Errorf("Ошибка создания запроса: %v", err)
	}
	req.Header.Set("Authorization", "Bearer "+KINESCOPE_API_TOKEN)
	req.Header.Set("Content-Type", "application/json")

	client := http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("Ошибка выполнения запроса: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		body, _ := ioutil.ReadAll(resp.Body)
		return "", fmt.Errorf("Kinescope API ответил со статусом: %d, ответ: %s", resp.StatusCode, body)
	}

	var kinescopeResult Result
	if err := json.NewDecoder(resp.Body).Decode(&kinescopeResult); err != nil {
		return "", fmt.Errorf("Ошибка декодирования ответа от Kinescope: %v", err)
	}

	fmt.Printf("Ответ от Kinescope API: ID = %s, Endpoint = %s\n", kinescopeResult.Data.ID, kinescopeResult.Data.Endpoint)

	offset := int64(0)
	for offset < int64(len(fileData)) {
		chunkSize := int64(5 * 1024 * 1024)
		if offset+chunkSize > int64(len(fileData)) {
			chunkSize = int64(len(fileData)) - offset
		}

		chunk := fileData[offset : offset+chunkSize]
		uploadReq, err := http.NewRequest(http.MethodPatch, kinescopeResult.Data.Endpoint, bytes.NewReader(chunk))
		if err != nil {
			return "", fmt.Errorf("Ошибка создания запроса загрузки: %v", err)
		}
		uploadReq.Header.Set("Content-Type", "application/octet-stream")
		uploadReq.Header.Set("Tus-Resumable", "1.0.0")
		uploadReq.Header.Set("Upload-Offset", fmt.Sprintf("%d", offset))

		uploadResp, err := client.Do(uploadReq)
		if err != nil {
			return "", fmt.Errorf("Ошибка загрузки видео на Kinescope: %v", err)
		}
		defer uploadResp.Body.Close()

		if uploadResp.StatusCode != http.StatusNoContent {
			body, _ := ioutil.ReadAll(uploadResp.Body)
			return "", fmt.Errorf("Ошибка при загрузке видео на Kinescope, статус: %d, тело ответа: %s", uploadResp.StatusCode, body)
		}

		offset += chunkSize
		log.Printf("Успешно загружен блок данных: %d байт", chunkSize)
	}

	log.Println("Видео успешно загружено на Kinescope!")
	return kinescopeResult.Data.ID, nil
}

func findAndUploadRecording(recordingID string, folderID string, conferenceUUID string) error {
	if client == nil {
		client = connectToMongoDB()
	}

	err := updateStatusInMongo(conferenceUUID, recordingID, "uploading", folderID)
	if err != nil {
		return fmt.Errorf("Ошибка установки статуса и folder_id в MongoDB: %v", err)
	}

	topic, err := getTopicFromMongo(conferenceUUID)
	if err != nil {
		return fmt.Errorf("Не удалось получить topic из MongoDB: %v", err)
	}

	log.Printf("Получен topic: %s", topic)

	fsFilesCollection := client.Database("zoom_files").Collection("shared_screen_with_speaker_view.files")

	var fileInfo bson.M
	err = fsFilesCollection.FindOne(context.TODO(), bson.M{"recording_id": recordingID}).Decode(&fileInfo)
	if err != nil {
		return fmt.Errorf("Файл не найден: %v", err)
	}

	filePath, ok := fileInfo["file_path"].(string)
	if !ok {
		return fmt.Errorf("Путь к файлу не найден или имеет неверный формат")
	}

	log.Printf("Файл найден: %s", filePath)

	fileData, err := os.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("Ошибка чтения файла из файловой системы: %v", err)
	}

	videoID, err := uploadToKinescope(fileData, topic, folderID)
	if err != nil {
		return fmt.Errorf("Ошибка при загрузке на Kinescope: %v", err)
	}

	log.Printf("Файл успешно загружен на Kinescope. Видео ID: %s", videoID)

	err = updateRecordingInfoInMongo(conferenceUUID, recordingID, videoID)
	if err != nil {
		return fmt.Errorf("Ошибка обновления информации о записи в MongoDB: %v", err)
	}

	return nil
}

func updateStatusInMongo(conferenceUUID, recordingID, status, folderID string) error {
	if client == nil {
		client = connectToMongoDB()
	}

	database := client.Database("mds_workspace")
	conferenceCollection := database.Collection("conference_videos")

	originalRecordingID := strings.Replace(recordingID, "_trimmed", "", 1)

	filter := bson.M{"meetings." + conferenceUUID + ".recordings.recording_id": originalRecordingID}
	update := bson.M{
		"$set": bson.M{
			"meetings." + conferenceUUID + ".recordings.$[elem].kinescope_status":    status,
			"meetings." + conferenceUUID + ".recordings.$[elem].kinescope_folder_id": folderID,
		},
	}
	arrayFilters := options.ArrayFilters{
		Filters: []interface{}{
			bson.M{"elem.recording_id": originalRecordingID},
		},
	}
	opts := options.UpdateOptions{
		ArrayFilters: &arrayFilters,
	}

	_, err := conferenceCollection.UpdateOne(context.TODO(), filter, update, &opts)
	if err != nil {
		return fmt.Errorf("Ошибка обновления статуса и folder_id в MongoDB: %v", err)
	}

	log.Printf("Обновлен статус в MongoDB для recording_id: %s, status: %s, folder_id: %s", originalRecordingID, status, folderID)
	return nil
}
