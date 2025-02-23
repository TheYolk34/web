package repository

import (
	"fmt"
	"math"
	"math/rand"
	"time"
)

// Repository представляет собой репозиторий для генерации цен с задержкой.
type Repository struct {
	MeanDelay float64 // Средняя задержка в секундах
	rng       *rand.Rand // Потокобезопасный генератор случайных чисел
}

// NewRepository создаёт новый экземпляр Repository с заданной средней задержкой.
func NewRepository(meanDelay float64) (*Repository, error) {
	if meanDelay <= 0 {
		return nil, fmt.Errorf("meanDelay must be positive")
	}
	// Инициализируем генератор с уникальным сидированием
	rng := rand.New(rand.NewSource(time.Now().UnixNano()))
	return &Repository{
		MeanDelay: meanDelay,
		rng:       rng,
	}, nil
}

// PriceResult содержит результат генерации цены.
type PriceResult struct {
	DrugID string  // Идентификатор препарата
	Price  float64 // Сгенерированная цена
	Delay  float64 // Задержка в секундах
}

// GeneratePrice генерирует цену с экспоненциальной задержкой, возвращая канал с результатом.
func (r *Repository) GeneratePrice(drugID string) (<-chan PriceResult, error) {
	resultChan := make(chan PriceResult, 1)

	// Запускаем асинхронную обработку
	go func() {
		defer close(resultChan)

		// Вычисляем интенсивность λ = 1 / средняя задержка
		lambda := 1.0 / r.MeanDelay

		// Генерируем экспоненциальную задержку: T = -ln(U) / λ
		u := r.rng.Float64()
		if u == 0 { // Маловероятно, но для безопасности
			u = 1e-10
		}
		delay := -math.Log(u) / lambda

		// Асинхронное ожидание через таймер
		<-time.After(time.Duration(delay * float64(time.Second)))

		// Генерируем цену в диапазоне [100, 1000)
		price := 100.0 + r.rng.Float64()*900.0

		// Отправляем результат в канал
		resultChan <- PriceResult{
			DrugID: drugID,
			Price:  price,
			Delay:  delay,
		}
	}()

	return resultChan, nil
}