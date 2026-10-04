# Разработка

## Запуск через Docker

```bash
docker compose up --build
```

Открыть [http://127.0.0.1:8000](http://127.0.0.1:8000). UI вшит в образ и отдаётся FastAPI вместе с `/api`.

Compose задаёт:

* `AGENTIKI_SEED=1`
* `AGENTIKI_SIM_BACKEND=python`

Healthcheck бьёт в `/api/health`.

## Локальный запуск (два терминала)

Терминал 1 — API:

```bash
uv sync
uv run uvicorn agentiki.server.main:app --reload --host 127.0.0.1 --port 8000
```

Терминал 2 — UI:

```bash
cd web
npm install
npm run dev
```

Открыть [http://127.0.0.1:5173](http://127.0.0.1:5173). Vite проксирует `/api` на порт 8000.

Альтернативный вход API (без reload):

```bash
uv run agentiki
```

(`agentiki.server.main:run` — host `127.0.0.1`, port `8000`, `reload=False`.)

## Типичный сценарий в UI

1. На главной — «Новый мир» (или «Загрузить мир», тогда открывается уже заполненный конфиг).
2. На экране конфигурации задать число агентов, плотность 1–10 и правила жизни.
3. «Старт» — симуляция на паузе, тик 0, камера в origin. «Сохранить конфиги» спрашивает имя и пишет только JSON, мир не запускает.
4. Play (~1 с на тик) или «Рестарт» (тот же конфиг, камера на месте, снова пауза и тик 0).
5. Pan (drag), zoom (колёсико к курсору или кнопки), «Вид» — масштаб и px ячейки.
6. Клик по агенту — инспектор: жизнь (hp), встреча, радиусы. Отдельного score нет.

На симуляции нет полей count/density и меню «Жизнь». Ручных «Шаг» и «×10» нет.

Размер ячейки по умолчанию: **50 px** при zoom 100% (из серверного `default_cell_px`).

## Полезные точки входа при разработке

| Задача | Начать здесь |
| --- | --- |
| Поведение тика | `src/agentiki/sim/tick.py` |
| Поля API | `src/agentiki/server/schemas.py`, `main.py` |
| Canvas / камера | `web/src/components/WorldCanvas.tsx` |
| REST-клиент | `web/src/api.ts` |

## Диагностика

| Симптом | Проверить |
| --- | --- |
| UI открывается, API падает на `:5173` | Работает ли uvicorn на `:8000`? Proxy только в Vite dev. |
| В UI `backend: null` | Не удался начальный `fetchWorld` — CORS/порт/процесс. |
| `viewport too large` | `/api/world/cells` ограничен 20 000 ячейками. |
| `Rust simulation core is not installed` | `AGENTIKI_SIM_BACKEND=rust` без `agentiki_sim_rust`. Используйте `python`. |
| Generate 400 | Count/density вне допустимых диапазонов. |
| Нет статики UI на голом uvicorn | Не собран `web/dist`; используйте Vite dev или Docker build. |
