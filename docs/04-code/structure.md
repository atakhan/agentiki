# Структура репозитория

```text
agentiki/
├── README.md                 # Краткое введение + команды запуска
├── DOCUMENTATION_TZ.md       # ТЗ на документацию (мета)
├── docs/                     # Этот комплект документации
├── pyproject.toml            # Python-пакет agentiki 0.1.0
├── uv.lock
├── compose.yaml              # Docker Compose
├── Dockerfile                # Multi-stage: сборка web + Python app
├── src/agentiki/
│   ├── __init__.py
│   ├── server/               # FastAPI control plane
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── world_configs.py  # JSON конфигов спавна
│   └── sim/                  # Ядро симуляции
│       ├── engine.py         # PythonEngine + create_engine
│       ├── protocol.py       # SimulationEngine, Cell
│       ├── tick.py           # оркестрация step_tick
│       ├── world.py
│       ├── hashing.py
│       ├── agents.py
│       ├── spatial_hash.py
│       ├── perception.py
│       ├── actions.py
│       ├── movement.py
│       ├── interactions.py
│       ├── meetings.py
│       ├── pd.py
│       ├── results.py
│       ├── config.py
│       └── strategy/
│           └── random_test.py
├── tests/                    # Набор unittest
├── data/world_configs/       # JSON конфигов; каталог в .gitignore
└── web/                      # React + Vite + Canvas UI
    ├── package.json
    └── src/
        ├── App.tsx
        ├── api.ts
        ├── components/
        ├── types/
        └── world/
```

## Точки входа пакета

* Импорт библиотеки: `agentiki.sim`, `agentiki.server`
* Console script: `agentiki` → `agentiki.server.main:run`
* ASGI-приложение: `agentiki.server.main:app`

## Раскладка тестов

| Файл | Фокус |
| --- | --- |
| `test_movement.py` | Разрешение ходов, детерминизм |
| `test_interactions.py` | Контакты vs движение |
| `test_meetings.py` | Встречи, PD, continue/leave |
| `test_perception.py` | Радиусы зрения / interact, observe |
| `test_hp.py` | Траты hp, смерть, нестандартные правила жизни |
| `test_generation.py` | Равномерная решётка и шаг density |
| `test_world_configs.py` | Сохранение JSON и отказ при неверном порядке притока |

## Отсутствует (важные отсутствия)

* До этого комплекта `docs/` не было (кроме ТЗ в корне).
* Нет конфигурации CI.
* Нет Rust-crate в дереве.
* Нет миграций БД.
