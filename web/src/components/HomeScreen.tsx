type HomeScreenProps = {
  offline: boolean;
  onNew: () => void;
  onLoad: () => void;
};

export default function HomeScreen({ offline, onNew, onLoad }: HomeScreenProps) {
  return (
    <div className="flex h-dvh items-center justify-center bg-base-100 px-4">
      <div className="flex w-full max-w-sm flex-col gap-3 rounded-box bg-base-200 p-6 shadow-lg">
        <h1 className="text-xl font-semibold tracking-tight">agentiki</h1>
        <p className="text-xs opacity-60">
          {offline ? "сервер недоступен" : "мир ещё не запущен"}
        </p>
        <button
          type="button"
          className="btn btn-primary"
          disabled={offline}
          onClick={onNew}
        >
          Новый мир
        </button>
        <button type="button" className="btn" disabled={offline} onClick={onLoad}>
          Загрузить мир
        </button>
      </div>
    </div>
  );
}
