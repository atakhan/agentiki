# agentiki

Браузерная симуляция эволюции: бесконечное двумерное поле, тысячи агентов (позже), детерминированный tick.

## Стек

| Слой | Сейчас | Позже |
| --- | --- | --- |
| Управление | FastAPI (`src/agentiki/server`) | тот же API |
| Simulation core | Python (`src/agentiki/sim`) | Rust/pyo3 за тем же `SimulationEngine` |
| UI | React + TypeScript + Canvas | без смены контракта |

Поле бесконечное и считается по seed: ячейка `(x, y)` всегда одна и та же. Визуализатор в браузере использует тот же u32-hash, что и Python. Камера живёт на клиенте, сервер отдаёт конфиг мира.

Точка замены ядра: `create_engine(backend=...)`. Rust включается переменной `AGENTIKI_SIM_BACKEND=rust`, когда появится модуль `agentiki_sim_rust`.

## Запуск

Одной командой через Docker:

```bash
docker compose up --build
```

Открыть [http://127.0.0.1:8000](http://127.0.0.1:8000). UI собирается в образ и отдаётся FastAPI вместе с `/api`.

Локально без Docker — в двух терминалах:

```bash
uv sync
uv run uvicorn agentiki.server.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
cd web
npm install
npm run dev
```

Открыть [http://127.0.0.1:5173](http://127.0.0.1:5173).

По умолчанию ячейка **50 px** при масштабе 100%. Перетаскивание двигает карту, колёсико зумит к курсору.

## API

- `GET /api/health`
- `GET /api/world`
- `GET /api/world/cell?x=&y=`
- `GET /api/world/cells?min_x=&min_y=&max_x=&max_y=`
- `POST /api/world/step` `{ "n": 1 }` → `{ "world": {...}, "agents": {...} }`
- `POST /api/world/reset` `{ "seed": 1 }`
- `GET /api/agents` (опционально `min_x`, `min_y`, `max_x`, `max_y`)
- `POST /api/agents/generate` `{ "count": 100, "density": 1.0 }`

Агент — круг в центре ячейки. Генерация случайная от центра `(0, 0)`, одна ячейка — один агент. Плотность: выше = компактнее у центра.

Движение: каждый tick все агенты одновременно выбирают действие (STAY/NORTH/SOUTH/EAST/WEST, пока случайно), намерения разрешаются, позиции обновляются атомарно. Конфликт за клетку — побеждает минимальный `agent_id`.

Восприятие: `vision_radius` / `interaction_radius` (Чебышёв), `engine.observe(agent_id)` → `Observation` с относительными координатами. Клик по агенту на карте — debug-визуализация зон.

Тесты: `uv run python -m unittest discover -s tests`
