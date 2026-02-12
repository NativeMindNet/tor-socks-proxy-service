# Requirements: Instance CI/CD

> Version: 1.2
> Status: APPROVED
> Last Updated: 2026-02-12

## Problem Statement

Необходимо автоматизировать процесс деплоя tor-socks-proxy-service на различные окружения (prod, dev, stage) при пуше в соответствующие ветки.

**Ключевые проблемы текущей конфигурации:**
- Порты захардкожены — невозможно запустить несколько окружений на одном сервере
- Нет привязки к конкретному IP — сервисы слушают на 0.0.0.0
- Образы без тегов окружения — конфликты при нескольких средах
- Логи только внутри контейнеров — сложно диагностировать

## Current State

**Репозиторий:** tor-socks-proxy-service (монорепо с сервисами)

**Сервисы в docker-compose.yml:**
| Сервис | Порт | Build | Описание |
|--------|------|-------|----------|
| tor-proxy | 9050 | docker/tor/Dockerfile | Tor SOCKS proxy |
| node-discovery | - | docker/node-discovery/Dockerfile | Node discovery |
| api | 8000 | docker/api/Dockerfile | REST API |
| prometheus | 9090 | image: prom/prometheus | Мониторинг |
| grafana | 3000 | image: grafana/grafana | Дашборды |
| cadvisor | 8080 | image: gcr.io/cadvisor | Container metrics |

**Структура:**
```
tor-socks-proxy-service/
├── docker-compose.yml          # Все сервисы
├── docker/
│   ├── api/Dockerfile
│   ├── tor/Dockerfile
│   └── node-discovery/Dockerfile
├── api/                        # API source
├── monitoring/                 # Prometheus/Grafana
└── db/
```

## User Stories

### Primary

**As a** разработчик
**I want** автоматический деплой при пуше в ветку (prod/dev/stage)
**So that** я могу быстро доставлять изменения без ручных операций

**As a** DevOps инженер
**I want** легкий доступ к логам приложения без входа в контейнер
**So that** я могу быстро диагностировать проблемы

**As a** оператор
**I want** запуск dev и prod на одном сервере без конфликтов
**So that** мы могли эффективнее использовать ресурсы

## Acceptance Criteria

### Must Have

1. **Given** пуш в ветку `prod`/`dev`/`stage`
   **When** GitHub Actions workflow запускается
   **Then** self-hosted runner на соответствующем инстансе:
   - Собирает образы локально
   - Обновляет и перезапускает контейнеры
   - Все 6 сервисов деплоятся вместе

2. **Given** dev и prod на одном сервере
   **When** оба окружения запущены
   **Then** они используют:
   - Разные IP-адреса/интерфейсы
   - Разные теги образов (`:dev`, `:prod`, `:stage`)
   - Не конфликтуют по портам

3. **Given** приложение работает
   **When** нужно просмотреть логи
   **Then** логи доступны в host-директории `/opt/tor-proxy/{env}/logs/`

4. **Given** Docker контейнер упал
   **When** Docker daemon обнаружил это
   **Then** контейнер автоматически перезапускается (restart: unless-stopped)

5. **Given** деплой на инстанс
   **When** обновляется docker-compose.yml из репо
   **Then** локальные `.env` и `docker-compose.override.yml` сохраняются

6. **Given** новый инстанс настраивается
   **When** оператор смотрит репозиторий
   **Then** есть `.env.example` с документацией всех переменных

### Should Have

- Ручной триггер workflow (workflow_dispatch)
- Простой health check после деплоя

### Won't Have (This Iteration)

- Blue-green deployment
- Автоматический rollback
- Уведомления (Slack/Telegram)
- Мониторинг и алертинг
- Kubernetes

## Technical Decisions

### Конфигурация (Approved)
- **Подход:** `.env` + `docker-compose.override.yml` на сервере
- **Расположение:** `/opt/tor-proxy/{env}/`
- **Что обновляется при деплое:** только `docker-compose.yml` из репо
- **Что сохраняется:** `.env`, `docker-compose.override.yml`, `logs/`

### Параметризация docker-compose.yml
```yaml
# Пример параметризации
services:
  api:
    image: tor-manager-api-image:${ENV_TAG:-latest}
    ports:
      - "${BIND_IP:-0.0.0.0}:${API_PORT:-8000}:8000"
    volumes:
      - ${LOGS_DIR:-./logs}/api:/app/logs
```

### Структура на сервере
```
/opt/tor-proxy/
├── dev/
│   ├── .env                    # BIND_IP=10.0.0.2, ENV_TAG=dev, etc.
│   ├── docker-compose.yml      # Из репо (обновляется)
│   ├── docker-compose.override.yml  # Локальные override (persistent)
│   └── logs/                   # Логи сервисов
├── prod/
│   ├── .env                    # BIND_IP=10.0.0.1, ENV_TAG=prod, etc.
│   ├── docker-compose.yml
│   ├── docker-compose.override.yml
│   └── logs/
└── stage/
    └── ...
```

## Constraints

- **Infrastructure:** Self-hosted GitHub Runner на каждом инстансе
- **Platform:** Docker + docker-compose на Linux
- **Network:** Разные IP-адреса для разных окружений
- **Build:** Сборка образов происходит локально на runner'е

## Open Questions

- [x] Какие IP-адреса/интерфейсы доступны на серверах? → **Указываются вручную в `.env` на сервере**
- [x] Нужно ли хранить `.env.example` в репо для референса? → **Да**
- [x] Нужен ли pre-deploy backup текущего состояния? → **Нет**

## References

- [GitHub Actions self-hosted runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Docker Compose environment variables](https://docs.docker.com/compose/environment-variables/)
- Текущий `docker-compose.yml` в репозитории

---

## Approval

- [x] Reviewed by: User
- [x] Approved on: 2026-02-12
- [x] Notes: All open questions resolved
