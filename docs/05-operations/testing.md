# Тестирование

## Команда

Из корня репозитория:

```bash
uv run python -m unittest discover -s tests
```

Подробно:

```bash
uv run python -m unittest discover -s tests -v
```

## Что покрыто

| Область | Файл | Стиль |
| --- | --- | --- |
| Конфликты / цепочки / жеребьёвка / стены | `tests/test_movement.py` | unittest |
| Interaction vs движение | `tests/test_interactions.py` | unittest + скриптовые стратегии |
| Встречи / PD / continue | `tests/test_meetings.py` | unittest |
| Генетические шкалы | `tests/test_genetics.py` | unittest |
| Восприятие / ограничения config | `tests/test_perception.py` | unittest |
| Траты и смерть hp | `tests/test_hp.py` | unittest |
| Еда / EatAction / replenish | `tests/test_food.py` | unittest |
| Решётка генерации | `tests/test_generation.py` | unittest |
| Границы карты | `tests/test_world_bounds.py` | unittest |
| JSON конфигов мира | `tests/test_world_configs.py` | unittest |

## Что не покрыто (текущий пробел)

* Тесты маршрутов FastAPI / HTTP-контракта
* Unit или e2e тесты фронтенда
* Тесты паритета хеша ячеек Python ↔ TypeScript
* Smoke-тесты Docker-образа сверх healthcheck Compose
* Rust-бэкенд

## Ручной smoke-чеклист

1. `GET /api/health` → `{"status":"ok"}`
2. «Новый мир» → карта/агенты/еда → «Старт»
3. Play; tick растёт, агенты идут к еде / едят отдельным тиком (PD по умолчанию выключен)
4. Выбрать агента; оверлей зрения; инспектор показывает hp и energy
5. `POST /api/world/reset` с seed; мир перезапускается пустым

## Проверки сборки (web)

```bash
cd web
npm run build
```

Выполняет `tsc -b && vite build`.
