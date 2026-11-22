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

* Править `resolve_moves` / `move_priority` в `movement.py`.
* Победитель — max hash-лотереи, не min id.
* Хорошо покрыто `tests/test_movement.py`.

## Еда и EatAction

* Стор и потребление: `food.py`. Поиск/eatable: `foraging.py`. Действие: `EatAction` в `actions.py`.
* Стратегия по умолчанию сначала ест, потом идёт к еде (`strategy/random_test.py`).
* Покрыто `tests/test_food.py`. Не смешивать «дойти» и «съесть» в одном тике.

## Связка interaction / meeting

* Контакты: `interactions.py`.
* Открытие встречи + PD: `meetings.py` + `pd.py`.
* По умолчанию `enable_pd=False` в `SimulationConfig`; для тестов PD включают явно.
* Порядок стадий в `step_tick` критичен — не переставлять без обновления доменных доков и тестов.

## Генетические шкалы

* Формулы и границы — `docs/02-domain/genetics.md`. Код — `sim/genetics.py`.
* Подключение к `choose_pd` — отдельный шаг: сейчас PD по-прежнему выбирает стратегия (`RandomTestStrategy` или скрипт в тесте).
* `N_max` ШВГОП в коде — `SHVGOP_MAX = 256`.
* Когнитивная стоимость возвращается полем `OpponentDecision.cognitive_cost` и из `energy` не списывается.

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
* `Agent.genome` — `Genome | None`. Оценка живёт в `genetics.py` и из тика не вызывается; генерация геном не назначает.
* `cell_biome` / `cell_color` игнорируют координаты и seed (хеш всё равно считается и отдаётся).

## Правила карты / еды / жизни в UI

Экран конфигурации задаёт размер карты, capacity/density/energy еды, старт hp, траты и приток PD. «Старт» и «Рестарт» вызывают `generate` с этими правилами; play шлёт life-правила в каждый `step`. Меню на симуляции нет. Неверный порядок притока в состояние конфига не принимается (`Приток: предатель > оба C > оба D > кооператор`).

## Play loop в UI

* `PLAY_INTERVAL_MS = 1000`; play шлёт `step` с `n=1`.
* Кнопок «Шаг» и «×10» нет.
* «Рестарт» ставит паузу, делает reset и generate тем же конфигом сессии, остаётся на симуляции, камеру не двигает, мир на тике 0.
* «Старт» с экрана конфига дополнительно возвращает камеру в origin.
* Защита `steppingRef` от перекрывающихся step.
* Жёлтый пунктир контакта (`renderInteractions.ts`, `FADE_MS = 1500`) соединяет позиции после хода и дистанцию не проверяет.

## Упаковка Docker

* Stage `web`: `npm ci` + `npm run build`.
* Stage `app`: `uv sync --frozen --no-dev`, копирование `web/dist`, uvicorn на `0.0.0.0:8000`.
