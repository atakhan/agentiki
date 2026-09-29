# Документация agentiki

Браузерная симуляция эволюции: бесконечное seed-детерминированное 2D-поле, агенты на тиках (ход / взаимодействие / PD-встречи), control plane на FastAPI, UI на React Canvas.

## Как читать

| Аудитория | Начать здесь |
| --- | --- |
| Первый взгляд | [01-concept/vision.md](01-concept/vision.md) → [цели](01-concept/goals.md) |
| Домен без кода | [02-domain/overview.md](02-domain/overview.md) → сущности → механики → правила |
| Устройство системы | [03-architecture/overview.md](03-architecture/overview.md) |
| Правка кода | [04-code/structure.md](04-code/structure.md) → модули → реализация |
| Запуск / тесты / деплой | [05-operations/setup.md](05-operations/setup.md) |

## Карта

```text
docs/
├── 01-concept/          Зачем существует проект
├── 02-domain/           Что такое мир (сущности, механики, алгоритмы, правила)
├── 03-architecture/     Как стыкуются слои и компоненты
├── 04-code/             Где что лежит в репозитории
├── 05-operations/       Установка, разработка, тесты, деплой
├── 06-experiments/      Шаблон журнала экспериментов (формальных прогонов нет)
├── 07-decisions/        Восстановленные дизайнерские решения
└── REVIEW.md            Известные пробелы, противоречия, риски
```

## Быстрые ссылки

* Эксперименты: [06-experiments/README.md](06-experiments/README.md)
* Решения: [07-decisions/README.md](07-decisions/README.md)
* Известные проблемы: [REVIEW.md](REVIEW.md)
* Исследовательские вопросы: [01-concept/research-questions.md](01-concept/research-questions.md)
* Корневой runbook: [../README.md](../README.md)

## Трассируемость

```text
Concept → Domain → Architecture → Code → Operations
```

Нижний слой уточняет верхний и не должен выдумывать новые продуктовые цели.
