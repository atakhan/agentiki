# Установка

## Требования

* Python **≥ 3.12**
* [uv](https://github.com/astral-sh/uv) для Python-зависимостей (рекомендуется; используется Docker и README)
* Node.js **22+** для web-приложения (в Docker — `node:22-alpine`)
* Docker + Docker Compose (опционально, для запуска одной командой)

## Установка (локально)

Из корня репозитория:

```bash
uv sync
```

Зависимости web:

```bash
cd web
npm install
```

(в Docker при опоре на lockfile используется `npm ci`.)

## Конфигурация

| Переменная | По умолчанию | Где |
| --- | --- | --- |
| `AGENTIKI_SEED` | `1` | Окружение процесса (Compose задаёт) |
| `AGENTIKI_SIM_BACKEND` | `python` | Окружение процесса |

Радиусы симуляции — defaults в коде (`vision_radius=3`, `interaction_radius=1`). Правила жизни по умолчанию: старт 60, ход 2, стояние 1, решение 1, раунд 1; приток +3/+3, +1/+1, +0/+5. Через env они не задаются; UI пишет их в generate и step. Каталог конфигов — `AGENTIKI_CONFIG_DIR` или `data/world_configs`.

## Проверка установки

```bash
uv run python -m unittest discover -s tests
```

Ожидается: все тесты OK (прогон 2026-10-04: 51 tests, OK).
