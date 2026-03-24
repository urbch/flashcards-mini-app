#!/bin/bash

set -e

log_message() {
    echo "[INFO] $1"
}

prepare_reports_dir() {
    mkdir -p reports/api reports/bot reports/frontend
}

build_images() {
    log_message "Сборка Docker-образов..."
    docker compose build
}

run_api_tests() {
    log_message "Запуск unit-тестов API..."
    docker compose run --rm api pytest tests/unit/ \
        -v \
        --cov=. \
        --cov-report=term-missing \
        --cov-report=html:/app/reports/htmlcov \
        --cov-report=xml:/app/reports/coverage.xml \
        --cov-fail-under=80 \
        --cov-config=/app/.coveragerc \
        --junitxml=/app/reports/junit.xml
}

run_bot_tests() {
    log_message "Запуск unit-тестов бота..."
    docker compose run --rm bot python -m pytest /app/test/test_bot.py \
        -v \
        --cov=. \
        --cov-config=/app/.coveragerc \
        --cov-report=term-missing \
        --cov-report=html:/app/reports/htmlcov \
        --cov-report=xml:/app/reports/coverage.xml \
        --junitxml=/app/reports/junit.xml
}

run_frontend_tests() {
    log_message "Запуск unit-тестов фронтенда..."
    docker compose run --rm frontend npm run coverage
}

execute_all_unit_tests() {
    prepare_reports_dir
    run_api_tests
    run_bot_tests
    run_frontend_tests
}

start_services() {
    log_message "Запуск сервисов..."
    docker compose up -d
}

stop_services() {
    log_message "Остановка сервисов..."
    docker compose down
}

run_full() {
    build_images
    start_services
}

show_help() {
    echo "Использование: $0 [команда]"
    echo "Команды:"
    echo "  full"
    echo "  build"
    echo "  test_api"
    echo "  test_bot"
    echo "  test_frontend"
    echo "  test_integration"
    echo "  test"
    echo "  start"
    echo "  stop"
    echo "  help"
}

case "${1:-full}" in
    full)
        run_full
        ;;
    build)
        build_images
        ;;
    test_api)
        prepare_reports_dir
        run_api_tests
        ;;
    test_bot)
        prepare_reports_dir
        run_bot_tests
        ;;
    test_frontend)
        prepare_reports_dir
        run_frontend_tests
        ;;
    unit_test)
        execute_all_unit_tests
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo "[INFO] Неизвестная команда: $1"
        show_help
        exit 1
        ;;
esac