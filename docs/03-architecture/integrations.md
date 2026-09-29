# Интеграции

## HTTP API

Базовый путь: `/api`.

| Метод | Путь | Роль |
| --- | --- | --- |
| GET | `/health` | Liveness |
| GET | `/world` | Сводка мира + радиусы |
| GET | `/world/cell?x&y` | Одна ячейка |
| GET | `/world/cells?min_x&min_y&max_x&max_y&step` | Ячейки viewport (макс. 20 000) |
| POST | `/world/step` | Продвинуть `n` тиков (`0…10000`); вернуть world, agents, interactions, meetings, PD rounds |
| POST | `/world/reset` | Сброс; опционально новый seed |
| GET | `/agents` | Все агенты или фильтр по bounds, если заданы все четыре |
| POST | `/agents/generate` | Заменить популяцию |
| GET | `/agents/{agent_id}/observation` | Снимок восприятия |

CORS разрешает `http://localhost:5173` и `http://127.0.0.1:5173`.

Статика UI: если существует `web/dist` относительно layout пакета, он монтируется на `/`.

## Переменные окружения

| Переменная | По умолчанию | Эффект |
| --- | --- | --- |
| `AGENTIKI_SEED` | `1` | Seed движка при старте |
| `AGENTIKI_SIM_BACKEND` | `python` | Выбор бэкенда |

## Внешние / будущие модули

| Интеграция | Статус |
| --- | --- |
| `agentiki_sim_rust` | Ожидаемое имя pyo3-модуля; при отсутствии import → `NotImplementedError` |
| npm registry | Зависимости web-сборки |
| uv / PyPI | Python-зависимости (FastAPI, uvicorn, pydantic) |
| Docker Hub / ghcr | Базовые образы `node:22-alpine`, `python:3.12-slim-bookworm`, `ghcr.io/astral-sh/uv` |

## Dev-прокси

Vite проксирует `/api` → `http://127.0.0.1:8000`, чтобы в `npm run dev` браузер ходил на относительный `/api`.

## Что не интегрировано

* Базы данных
* Очереди сообщений
* Провайдеры auth
* Бэкенды наблюдаемости
* CI-сервисы (в репозитории нет workflow-файлов)
