import { useEffect, useState } from "react";
import { MAX_CELL_PX, MIN_CELL_PX } from "../world/camera";

type TopBarProps = {
  zoom: number;
  cellPx: number;
  backend: string | null;
  placedAgents: number;
  tick: number;
  playing: boolean;
  stepping: boolean;
  onZoomChange: (zoom: number) => void;
  onCellPxChange: (px: number) => void;
  onTogglePlay: () => void;
  onRestart: () => void;
  onResetView: () => void;
  onBack: () => void;
};

const ZOOM_STEP = 0.1;

export default function TopBar({
  zoom,
  cellPx,
  backend,
  placedAgents,
  tick,
  playing,
  stepping,
  onZoomChange,
  onCellPxChange,
  onTogglePlay,
  onRestart,
  onResetView,
  onBack,
}: TopBarProps) {
  const [cellDraft, setCellDraft] = useState(String(cellPx));
  const zoomPercent = Math.round(zoom * 100);
  const simDisabled = backend === null || placedAgents === 0;

  useEffect(() => {
    setCellDraft(String(cellPx));
  }, [cellPx]);

  const commitCellPx = () => {
    const parsed = Number(cellDraft);
    if (Number.isFinite(parsed)) {
      onCellPxChange(parsed);
    } else {
      setCellDraft(String(cellPx));
    }
  };

  return (
    <header className="navbar bg-base-200 h-12 min-h-12 gap-2 px-3">
      <div className="navbar-start min-w-0 flex-1 gap-2">
        <button
          type="button"
          className="btn btn-sm btn-ghost px-2"
          aria-label="На главную"
          onClick={onBack}
        >
          ←
        </button>
        <span className="shrink-0 text-base font-semibold tracking-tight">
          agentiki
        </span>
        <span className="truncate text-xs opacity-60">
          tick {tick}
          {placedAgents > 0 ? ` · ${placedAgents} аг.` : ""}
          {backend ? ` · ${backend}` : " · офлайн"}
        </span>
      </div>

      <div className="navbar-center flex-none gap-2">
        <div className="join">
          <button
            type="button"
            className="btn btn-sm join-item px-3"
            disabled={simDisabled || stepping}
            aria-label={playing ? "Пауза" : "Play"}
            onClick={onTogglePlay}
          >
            {playing ? "⏸" : "▶"}
          </button>
          <button
            type="button"
            className="btn btn-sm join-item"
            disabled={simDisabled || stepping}
            onClick={onRestart}
          >
            Рестарт
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
