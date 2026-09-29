# Модули

## `agentiki.sim.protocol`

* `Cell` — frozen DTO ячейки.
* `SimulationEngine` — runtime-checkable protocol: step/reset/cell/agents/generate/observe/config/last_interactions.

## `agentiki.sim.engine`

* `PythonEngine` — бэкенд по умолчанию; связывает мир, популяцию, встречи, `RandomTestStrategy`, `step_tick`.
* `create_engine(backend=...)` — factory; путь `rust` импортирует `agentiki_sim_rust`.
* `DEFAULT_SPATIAL_CELL_SIZE = 4.0` — хранится на движке; spatial-хеш популяции независимо использует `1.0`.

## `agentiki.sim.tick`

* Protocol `AgentStrategy` — `choose(observation, config, rng)`.
* `step_tick(...)` — полная оркестрация тика, возвращает `StepResult`.

## `agentiki.sim.agents`

* `AgentState`, `Agent`, `AgentPopulation`, `MAX_AGENTS`.
* Генерация, занятость, `apply_positions`, итерация по bounds.

## `agentiki.sim.movement`

* `tick_rng`, `target_cell`, `build_intents_from_actions`, `resolve_moves`.
* Алиас `Action = MoveDirection` для старых call sites/тестов.

## `agentiki.sim.interactions`

* `Interaction`, `is_valid_interact`, `resolve_interactions`.

## `agentiki.sim.meetings`

* `Meeting`, `MeetingStore`, `MeetingStatus`, `ContinueChoice`, `MeetingRoundOutcome`.
* Protocol `MeetingStrategy` — `choose_pd`, `choose_continue`.
* `create_meetings_from_interactions`, `process_meeting_rounds`.

## `agentiki.sim.pd`

* `PDChoice`, `PayoffMatrix`, `PDRoundResult`.

## `agentiki.sim.perception`

* `VisibleAgent`, `RelativeAgent`, `Observation`.
* `chebyshev_distance`, `is_interactable`, `observe`.

## `agentiki.sim.strategy.random_test`

* `RandomTestStrategy` — временная случайная политика; реализует методы world- и meeting-стратегии.

## `agentiki.server.main`

* Создание движка в lifespan; обработчики маршрутов; mount статики; helper `run()`.

## `agentiki.server.schemas`

* Pydantic request/response модели API.

## Модули фронтенда (высокий уровень)

| Модуль | Роль |
| --- | --- |
| `web/src/api.ts` | REST-клиент |
| `web/src/world/hash.ts` | Общий хеш ячеек / цвета |
| `web/src/world/camera.ts` | Математика камеры |
| `web/src/world/render*.ts` | Отрисовка на canvas |
| `web/src/world/interactionOverlay.ts` | Кратковременные визуалы interact/PD |
| `web/src/world/agentAnimation.ts` | Плавные переходы агентов |
| `web/src/components/WorldCanvas.tsx` | Ввод + rAF paint |
| `web/src/components/TopBar.tsx` | Контролы |
| `web/src/App.tsx` | Состояние приложения / play loop |
