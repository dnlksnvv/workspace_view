// main.go
package main

//main.go

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/golang-jwt/jwt/v4"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"io/ioutil"
	"log"
	"net/http"
	"strings"
	"time"
)

// Константы для JWT и Kinescope API
const (
	SECRET_KEY     = "-*************-*************-*************-*************-*************-*************"
)

// Структура для хранения информации о папке
type FolderInfo struct {
	FolderID       string `json:"folder_id"`
	ProjectID      string `json:"project_id"`
	ParentID       string `json:"parent_id"`
	RecordingID    string `json:"recording_id"`
	ConferenceUUID string `json:"conference_uuid"`
}

// Middleware для обработки CORS
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")

		if origin != "" {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
			w.Header().Set("Access-Control-Allow-Credentials", "true")
		}

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// Middleware для проверки токена в cookies
func authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Извлечение токена из cookies
		cookie, err := r.Cookie("access_token")
		if err != nil {
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		// Проверка валидности токена
		if !validateToken(cookie.Value) {
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func validateToken(tokenString string) bool {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(SECRET_KEY), nil
	})

	if err != nil {
		log.Printf("Ошибка валидации токена: %v", err)
		return false
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		exp := int64(claims["exp"].(float64))
		if time.Now().Unix() > exp {
			log.Println("Токен истек")
			return false
		}
		return true
	}

	return false
}

