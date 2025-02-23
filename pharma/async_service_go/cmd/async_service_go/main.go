package main

import (
    "log"
    "async_service_go/internal/api"
)

func main() {
    log.Println("Application start!")
    api.StartServer()
    log.Println("Application terminated!")
}