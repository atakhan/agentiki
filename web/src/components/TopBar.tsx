import { useEffect, useState } from "react";
import { MAX_CELL_PX, MIN_CELL_PX } from "../world/camera";

type TopBarProps = {
  zoom: number;
  cellPx: number;
  backend: string | null;
  agentCount: number;
  agentDensity: number;
  placedAgents: number;
  tick: number;
  lastStepInteractions: number;
  lastStepPdRounds: number;
  generating: boolean;
  stepping: boolean;
  playing: boolean;
  onZoomChange: (zoom: number) => void;
  onCellPxChange: (px: number) => void;
  onAgentCountChange: (count: number) => void;
  onAgentDensityChange: (density: number) => void;
  onGenerateAgents: () => void;
  onStep: (n: number) => void;
  onTogglePlay: () => void;
  onResetView: () => void;
};

const ZOOM_STEP = 0.1;
const MIN_AGENT_COUNT = 1;
const MAX_AGENT_COUNT = 100_000;
const MIN_AGENT_DENSITY = 0.1;
const MAX_AGENT_DENSITY = 5;

export default function TopBar({
  zoom,
  cellPx,
  backend,
  agentCount,
  agentDensity,
  placedAgents,
  tick,
  lastStepInteractions,
  lastStepPdRounds,
  generating,
  stepping,
  playing,
  onZoomChange,
  onCellPxChange,
  onAgentCountChange,
  onAgentDensityChange,
  onGenerateAgents,
  onStep,
  onTogglePlay,
  onResetView,
}: TopBarProps) {
  const [cellDraft, setCellDraft] = useState(String(cellPx));
  const [countDraft, setCountDraft] = useState(String(agentCount));
  const zoomPercent = Math.round(zoom * 100);
  const simDisabled = backend === null || placedAgents === 0;

  useEffect(() => {
    setCellDraft(String(cellPx));
  }, [cellPx]);

  useEffect(() => {
    setCountDraft(String(agentCount));
  }, [agentCount]);

  const commitCellPx = () => {
    const parsed = Number(cellDraft);
    if (Number.isFinite(parsed)) {
      onCellPxChange(parsed);
    } else {
      setCellDraft(String(cellPx));
    }
  };

  const commitAgentCount = () => {
    const parsed = Number(countDraft);
    if (
      Number.isFinite(parsed) &&
      parsed >= MIN_AGENT_COUNT &&
      parsed <= MAX_AGENT_COUNT
    ) {
      onAgentCountChange(Math.round(parsed));
    } else {
      setCountDraft(String(agentCount));
    }
  };

  return (
    <header className="navbar bg-base-200 h-12 min-h-12 gap-2 px-3">
      <div className="navbar-start min-w-0 flex-1 gap-2">
        <span className="shrink-0 text-base font-semibold tracking-tight">
          agentiki
        </span>
        <span className="truncate text-xs opacity-60">
          tick {tick}
          {lastStepInteractions > 0 ? ` · contacts ${lastStepInteractions}` : ""}
          {lastStepPdRounds > 0 ? ` · PD ${lastStepPdRounds}` : ""}
          {placedAgents > 0 ? ` · ${placedAgents} аг.` : ""}
          {backend ? ` · ${backend}` : " · офлайн"}
        </span>
      </div>

      <div className="navbar-center flex-none gap-2">
        <div className="join">
          <button
            type="button"
            className="btn btn-sm join-item px-3"
            disabled={simDisabled}
            aria-label={playing ? "Пауза" : "Play"}
            onClick={onTogglePlay}
          >
            {playing ? "⏸" : "▶"}
          </button>
          <button
            type="button"
            className="btn btn-sm join-item"
            disabled={playing || stepping || simDisabled}
            onClick={() => onStep(1)}
          >
            Шаг
          </button>
          <button
            type="button"
            className="btn btn-sm join-item"
            disabled={playing || stepping || simDisabled}
            onClick={() => onStep(10)}
          >
            ×10
          </button>
        </div>

        <div className="join hidden sm:flex">
          <button
            type="button"
            className="btn btn-sm join-item px-2"
            aria-label="Уменьшить масштаб"
            onClick={() => onZoomChange(zoom - ZOOM_STEP)}
          >
            −
          </button>
          <span className="btn btn-sm join-item pointer-events-none min-w-12 px-1 font-mono text-xs">
            {zoomPercent}%
          </span>
          <button
            type="button"
            className="btn btn-sm join-item px-2"
            aria-label="Увеличить масштаб"
            onClick={() => onZoomChange(zoom + ZOOM_STEP)}
          >
            +
          </button>
        </div>
      </div>

      <div className="navbar-end min-w-0 flex-1 justify-end gap-1">
        <details className="dropdown dropdown-end">
          <summary className="btn btn-sm">Агенты</summary>
          <div className="dropdown-content bg-base-200 z-20 mt-1 w-56 rounded-box p-3 shadow-lg">
            <fieldset className="fieldset gap-3">
              <label className="input input-sm w-full">
                <span className="label">Кол-во</span>
                <input
                  type="number"
                  min={MIN_AGENT_COUNT}
                  max={MAX_AGENT_COUNT}
                  step={1}
                  value={countDraft}
                  aria-label="Количество агентов"
                  onChange={(event) => setCountDraft(event.target.value)}
                  onBlur={commitAgentCount}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.currentTarget.blur();
                    }
                  }}
                />
              </label>
              <div>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="label p-0">Плотность</span>
                  <span className="font-mono opacity-70">
                    {agentDensity.toFixed(1)}
                  </span>
                </div>
                <input
                  type="range"
                  min={MIN_AGENT_DENSITY * 10}
                  max={MAX_AGENT_DENSITY * 10}
                  step={1}
                  value={Math.round(agentDensity * 10)}
                  className="range range-xs w-full"
                  aria-label="Плотность агентов"
                  onChange={(event) =>
                    onAgentDensityChange(Number(event.target.value) / 10)
                  }
                />
              </div>
              <button
                type="button"
                className="btn btn-sm btn-block"
                disabled={generating || backend === null}
                onClick={onGenerateAgents}
              >
                {generating ? (
                  <span className="loading loading-spinner loading-xs" />
                ) : (
                  "Сгенерировать"
                )}
              </button>
            </fieldset>
          </div>
        </details>

        <details className="dropdown dropdown-end">
          <summary className="btn btn-sm">Вид</summary>
          <div className="dropdown-content bg-base-200 z-20 mt-1 w-56 rounded-box p-3 shadow-lg">
            <fieldset className="fieldset gap-3">
              <div>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="label p-0">Масштаб</span>
                  <span className="font-mono opacity-70">{zoomPercent}%</span>
                </div>
                <input
                  type="range"
                  min={10}
                  max={400}
                  step={5}
                  value={zoomPercent}
                  className="range range-xs w-full"
                  aria-label="Масштаб"
                  onChange={(event) =>
                    onZoomChange(Number(event.target.value) / 100)
                  }
                />
              </div>
              <label className="input input-sm w-full">
                <span className="label">Ячейка</span>
                <input
                  type="number"
                  min={MIN_CELL_PX}
                  max={MAX_CELL_PX}
                  step={1}
                  value={cellDraft}
                  aria-label="Размер ячейки в пикселях"
                  onChange={(event) => {
                    const next = event.target.value;
                    setCellDraft(next);
                    const parsed = Number(next);
                    if (
                      next.trim() !== "" &&
                      Number.isFinite(parsed) &&
                      parsed >= MIN_CELL_PX &&
                      parsed <= MAX_CELL_PX
                    ) {
                      onCellPxChange(parsed);
                    }
                  }}
                  onBlur={commitCellPx}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.currentTarget.blur();
                    }
                  }}
                />
                <span className="label">px</span>
              </label>
              <button
                type="button"
                className="btn btn-sm btn-block"
                onClick={onResetView}
              >
                К началу
              </button>
              <p className="label text-xs opacity-50">
                drag — панорама · wheel — зум
              </p>
            </fieldset>
          </div>
        </details>
      </div>
    </header>
  );
}
