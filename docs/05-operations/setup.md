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

Радиусы симуляции и матрица выплат — defaults в коде (`SimulationConfig` / `PayoffMatrix`), через env сегодня не задаются.

## Проверка установки

```bash
uv run python -m unittest discover -s tests
```

Ожидается: все тесты OK (на момент документации — 37).
