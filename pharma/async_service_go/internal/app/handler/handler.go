package handler

import (
	"bytes"
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
	"async_service_go/internal/app/repository"
)

type Handler struct {
	Repository *repository.Repository
}

func NewHandler(r *repository.Repository) *Handler {
	return &Handler{Repository: r}
}

func (h *Handler) GeneratePriceHandler(c *gin.Context) {
	drugID := c.PostForm("drug_id")
	if drugID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "drug_id is required"})
		return
	}

	// Асинхронная обработка в горутине
	go func(id string) {
		// Получаем канал с результатом
		resultChan, err := h.Repository.GeneratePrice(id)
		if err != nil {
			logrus.Errorf("Failed to generate price for drug %s: %v", id, err)
			return
		}

		// Получаем значение из канала
		result := <-resultChan

		// Логируем сгенерированное время задержки
		logrus.Infof("Generated delay for drug %s: %.2f seconds", id, result.Delay)

		// Отправка результата в Django через HTTP PUT
		url := fmt.Sprintf("http://localhost:8000/drugs/%s/price/", id)
		payload := []byte(fmt.Sprintf(`{"price": %.2f}`, result.Price))
		req, err := http.NewRequest("PUT", url, bytes.NewBuffer(payload))
		if err != nil {
			logrus.Errorf("Failed to create PUT request: %v", err)
			return
		}
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Authorization", "Token 12345678")

		client := &http.Client{}
		resp, err := client.Do(req)
		if err != nil {
			logrus.Errorf("Failed to send PUT request: %v", err)
			return
		}
		defer resp.Body.Close()

		if resp.StatusCode == http.StatusOK {
			logrus.Infof("Price %.2f sent successfully for drug %s", result.Price, id)
		} else {
			logrus.Errorf("Failed to update price, status: %d", resp.StatusCode)
		}
	}(drugID)

	c.JSON(http.StatusOK, gin.H{"message": "Price generation started for drug " + drugID})
}