func receiveFolderInfo(w http.ResponseWriter, r *http.Request) {
	log.Printf("Получен запрос: %s %s", r.Method, r.URL.Path)

	var folderInfo FolderInfo
	err := json.NewDecoder(r.Body).Decode(&folderInfo)
	if err != nil {
		log.Printf("Ошибка при декодировании данных: %v", err)
		http.Error(w, "Ошибка при декодировании данных", http.StatusBadRequest)
		return
	}

	log.Printf("Получена информация о папке: ID = %s, ProjectID = %s, ParentID = %s, RecordingID = %s, ConferenceUUID = %s",
		folderInfo.FolderID, folderInfo.ProjectID, folderInfo.ParentID, folderInfo.RecordingID, folderInfo.ConferenceUUID)

	err = findAndUploadRecording(folderInfo.RecordingID, folderInfo.FolderID, folderInfo.ConferenceUUID)
	if err != nil {
		log.Printf("Ошибка при загрузке файла: %v", err)
		http.Error(w, "Ошибка при загрузке файла", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, "Информация о папке успешно получена и файл загружен.")
}

// Функция для запроса информации о видео из Kinescope API
func getKinescopeVideoInfo(videoID string) (map[string]interface{}, error) {
	req, err := http.NewRequest("GET", KINESCOPE_API_URL+"/"+videoID, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+KINESCOPE_API_TOKEN)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Kinescope API ответил со статусом: %d", resp.StatusCode)
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var videoInfo map[string]interface{}
	if err := json.Unmarshal(body, &videoInfo); err != nil {
		return nil, err
	}

	return videoInfo, nil
}

func checkVideoStatus(w http.ResponseWriter, r *http.Request) {
	var requestData struct {
		RecordingID    string `json:"recording_id"`
		ConferenceUUID string `json:"conference_uuid"`
	}

	err := json.NewDecoder(r.Body).Decode(&requestData)
	if err != nil {
		http.Error(w, "Ошибка при декодировании данных", http.StatusBadRequest)
		return
	}

	if strings.HasSuffix(requestData.RecordingID, "_trimmed") {
		requestData.RecordingID = strings.TrimSuffix(requestData.RecordingID, "_trimmed")
	}

	clientOptions := options.Client().ApplyURI(MONGODB_URI)
	client, err := mongo.Connect(context.TODO(), clientOptions)
	if err != nil {
		http.Error(w, "Ошибка подключения к MongoDB", http.StatusInternalServerError)
		return
	}
	defer client.Disconnect(context.TODO())

	collection := client.Database("mds_workspace").Collection("conference_videos")

	startTime := time.Now()
	attempts := 0

	for {
		if time.Since(startTime) > MAX_WAIT_TIME || attempts >= MAX_ATTEMPTS {
			http.Error(w, "Превышено время ожидания", http.StatusGatewayTimeout)
			return
		}

		filter := bson.M{"meetings." + requestData.ConferenceUUID + ".recordings.recording_id": requestData.RecordingID}
		var result bson.M
		err = collection.FindOne(context.TODO(), filter).Decode(&result)
		if err != nil {
			http.Error(w, "Видео не найдено", http.StatusNotFound)
			return
		}

		// Извлекаем значение kinescope_general_code
		meetings := result["meetings"].(bson.M)
		meeting := meetings[requestData.ConferenceUUID].(bson.M)
		recordings := meeting["recordings"].(bson.A)

		for _, recording := range recordings {
			rec := recording.(bson.M)
			if rec["recording_id"] == requestData.RecordingID {
				kinescopeCode, ok := rec["kinescope_general_code"].(string)
				if ok && kinescopeCode != "" {

					// Повторяем запрос к Kinescope API до тех пор, пока не появится play_link
					for attempts < MAX_ATTEMPTS {
						videoInfo, err := getKinescopeVideoInfo(kinescopeCode)
						if err != nil {
							http.Error(w, "Ошибка при запросе к Kinescope API", http.StatusInternalServerError)
							return
						}

						// Выводим содержимое ответа в консоль
						log.Printf("Ответ от Kinescope API (попытка %d): %v", attempts+1, videoInfo)

						// Проверяем наличие play_link
						if data, exists := videoInfo["data"].(map[string]interface{}); exists {
							if playLink, ok := data["play_link"].(string); ok && playLink != "" {
								log.Printf("play_link найден: %s", playLink)

								// Извлекаем код из play_link (после последнего '/')
								playCode := playLink[strings.LastIndex(playLink, "/")+1:]

								// Обновляем kinescope_status и kinescope_code в MongoDB
								update := bson.M{
									"$set": bson.M{
										"meetings." + requestData.ConferenceUUID + ".recordings.$[record].kinescope_status": "done",
										"meetings." + requestData.ConferenceUUID + ".recordings.$[record].kinescope_code":   playCode,
									},
								}
								arrayFilter := options.ArrayFilters{
									Filters: []interface{}{
										bson.M{"record.recording_id": requestData.RecordingID},
									},
								}
								updateOptions := options.UpdateOptions{
									ArrayFilters: &arrayFilter,
								}

								_, err := collection.UpdateOne(context.TODO(), filter, update, &updateOptions)
								if err != nil {
									http.Error(w, "Ошибка при обновлении данных в MongoDB", http.StatusInternalServerError)
									return
								}

								response := map[string]string{
									"kinescope_status": "done",
									"kinescope_code":   playCode,
								}
								json.NewEncoder(w).Encode(response)
								return
							}
						}

						log.Println("play_link не найден в ответе, продолжаем проверку...")

						time.Sleep(CHECK_INTERVAL)
						attempts++
					}

					http.Error(w, "Превышено время ожидания Kinescope", http.StatusGatewayTimeout)
					return
				}
			}
		}

		time.Sleep(CHECK_INTERVAL)
		attempts++
	}
}


func clearKinescopeDataInMongo(conferenceUUID, recordingID string) error {
	clientOptions := options.Client().ApplyURI(MONGODB_URI)
	client, err := mongo.Connect(context.TODO(), clientOptions)
	if err != nil {
		return fmt.Errorf("Ошибка подключения к MongoDB: %v", err)
	}
	defer client.Disconnect(context.TODO())

	collection := client.Database("mds_workspace").Collection("conference_videos")

	filter := bson.M{"meetings." + conferenceUUID + ".recordings.recording_id": recordingID}

	update := bson.M{
		"$set": bson.M{
			"meetings." + conferenceUUID + ".recordings.$[elem].kinescope_status":       "",
			"meetings." + conferenceUUID + ".recordings.$[elem].kinescope_code":         "",
			"meetings." + conferenceUUID + ".recordings.$[elem].kinescope_general_code": "",
			"meetings." + conferenceUUID + ".recordings.$[elem].kinescope_folder_id":    "",
		},
	}

	// Опции для обновления записей в массиве
	arrayFilters := options.ArrayFilters{
		Filters: []interface{}{
			bson.M{"elem.recording_id": recordingID},
		},
	}

	// Опции обновления
	updateOptions := options.UpdateOptions{
		ArrayFilters: &arrayFilters,
	}

	// Выполняем обновление
	_, err = collection.UpdateOne(context.TODO(), filter, update, &updateOptions)
	if err != nil {
		return fmt.Errorf("Ошибка при очистке данных в MongoDB: %v", err)
	}

	log.Printf("Данные успешно очищены для RecordingID: %s, ConferenceUUID: %s", recordingID, conferenceUUID)
	return nil
}

func cancelUpload(w http.ResponseWriter, r *http.Request) {
	log.Printf("Получен запрос: %s %s", r.Method, r.URL.Path)

	// Проверка токена авторизации
	cookie, err := r.Cookie("access_token")
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	if !validateToken(cookie.Value) {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Извлекаем данные из тела запроса
	var requestData struct {
		RecordingID    string `json:"recording_id"`
		ConferenceUUID string `json:"conference_uuid"`
	}

	err = json.NewDecoder(r.Body).Decode(&requestData)
	if err != nil {
		log.Printf("Ошибка при декодировании данных: %v", err)
		http.Error(w, "Ошибка при декодировании данных", http.StatusBadRequest)
		return
	}

	log.Printf("Получены данные для отмены загрузки: RecordingID = %s, ConferenceUUID = %s", requestData.RecordingID, requestData.ConferenceUUID)

	err = clearKinescopeDataInMongo(requestData.ConferenceUUID, requestData.RecordingID)
	if err != nil {
		log.Printf("Ошибка при очистке данных в MongoDB: %v", err)
		http.Error(w, "Ошибка при очистке данных в MongoDB", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, "Запрос на отмену загрузки успешно обработан.")
}

func main() {
	http.Handle("/receive-folder-info", authMiddleware(http.HandlerFunc(receiveFolderInfo)))
	http.Handle("/check-video-status", authMiddleware(http.HandlerFunc(checkVideoStatus)))
	http.Handle("/cancel-upload", authMiddleware(http.HandlerFunc(cancelUpload)))

	fmt.Println("Сервер запущен на порту :8001")
	log.Fatal(http.ListenAndServe(":8001", corsMiddleware(http.DefaultServeMux)))
}
