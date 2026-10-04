type LoadScreenProps = {
  names: string[];
  loading: boolean;
  error: string | null;
  onBack: () => void;
  onPick: (name: string) => void;
};

export default function LoadScreen({
  names,
  loading,
  error,
  onBack,
  onPick,
}: LoadScreenProps) {
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
        <span className="text-base font-semibold">Загрузить мир</span>
      </header>
      <div className="mx-auto flex w-full max-w-md flex-1 flex-col gap-2 overflow-y-auto p-4">
        {loading ? <p className="text-sm opacity-60">Загрузка…</p> : null}
        {error ? <p className="text-sm text-error">{error}</p> : null}
        {!loading && !error && names.length === 0 ? (
          <p className="text-sm opacity-60">Нет сохранённых миров</p>
        ) : null}
        {names.map((name) => (
          <button
            key={name}
            type="button"
            className="btn btn-block justify-start"
            onClick={() => onPick(name)}
          >
            {name}
          </button>
        ))}
      </div>
    </div>
  );
}
