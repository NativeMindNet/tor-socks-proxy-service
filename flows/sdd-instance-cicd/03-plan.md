# Implementation Plan: Instance CI/CD

> Version: 1.1
> Status: APPROVED
> Last Updated: 2026-02-12
> Specifications: ./02-specifications.md

## Summary

Реализация CI/CD для автодеплоя на prod/dev/stage инстансы с поддержкой Linux и macOS. Три основных deliverable: параметризованный docker-compose.yml, .env.example, и GitHub Actions workflow.

## Task Breakdown

### Phase 1: Docker Compose Parameterization

#### Task 1.1: Параметризация портов и IP
- **Description**: Заменить хардкод портов на переменные окружения с defaults
- **Files**:
  - `docker-compose.yml` - Modify
- **Dependencies**: None
- **Verification**: `docker-compose config` показывает переменные; запуск без .env использует defaults
- **Complexity**: Low

**Changes:**
```yaml
# Before
ports:
  - "9050:9050"

# After
ports:
  - "${BIND_IP:-0.0.0.0}:${TOR_PORT:-9050}:9050"
```

#### Task 1.2: Параметризация image tags
- **Description**: Добавить `${ENV_TAG:-latest}` к именам образов
- **Files**:
  - `docker-compose.yml` - Modify
- **Dependencies**: Task 1.1
- **Verification**: `docker-compose config` показывает теги; образы собираются с правильными тегами
- **Complexity**: Low

**Changes:**
```yaml
# Before
image: tor-proxy-image:latest

# After
image: tor-proxy-image:${ENV_TAG:-latest}
```

#### Task 1.3: Profile для cadvisor (Linux-only)
- **Description**: Добавить `profiles: ["linux"]` к cadvisor
- **Files**:
  - `docker-compose.yml` - Modify
- **Dependencies**: Task 1.1
- **Verification**: На Linux `--profile linux` запускает cadvisor; без profile - не запускает
- **Complexity**: Low

### Phase 2: Environment Configuration

#### Task 2.1: Создание .env.example
- **Description**: Создать документированный шаблон переменных окружения
- **Files**:
  - `.env.example` - Create
- **Dependencies**: Phase 1 complete
- **Verification**: Копия .env.example как .env позволяет запустить docker-compose
- **Complexity**: Low

**Content:**
- COMPOSE_PROJECT_NAME
- ENV_TAG
- BIND_IP
- All ports (TOR_PORT, API_PORT, etc.)
- GRAFANA_PASSWORD
- Примеры для Linux и macOS

**Logging:** Используется стандартный Docker logging (stdout → json-file). Доступ через `docker-compose logs`.

#### Task 2.2: Обновление .gitignore
- **Description**: Добавить .env в .gitignore (если не добавлен)
- **Files**:
  - `.gitignore` - Modify
- **Dependencies**: None
- **Verification**: `git status` не показывает .env файлы
- **Complexity**: Low

### Phase 3: GitHub Actions Workflow

#### Task 3.1: Создание базового workflow
- **Description**: Создать deploy.yml с triggers и job structure
- **Files**:
  - `.github/workflows/deploy.yml` - Create
- **Dependencies**: None
- **Verification**: Workflow появляется в GitHub Actions UI
- **Complexity**: Medium

**Structure:**
```yaml
name: Deploy
on:
  push:
    branches: [prod, dev, stage]
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [prod, dev, stage]
jobs:
  deploy:
    runs-on: [self-hosted, "${{ ... }}"]
```

#### Task 3.2: Environment validation step
- **Description**: Проверка DEPLOY_DIR и .env перед деплоем
- **Files**:
  - `.github/workflows/deploy.yml` - Modify
- **Dependencies**: Task 3.1
- **Verification**: Workflow fails gracefully если DEPLOY_DIR не задан или .env отсутствует
- **Complexity**: Low

#### Task 3.3: Deploy step с OS detection
- **Description**: Копирование файлов, build, restart с определением OS для profiles
- **Files**:
  - `.github/workflows/deploy.yml` - Modify
