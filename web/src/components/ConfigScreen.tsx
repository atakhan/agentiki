import { useEffect, useState } from "react";
import {
  DEFAULT_AGENT_COUNT,
  DEFAULT_AGENT_DENSITY,
  DEFAULT_LIFE_RULES,
  saveWorldConfig,
  type LifeRules,
  type WorldConfig,
} from "../api";

const MIN_AGENT_COUNT = 1;
const MAX_AGENT_COUNT = 100_000;
const MIN_AGENT_DENSITY = 1;
const MAX_AGENT_DENSITY = 10;
const INCOME_ORDER_ERROR = "Приток: предатель > оба C > оба D > кооператор";

export const EMPTY_WORLD_CONFIG: WorldConfig = {
  name: "",
  count: DEFAULT_AGENT_COUNT,
  density: DEFAULT_AGENT_DENSITY,
  life: DEFAULT_LIFE_RULES,
};

function incomesOrdered(life: LifeRules): boolean {
  return (
    life.defector > life.bothCooperate &&
    life.bothCooperate > life.bothDefect &&
    life.bothDefect > life.cooperator
  );
}

function RuleField({
  label,
  value,
  min,
  onCommit,
}: {
  label: string;
  value: number;
  min: number;
  onCommit: (value: number) => boolean;
}) {
  const [draft, setDraft] = useState(String(value));

  useEffect(() => {
    setDraft(String(value));
  }, [value]);

  const tryCommit = (raw: string) => {
    const parsed = Number(raw);
    if (raw.trim() !== "" && Number.isInteger(parsed) && parsed >= min) {
      return onCommit(parsed);
    }
    return false;
  };

  return (
    <label className="flex flex-col gap-1">
      <span className="label p-0 text-xs">{label}</span>
      <input
        type="number"
        min={min}
        step={1}
        value={draft}
        className="input input-sm w-full"
        aria-label={label}
        onChange={(event) => {
          const next = event.target.value;
          setDraft(next);
          tryCommit(next);
        }}
        onBlur={() => {
          if (!tryCommit(draft)) {
            setDraft(String(value));
            onCommit(value);
          }
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.currentTarget.blur();
          }
        }}
      />
    </label>
  );
}

type ConfigScreenProps = {
  initial: WorldConfig;
  offline: boolean;
  starting: boolean;
  startError: string | null;
  onBack: () => void;
  onStart: (config: WorldConfig) => void;
};

