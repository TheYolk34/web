package api

import (
    "github.com/gin-gonic/gin"
    "github.com/sirupsen/logrus"
    "log"
    "async_service_go/internal/app/handler"
    "async_service_go/internal/app/repository"
)

func StartServer() {
    log.Println("Server start up")

    repo, err := repository.NewRepository(10)
    if err != nil {
        logrus.Errorf("Failed to initialize repository: %v", err)
        return
    }

    h := handler.NewHandler(repo)

    r := gin.Default()
    r.POST("/generate-price", h.GeneratePriceHandler)

    if err := r.Run(":8081"); err != nil {
        logrus.Errorf("Failed to run server: %v", err)
    }
    log.Println("Server down")
}