# Заметки по реализации

Где менять механику и что код делает сейчас.

## Замена политики решений агента

* Движок создаёт `RandomTestStrategy()` в `PythonEngine.__init__`.
* Реализовать `choose` / `choose_pd` / `choose_continue` (протоколы в `tick.py` и `meetings.py`).
* Подключить новый экземпляр в `PythonEngine` (или через конструктор — **Fact:** API инъекции пока нет; стратегия зашита).

**Оговорка:** `Observation.for_strategy()` скрывает id, но `RandomTestStrategy` читает `visible_agents` (с id), чтобы строить `InteractAction`.

## Изменение радиусов восприятия

* По умолчанию: `SimulationConfig(vision_radius=3, interaction_radius=1)`.
* Движок использует `config or SimulationConfig()`; сервер пока не даёт менять радиусы через API в runtime (**Fact:** радиусы только отдаются в `WorldOut` / observation).

## Конфликты движения

* Править `resolve_moves` в `movement.py`.
* Хорошо покрыто `tests/test_movement.py`.

## Связка interaction / meeting

* Контакты: `interactions.py`.
* Открытие встречи + PD: `meetings.py` + `pd.py`.
* Порядок стадий в `step_tick` критичен — не переставлять без обновления доменных доков и тестов.

## Встреча и ход в одном тике

В тике контакта цель, выбравшая `MoveAction`, всё равно ходит после создания встречи (`test_target_moves_away_contact_still_happens`). «Заморозка» встречи действует на **следующих** тиках, когда решение пропускается.

## Смена бэкенда

```python
create_engine(backend="python" | "rust", seed=..., spatial_cell_size=..., config=...)
```

Путь Rust ожидает `agentiki_sim_rust.Engine(...)` с совместимой поверхностью.

## Риск расхождения общего хеша

Python `hashing.py` и TypeScript `world/hash.ts` должны оставаться алгоритмически одинаковыми. Автотеста кросс-языкового паритета хеша в репозитории нет (**Fact**).

## Мёртвые / неиспользуемые части (реализация)

* `PythonEngine.spatial` очищается на reset, но никогда не заполняется и не опрашивается; восприятие идёт через `AgentPopulation.spatial`.
* `Agent.genome` нигде не читается.
* `cell_biome` / `cell_color` игнорируют координаты и seed (хеш всё равно считается и отдаётся).

## Play loop в UI

* `PLAY_INTERVAL_MS = 1000`; шлёт `step` с `n=1`.
* Защита `steppingRef` от перекрывающихся step.
* Interaction overlay накапливает события последнего step для короткой отрисовки.

## Упаковка Docker

* Stage `web`: `npm ci` + `npm run build`.
* Stage `app`: `uv sync --frozen --no-dev`, копирование `web/dist`, uvicorn на `0.0.0.0:8000`.
