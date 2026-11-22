# agentiki

Браузерная симуляция эволюции: фиксированное прямоугольное поле W×H, тысячи агентов (позже), детерминированный tick.

Полная документация: [docs/README.md](docs/README.md).

## Стек

| Слой | Сейчас | Позже |
| --- | --- | --- |
| Управление | FastAPI (`src/agentiki/server`) | тот же API |
| Simulation core | Python (`src/agentiki/sim`) | Rust/pyo3 за тем же `SimulationEngine` |
| UI | React + TypeScript + Canvas | без смены контракта |

Карта — прямоугольник `[0 .. width) × [0 .. height)` (размер задаётся при создании мира, по умолчанию 64×64). Содержимое клетки по-прежнему считается из seed-hash; край жёсткий (ход за границу = stay). Камера на клиенте; сервер отдаёт `map_width` / `map_height`.

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
- `POST /api/world/step` `{ "n": 1 }` → `{ "world", "agents", "food", "food_consumed", "interactions", "meetings_started", "pd_rounds" }`
- `POST /api/world/reset` `{ "seed": 1 }`
- `GET /api/agents` (опционально `min_x`, `min_y`, `max_x`, `max_y`)
- `POST /api/agents/generate` `{ "count": 100, "density": 1.0, "map_width": 64, "map_height": 64, "food_capacity": 50 }`
- `GET /api/food`
- `GET /api/agents/{id}/observation`

Агент — круг в центре ячейки. Генерация — решётка с шагом `density` в центре карты; одна ячейка — один агент. Если не помещается — ошибка.

Движение: видит еду → идёт к ней. Поедание — отдельный tick (`EatAction`). `food_energy / n` → energy. **hp** — жизнь-таймер (random min…max, −1/тик, не пополняется). **energy** — старт 100 (конфиг мира), траты за действия, приток от еды/PD; ≤ 0 → смерть. PD по умолчанию выключен.

Восприятие: `vision_radius` / `interaction_radius` (Чебышёв), `engine.observe(agent_id)` → `Observation` с относительными координатами. Клик по агенту на карте — debug-визуализация зон.

Тесты: `uv run python -m unittest discover -s tests`
