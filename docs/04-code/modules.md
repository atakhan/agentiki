# Модули

## `agentiki.sim.protocol`

* `Cell` — frozen DTO ячейки.
* `SimulationEngine` — runtime-checkable protocol: step/reset/cell/agents/generate/observe/config/food/last_interactions.

## `agentiki.sim.engine`

* `PythonEngine` — бэкенд по умолчанию; связывает мир, популяцию, еду, встречи, `RandomTestStrategy`, `step_tick`.
* `create_engine(backend=...)` — factory; путь `rust` импортирует `agentiki_sim_rust`.
* `DEFAULT_SPATIAL_CELL_SIZE = 4.0` — хранится на движке; spatial-хеш популяции независимо использует `1.0`.

## `agentiki.sim.tick`

* Protocol `AgentStrategy` — `choose(observation, config, rng)`.
* `step_tick(...)` — полная оркестрация тика (в т.ч. EatAction и food), возвращает `StepResult`.

## `agentiki.sim.agents`

* `AgentState`, `Agent` (поля `hp`, `energy`, …), `AgentPopulation`, `MAX_AGENTS`.
* Генерация внутри bounds, занятость, `apply_positions`, итерация по bounds.

## `agentiki.sim.world`

* `BoundedWorld`, `DEFAULT_MAP_WIDTH` / `DEFAULT_MAP_HEIGHT` (64).

## `agentiki.sim.config`

* `SimulationConfig`: радиусы, map W×H, food_*, `enable_pd`, life/PD payoffs.

## `agentiki.sim.actions`

* `MoveDirection`, `MoveAction`, `InteractAction`, `EatAction`, `AgentAction`.

## `agentiki.sim.movement`

* `tick_rng`, `move_priority`, `target_cell`, `build_intents_from_actions`, `resolve_moves`.
* Алиас `Action = MoveDirection` для старых call sites/тестов.

## `agentiki.sim.food`

* `Food`, `FoodStore`, `FoodConsumption`, спавн / density replenish / `process_food_consumption(eat_intents)`.

## `agentiki.sim.foraging`

* `pick_nearest_food`, `pick_eatable_food`, `direction_toward`.

## `agentiki.sim.interactions`

* `Interaction`, `is_valid_interact`, `resolve_interactions`.

## `agentiki.sim.meetings`

* `Meeting`, `MeetingStore`, `MeetingStatus`, `ContinueChoice`, `MeetingRoundOutcome`.
* Protocol `MeetingStrategy` — `choose_pd`, `choose_continue`.
* `create_meetings_from_interactions`, `process_meeting_rounds`.

## `agentiki.sim.pd`

* `PDChoice`, `PayoffMatrix`, `PDRoundResult`.

## `agentiki.sim.genetics`

* `Genome` (ШВГОП / ШПМ / ШЗ), `OpponentMemory`, `evaluate_opponent`, `decide_against`.
* Считает ход PD и когнитивную стоимость. В `step_tick` не подключён; `energy` не уменьшает. Мутаций и наследования нет. Правила — в `docs/02-domain/genetics.md`.

## `agentiki.sim.perception`

* `VisibleAgent`, `VisibleFood`, `RelativeAgent`, `RelativeFood`, `Observation`.
* `chebyshev_distance`, `manhattan_distance`, `is_interactable`, `observe`.

## `agentiki.sim.strategy.random_test`

* `RandomTestStrategy` — временная политика: eat → seek food → (interact если PD) → random move; meeting PD/continue.

## `agentiki.server.main`

* Создание движка в lifespan; обработчики маршрутов (в т.ч. `/api/food`); mount статики; helper `run()`.

## `agentiki.server.schemas`

* Pydantic request/response модели API, включая map/food, `LifeRulesIn` и `WorldConfigIn`.

## `agentiki.server.world_configs`

* Именованные конфиги спавна: `data/world_configs/<имя>.json`. Не снимок тика и агентов.

## Модули фронтенда (высокий уровень)

| Модуль | Роль |
| --- | --- |
| `web/src/api.ts` | REST-клиент |
| `web/src/world/hash.ts` | Общий хеш ячеек / цвета |
| `web/src/world/camera.ts` | Математика камеры |
| `web/src/world/render*.ts` | Отрисовка сетки / агентов / еды / зрения |
| `web/src/world/interactionOverlay.ts` | Кратковременные визуалы interact/PD |
| `web/src/world/agentAnimation.ts` | Плавные переходы агентов |
| `web/src/components/WorldCanvas.tsx` | Ввод + rAF paint |
| `web/src/components/HomeScreen.tsx` | Главная: новый / загрузить мир |
| `web/src/components/ConfigScreen.tsx` | Карта, популяция, еда, жизнь |
| `web/src/components/LoadScreen.tsx` | Список сохранённых конфигов |
| `web/src/components/TopBar.tsx` | Play/pause, «Рестарт», zoom, «Вид» |
| `web/src/App.tsx` | Экраны, play loop, инспектор hp/energy |