export default function ConfigScreen({
  initial,
  offline,
  starting,
  startError,
  onBack,
  onStart,
}: ConfigScreenProps) {
  const [count, setCount] = useState(initial.count);
  const [countDraft, setCountDraft] = useState(String(initial.count));
  const [density, setDensity] = useState(initial.density);
  const [life, setLife] = useState<LifeRules>(initial.life);
  const [lifeError, setLifeError] = useState<string | null>(null);
  const [knownName, setKnownName] = useState(initial.name);
  const [saveOpen, setSaveOpen] = useState(false);
  const [nameDraft, setNameDraft] = useState(initial.name);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [savedNote, setSavedNote] = useState<string | null>(null);

  useEffect(() => {
    setCount(initial.count);
    setCountDraft(String(initial.count));
    setDensity(initial.density);
    setLife(initial.life);
    setKnownName(initial.name);
    setNameDraft(initial.name);
    setLifeError(null);
    setSaveError(null);
    setSavedNote(null);
  }, [initial]);

  const commitLife = (key: keyof LifeRules, value: number) => {
    const next = { ...life, [key]: value };
    if (!incomesOrdered(next)) {
      setLifeError(INCOME_ORDER_ERROR);
      return false;
    }
    setLifeError(null);
    setLife(next);
    return true;
  };

  const commitCount = (raw: string) => {
    const parsed = Number(raw);
    if (
      raw.trim() !== "" &&
      Number.isInteger(parsed) &&
      parsed >= MIN_AGENT_COUNT &&
      parsed <= MAX_AGENT_COUNT
    ) {
      setCount(parsed);
      return true;
    }
    return false;
  };

  const current = (): WorldConfig => ({
    name: knownName,
    count,
    density,
    life,
  });

  const confirmSave = async () => {
    const name = nameDraft.trim();
    if (!name) {
      setSaveError("Нужно имя мира");
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      const saved = await saveWorldConfig({ ...current(), name });
      setKnownName(saved.name);
      setNameDraft(saved.name);
      setSavedNote(`Сохранено: ${saved.name}`);
      setSaveOpen(false);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex h-dvh flex-col bg-base-100">
      <header className="navbar bg-base-200 h-12 min-h-12 px-3">
        <button
          type="button"
          className="btn btn-sm btn-ghost px-2"
          aria-label="На главную"
          onClick={onBack}
        >
          ←
        </button>
        <span className="text-base font-semibold">
          {knownName ? knownName : "Новый мир"}
        </span>
      </header>
      <div className="mx-auto w-full max-w-lg flex-1 overflow-y-auto p-4">
        <div className="flex flex-col gap-4 rounded-box bg-base-200 p-4 shadow-lg">
          <label className="flex flex-col gap-1">
            <span className="label p-0 text-xs">Количество агентов</span>
            <input
              type="number"
              min={MIN_AGENT_COUNT}
              max={MAX_AGENT_COUNT}
              step={1}
              value={countDraft}
              className="input input-sm w-full"
              aria-label="Количество агентов"
              onChange={(event) => {
                const next = event.target.value;
                setCountDraft(next);
                commitCount(next);
              }}
              onBlur={() => {
                if (!commitCount(countDraft)) {
                  setCountDraft(String(count));
                }
              }}
            />
          </label>

          <div>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="label p-0">Плотность</span>
              <span className="font-mono opacity-70">{Math.round(density)}</span>
            </div>
            <input
              type="range"
              min={MIN_AGENT_DENSITY}
              max={MAX_AGENT_DENSITY}
              step={1}
              value={Math.round(density)}
              className="range range-xs w-full"
              aria-label="Расстояние до ближайшего агента"
              onChange={(event) => setDensity(Number(event.target.value))}
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <p className="text-xs opacity-60 sm:col-span-2">Конфиги жизни · траты</p>
            <RuleField label="Старт" min={1} value={life.startHp} onCommit={(value) => commitLife("startHp", value)} />
            <RuleField label="Ход" min={0} value={life.moveCost} onCommit={(value) => commitLife("moveCost", value)} />
            <RuleField label="Стояние" min={0} value={life.stayCost} onCommit={(value) => commitLife("stayCost", value)} />
            <RuleField label="Решение" min={0} value={life.decisionCost} onCommit={(value) => commitLife("decisionCost", value)} />
            <RuleField label="Раунд" min={0} value={life.roundCost} onCommit={(value) => commitLife("roundCost", value)} />
            <p className="text-xs opacity-60 sm:col-span-2">Приток</p>
            <RuleField label="Оба сотрудничают" min={0} value={life.bothCooperate} onCommit={(value) => commitLife("bothCooperate", value)} />
            <RuleField label="Оба предают" min={0} value={life.bothDefect} onCommit={(value) => commitLife("bothDefect", value)} />
            <RuleField label="Предатель" min={0} value={life.defector} onCommit={(value) => commitLife("defector", value)} />
            <RuleField label="Кооператор" min={0} value={life.cooperator} onCommit={(value) => commitLife("cooperator", value)} />
          </div>

          {lifeError ? <p className="text-xs text-error">{lifeError}</p> : null}
          {startError ? <p className="text-xs text-error">{startError}</p> : null}
          {savedNote ? <p className="text-xs opacity-70">{savedNote}</p> : null}

          <div className="flex gap-2">
            <button
              type="button"
              className="btn btn-primary flex-1"
              disabled={offline || starting || lifeError !== null}
              onClick={() => onStart(current())}
            >
              {starting ? <span className="loading loading-spinner loading-xs" /> : "Старт"}
            </button>
            <button
              type="button"
              className="btn flex-1"
              disabled={offline || lifeError !== null}
              onClick={() => {
                setNameDraft(knownName);
                setSaveError(null);
                setSaveOpen(true);
              }}
            >
              Сохранить конфиги
            </button>
          </div>
        </div>
      </div>

      {saveOpen ? (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-sm rounded-box bg-base-200 p-4 shadow-lg">
            <h2 className="mb-2 font-medium">Имя мира</h2>
            <input
              type="text"
              maxLength={80}
              value={nameDraft}
              className="input input-sm w-full"
              aria-label="Имя мира"
              onChange={(event) => setNameDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void confirmSave();
                }
              }}
            />
            {saveError ? <p className="mt-2 text-xs text-error">{saveError}</p> : null}
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                className="btn btn-sm flex-1"
                onClick={() => setSaveOpen(false)}
              >
                Отмена
              </button>
              <button
                type="button"
                className="btn btn-primary btn-sm flex-1"
                disabled={saving || nameDraft.trim() === ""}
                onClick={() => void confirmSave()}
              >
                {saving ? <span className="loading loading-spinner loading-xs" /> : "Сохранить"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
