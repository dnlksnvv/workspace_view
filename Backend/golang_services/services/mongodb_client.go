// mongo_client.go
package main

//mongodb_client.go

import (
	"context"
	"fmt"
	"log"
	"strings"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

var client *mongo.Client

// Подключение к MongoDB
func connectToMongoDB() *mongo.Client {
	clientOptions := options.Client().ApplyURI("mongodb://localhost:27017")
	client, err := mongo.Connect(context.TODO(), clientOptions)
	if err != nil {
		log.Fatalf("Ошибка подключения к MongoDB: %v", err)
	}

	// Проверка соединения
	err = client.Ping(context.TODO(), nil)
	if err != nil {
		log.Fatalf("Ошибка пинга MongoDB: %v", err)
	}

	log.Println("Успешное подключение к MongoDB")
	return client
}

// Функция для обновления информации о записи в MongoDB
func updateRecordingInfoInMongo(conferenceUUID, recordingID, videoID string) error {
	if client == nil {
		client = connectToMongoDB()
	}

	database := client.Database("mds_workspace")
	conferenceCollection := database.Collection("conference_videos")

	originalRecordingID := strings.Replace(recordingID, "_trimmed", "", 1)

	filter := bson.M{"meetings." + conferenceUUID + ".recordings.recording_id": originalRecordingID}
	update := bson.M{
		"$set": bson.M{
			"meetings." + conferenceUUID + ".recordings.$[elem].kinescope_general_code": videoID,
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
		return fmt.Errorf("Ошибка обновления документа в MongoDB: %v", err)
	}

	log.Printf("Обновлена информация о записи в MongoDB для recording_id: %s", originalRecordingID)
	return nil
}

// Функция получения `topic` из MongoDB
func getTopicFromMongo(conferenceUUID string) (string, error) {
	if client == nil {
		client = connectToMongoDB()
	}

	database := client.Database("mds_workspace")
	conferenceCollection := database.Collection("conference_videos")

	var conferenceData bson.M
	err := conferenceCollection.FindOne(context.TODO(), bson.M{"meetings." + conferenceUUID: bson.M{"$exists": true}}).Decode(&conferenceData)
	if err != nil {
		return "", fmt.Errorf("Не удалось найти данные конференции: %v", err)
	}

	meetings := conferenceData["meetings"].(bson.M)
	meeting := meetings[conferenceUUID].(bson.M)
	topic := meeting["topic"].(string)

	return topic, nil
}