- **Dependencies**: Task 3.2
- **Verification**: На Linux запускается с `--profile linux`, на macOS без
- **Complexity**: Medium

#### Task 3.4: Health check step
- **Description**: Проверка что контейнеры запустились (warning only)
- **Files**:
  - `.github/workflows/deploy.yml` - Modify
- **Dependencies**: Task 3.3
- **Verification**: Warning в логах если < 3 сервисов running; workflow не fails
- **Complexity**: Low

### Phase 4: Documentation & Testing

#### Task 4.1: Обновление README
- **Description**: Добавить секцию о CI/CD setup
- **Files**:
  - `README.md` - Modify
- **Dependencies**: All previous tasks
- **Verification**: README содержит инструкции по настройке runner'ов
- **Complexity**: Low

#### Task 4.2: Локальное тестирование docker-compose
- **Description**: Проверить что параметризованный compose работает локально
- **Files**: None (testing only)
- **Dependencies**: Phase 1, Phase 2
- **Verification**:
  - `docker-compose config` без ошибок
  - `docker-compose up -d` запускает все сервисы
  - Логи пишутся в LOGS_DIR
- **Complexity**: Low

## Dependency Graph

```
Phase 1 (Docker Compose)          Phase 2 (Env)         Phase 3 (Workflow)
========================          =============         ==================

Task 1.1 ─────┬─────────────────→ Task 2.1              Task 3.1
(ports/IP)    │                   (.env.example)           │
              │                        │                   ▼
Task 1.2 ─────┤                        │              Task 3.2
(image tags)  │                        │              (validation)
              │                        │                   │
Task 1.3 ─────┘                        │                   ▼
(cadvisor)                             │              Task 3.3
                                       │              (deploy + OS)
              Task 2.2                 │                   │
              (.gitignore)             │                   ▼
                                       │              Task 3.4
                                       │              (health check)
                                       │                   │
                                       ▼                   ▼
                                  ┌─────────────────────────────┐
                                  │  Phase 4: Docs & Testing    │
                                  │  Task 4.1 (README)          │
                                  │  Task 4.2 (local test)      │
                                  └─────────────────────────────┘
```

**Logging:** Стандартный Docker (stdout → json-file). Просмотр: `docker-compose logs -f [service]`

## File Change Summary

| File | Action | Reason |
|------|--------|--------|
| `docker-compose.yml` | Modify | Параметризация (IP, ports, tags, logs, profiles) |
| `.env.example` | Create | Шаблон конфигурации |
| `.github/workflows/deploy.yml` | Create | CI/CD workflow |
| `.gitignore` | Modify | Исключить .env |
| `README.md` | Modify | Документация CI/CD setup |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| torrc путь изменился | Low | Low | Проверить текущий docker-compose |
| Runner не имеет прав на DEPLOY_DIR | Medium | High | Документировать в README требования к permissions |
| docker-compose v1 vs v2 синтаксис | Low | Medium | Использовать `docker-compose` (v1 compatible) |

## Rollback Strategy

Все изменения версионируются в git:

1. `git revert <commit>` для отката изменений
2. На серверах: старые контейнеры продолжают работать до успешного `docker-compose up`
3. `.env` на серверах не затрагивается деплоем

## Checkpoints

### После Phase 1:
- [ ] `docker-compose config` без ошибок
- [ ] Все переменные имеют defaults
- [ ] cadvisor в profile "linux"

### После Phase 2:
- [ ] `.env.example` содержит все переменные
- [ ] `.env` в .gitignore

### После Phase 3:
- [ ] Workflow виден в GitHub UI
- [ ] Push в dev ветку триггерит workflow

### После Phase 4:
- [ ] README обновлен
- [ ] Локальный тест пройден

## Open Implementation Questions

- [x] Куда пишут логи tor, node-discovery, api? → **stdout (стандартный Docker logging)**

---

## Approval

- [x] Reviewed by: User
- [x] Approved on: 2026-02-12
- [x] Notes: Simplified logging (Docker stdout)
