# Потоки данных

## Старт

```mermaid
sequenceDiagram
    participant Env
    participant FastAPI
    participant Factory as create_engine
    participant Engine as PythonEngine

    Env->>FastAPI: AGENTIKI_SEED, AGENTIKI_SIM_BACKEND
    FastAPI->>Factory: backend, seed
    Factory->>Engine: construct
    FastAPI->>FastAPI: app.state.engine = Engine
```

## Bootstrap UI

```mermaid
sequenceDiagram
    participant UI
    participant API
    participant Engine

    UI->>API: GET /api/world
    API->>Engine: seed, tick, radii, ...
    API-->>UI: WorldOut
    UI->>API: GET /api/agents
    API->>Engine: list_agents
    API-->>UI: AgentsOut
```

## Генерация агентов

```text
UI POST /api/agents/generate {count, density}
  → engine.generate_agents(...)
    → AgentPopulation.clear + взвешенная выборка по диску + place
  → AgentsOut
UI обновляет tick через GET /api/world
```

## Step (вручную или play-интервал)

```mermaid
flowchart LR
    UI[UI step / play] --> API["POST /api/world/step"]
    API --> ENG[engine.step]
    ENG --> TICK[step_tick]
    TICK --> RES[StepResult]
    RES --> API2[StepOut JSON]
    API2 --> UI2[Обновить агентов, tick, оверлеи]
```

Внутри `step_tick` (концептуально):

```text
СВОБОДНЫЕ агенты: observe → strategy.choose
interact intents → resolve_interactions → создать встречи
move intents → resolve_moves → apply_positions
продолжающиеся встречи → раунд PD
новые встречи → раунд PD
вернуть StepResult
```

## Debug observation (отладка)

```text
UI выбирает агента
  → GET /api/agents/{id}/observation
  → engine.observe
  → ObservationOut
UI рисует оверлеи зрения / взаимодействия
```

## Путь клиентской отрисовки

```text
camera + cellPx
  → видимый AABB мира
  → renderGrid (локальный хеш ячейки / единый цвет)
  → renderAgents (анимированные позиции)
  → renderVisionDebug (если выбран агент)
  → renderInteractions (импульсы последнего step)
```

Авторитет симуляции остаётся на сервере; клиент только интерполирует движение для отображения.
