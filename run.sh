#!/bin/bash
# filepath: run.sh

# Включаем строгий режим: остановка при любой ошибке
set -e

# Функция для вывода информационных сообщений
log_message() {
    echo "[INFO] $1"
}

# Функция для проверки статуса выполнения команды
verify_status() {
    if [ $? -eq 0 ]; then
        log_message "✔ $1 выполнен успешно"
    else
        log_message "✘ Ошибка при выполнении: $1"
        exit 1
    fi
}

# Функция: сборка всех Docker-образов
build_images() {
    log_message "Сборка Docker-образов..."
    docker compose build
    verify_status "Сборка образов"
}

# Функция: запуск юнит-тестов для бэкенда
run_backend_tests() {
    log_message "Запуск юнит-тестов для бэкенда..."
    docker compose run --rm api pytest tests/unit/ -v
    verify_status "Юнит-тесты бэкенда"
}

# Функция: запуск юнит-тестов для фронтенда
run_frontend_tests() {
    log_message "Запуск юнит-тестов для фронтенда..."
    docker compose run --rm frontend npm test
    verify_status "Юнит-тесты фронтенда"
}

# Функция: запуск интеграционного теста
run_integration_test() {
    log_message "Запуск интеграционного теста..."
    docker compose run --rm api pytest tests/test_integration.py -v
    verify_status "Интеграционный тест"
}

# Функция: выполнение всех тестов
execute_all_tests() {
    run_backend_tests
    run_frontend_tests
    run_integration_test
    log_message "Все тесты завершены."
}

# Функция: запуск всех сервисов в фоновом режиме
start_services() {
    log_message "Запуск всех сервисов приложения..."
    docker compose up -d
    verify_status "Запуск сервисов"
}

# Функция: остановка и удаление всех контейнеров
stop_services() {
    log_message "Остановка всех сервисов..."
    docker compose down
    verify_status "Остановка сервисов"
}

# Функция: выполнение всех шагов (сборка, тесты, запуск)
full() {
    build_images
    execute_all_tests
    start_services
    log_message "Приложение запущено! Используйте './run.sh stop' для остановки."
}

# Функция: отображение справки
show_help() {
    echo "Использование: $0 [команда]"
    echo ""
    echo "Доступные команды:"
    echo "  full              Выполнить сборку, тесты и запуск (по умолчанию)"
    echo "  build             Собрать Docker-образы"
    echo "  test_backend      Запустить юнит-тесты для бэкенда"
    echo "  test_frontend     Запустить юнит-тесты для фронтенда"
    echo "  test_integration  Запустить интеграционный тест"
    echo "  test              Выполнить все тесты (backend + frontend + integration)"
    echo "  start             Запустить сервисы в фоновом режиме"
    echo "  stop              Остановить и удалить контейнеры"
    echo "  help              Показать эту справку"
    echo ""
}

# Основная логика скрипта
case "${1:-full}" in
    "full")
        full
        ;;
    "build")
        build_images
        ;;
    "test_backend")
        run_backend_tests
        ;;
    "test_frontend")
        run_frontend_tests
        ;;
    "test_integration")
        run_integration_test
        ;;
    "test")
        execute_all_tests
        ;;
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        log_message "Неизвестная команда: $1"
        show_help
        exit 1
        ;;
esac
