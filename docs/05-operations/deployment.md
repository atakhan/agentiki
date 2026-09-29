# Развёртывание

## Поддерживаемая упаковка

В репозитории есть путь развёртывания через **Docker**; отдельного Kubernetes/Helm/cloud IaC в дереве нет.

### Сборка и запуск

```bash
docker compose up --build
```

Или собрать образ напрямую из `Dockerfile` и пробросить порт `8000`.

### Форма образа

1. **web stage** — Node 22, `npm ci`, `npm run build` → статика.
2. **app stage** — Python 3.12 + uv, `uv sync --frozen --no-dev`, копирование `src/` и `web/dist`, старт:

```text
uvicorn agentiki.server.main:app --host 0.0.0.0 --port 8000
```

### Runtime env

Задаётся при старте контейнера (пример Compose):

* `AGENTIKI_SEED`
* `AGENTIKI_SIM_BACKEND`

### Health

Healthcheck Compose:

```text
GET http://127.0.0.1:8000/api/health
```

## Production-ограничения (фактические)

* Состояние симуляции **в памяти** процесса; рестарт теряет мир.
* На control-эндпоинтах нет auth — кто достучался до порта, может step/reset/generate.
* В документированном CMD предполагается один worker (один экземпляр движка на `app.state`).
* Горизонтальное масштабирование породило бы независимые миры, пока нет внешней координации (**Inference:** пока не спроектировано).

## Минимальный деплой без Docker

1. Собрать UI: `cd web && npm ci && npm run build`, чтобы `web/dist` оказался там, где его ждёт сервер (`Path(__file__).parents[3] / "web" / "dist"` из `main.py`).
2. `uv sync --frozen` (или `uv sync`) и запустить uvicorn как выше.
3. При необходимости — reverse proxy спереди (в репозитории не настроен).

## CI / CD

**Unknown / absent:** на момент документации файлов GitHub Actions или иных пайплайнов в репозитории не найдено.
