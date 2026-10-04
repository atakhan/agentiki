import { useCallback, useEffect, useRef, useState } from "react";
import ConfigScreen, { EMPTY_WORLD_CONFIG } from "./components/ConfigScreen";
import HomeScreen from "./components/HomeScreen";
import LoadScreen from "./components/LoadScreen";
import TopBar from "./components/TopBar";
import WorldCanvas from "./components/WorldCanvas";
import {
  DEFAULT_LIFE_RULES,
  fetchObservation,
  fetchWorld,
  generateAgents,
  listWorldConfigs,
  loadWorldConfig,
  resetWorld,
  stepWorld,
  type LifeRules,
  type WorldConfig,
} from "./api";
import type { Agent } from "./types/agent";
import type { VisibleAgentObs } from "./types/observation";
import {
  clampCellPx,
  clampZoom,
  DEFAULT_CELL_PX,
  type Camera,
} from "./world/camera";
import { InteractionOverlay } from "./world/interactionOverlay";

const ORIGIN_CAMERA: Camera = { x: 0, y: 0, zoom: 1 };
const PLAY_INTERVAL_MS = 1000;

type Screen = "home" | "load" | "config" | "sim";

export default function App() {
  const [screen, setScreen] = useState<Screen>("home");
  const [camera, setCamera] = useState<Camera>(ORIGIN_CAMERA);
  const [cellPx, setCellPx] = useState(DEFAULT_CELL_PX);
  const [backend, setBackend] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [lifeRules, setLifeRules] = useState<LifeRules>(DEFAULT_LIFE_RULES);
  const sessionConfigRef = useRef<WorldConfig | null>(null);
  const [configDraft, setConfigDraft] = useState<WorldConfig>(EMPTY_WORLD_CONFIG);
  const [configKey, setConfigKey] = useState(0);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const [loadNames, setLoadNames] = useState<string[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadingList, setLoadingList] = useState(false);
  const [stepping, setStepping] = useState(false);
  const [playing, setPlaying] = useState(false);
  const steppingRef = useRef(false);
  const [visionRadius, setVisionRadius] = useState(3);
  const [interactionRadius, setInteractionRadius] = useState(1);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [visibleAgents, setVisibleAgents] = useState<VisibleAgentObs[]>([]);
  const [hoverCell, setHoverCell] = useState<{ x: number; y: number } | null>(null);
  const [lastStepPdRounds, setLastStepPdRounds] = useState(0);
  const [interactionPulse, setInteractionPulse] = useState(0);
  const interactionOverlayRef = useRef(new InteractionOverlay());

  useEffect(() => {
    let cancelled = false;
    fetchWorld()
      .then((world) => {
        if (cancelled) {
          return;
        }
        setBackend(world.backend);
        setCellPx(clampCellPx(world.default_cell_px));
      })
      .catch(() => {
        if (!cancelled) {
          setBackend(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const refreshObservation = useCallback(async (agentId: number | null) => {
    if (agentId === null) {
      setVisibleAgents([]);
      return;
    }
    try {
      const observation = await fetchObservation(agentId);
      setVisibleAgents(observation.visible_agents);
      setVisionRadius(observation.vision_radius);
      setInteractionRadius(observation.interaction_radius);
    } catch (error) {
      console.error(error);
      setVisibleAgents([]);
    }
  }, []);

  useEffect(() => {
    if (screen !== "sim") {
      return;
    }
    void refreshObservation(selectedAgentId);
  }, [screen, selectedAgentId, agents, tick, refreshObservation]);

  const handleStep = useCallback(async (n: number) => {
    if (steppingRef.current) {
      return false;
    }
    steppingRef.current = true;
    setStepping(true);
    try {
      const result = await stepWorld(n, lifeRules);
      setTick(result.world.tick);
      setAgents(result.agents.agents);
      setLastStepPdRounds(result.pd_rounds.length);
      interactionOverlayRef.current.add(result.interactions);
      interactionOverlayRef.current.addPdRounds(result.pd_rounds);
      setInteractionPulse((value) => value + 1);
      return true;
    } catch (error) {
      console.error(error);
      setPlaying(false);
      return false;
    } finally {
      steppingRef.current = false;
      setStepping(false);
    }
  }, [lifeRules]);

  useEffect(() => {
    if (!playing || backend === null || agents.length === 0 || screen !== "sim") {
      return;
    }

    let cancelled = false;

    const runTick = () => {
      if (cancelled || steppingRef.current) {
        return;
      }
      void handleStep(1);
    };

    runTick();
    const intervalId = window.setInterval(runTick, PLAY_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [playing, backend, agents.length, handleStep, screen]);

  const openNew = () => {
    setPlaying(false);
    setStartError(null);
    setConfigDraft(EMPTY_WORLD_CONFIG);
    setConfigKey((value) => value + 1);
    setScreen("config");
  };

  const openLoad = async () => {
    setPlaying(false);
    setLoadError(null);
    setLoadingList(true);
    setScreen("load");
    try {
      setLoadNames(await listWorldConfigs());
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Не удалось загрузить список");
      setLoadNames([]);
    } finally {
      setLoadingList(false);
    }
  };

  const openSaved = async (name: string) => {
    setStartError(null);
    try {
      const loaded = await loadWorldConfig(name);
      setConfigDraft(loaded);
      setConfigKey((value) => value + 1);
      setScreen("config");
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Не удалось открыть мир");
    }
  };

  const handleStart = async (config: WorldConfig) => {
    setStarting(true);
    setStartError(null);
    setPlaying(false);
    setSelectedAgentId(null);
    try {
      const world = await resetWorld();
      const result = await generateAgents(config.count, config.density, config.life);
      setBackend(world.backend);
      setTick(0);
      setAgents(result.agents);
      setLifeRules(config.life);
      sessionConfigRef.current = config;
      setLastStepPdRounds(0);
      interactionOverlayRef.current = new InteractionOverlay();
      setCamera(ORIGIN_CAMERA);
      setScreen("sim");
      const after = await fetchWorld();
      setTick(after.tick);
    } catch (error) {
      setStartError(error instanceof Error ? error.message : "Не удалось запустить мир");
    } finally {
      setStarting(false);
    }
  };

  const goHome = () => {
    setPlaying(false);
    setScreen("home");
  };

  const handleRestart = async () => {
    const config = sessionConfigRef.current;
    if (config === null || steppingRef.current) {
      return;
    }
    setPlaying(false);
    steppingRef.current = true;
    setStepping(true);
    setSelectedAgentId(null);
    try {
      await resetWorld();
      const result = await generateAgents(config.count, config.density, config.life);
      setAgents(result.agents);
      setLifeRules(config.life);
      setLastStepPdRounds(0);
      interactionOverlayRef.current = new InteractionOverlay();
      setInteractionPulse((value) => value + 1);
      const after = await fetchWorld();
      setTick(after.tick);
    } catch (error) {
      console.error(error);
    } finally {
      steppingRef.current = false;
      setStepping(false);
    }
  };

  if (screen === "home") {
    return <HomeScreen offline={backend === null} onNew={openNew} onLoad={() => void openLoad()} />;
  }

  if (screen === "load") {
    return (
      <LoadScreen
        names={loadNames}
        loading={loadingList}
        error={loadError}
        onBack={goHome}
        onPick={(name) => void openSaved(name)}
      />
    );
  }

  if (screen === "config") {
    return (
      <ConfigScreen
        key={configKey}
        initial={configDraft}
        offline={backend === null}
        starting={starting}
        startError={startError}
        onBack={goHome}
        onStart={(config) => void handleStart(config)}
      />
    );
  }

  const cellLabel = hoverCell ?? {
    x: Math.floor(camera.x),
    y: Math.floor(camera.y),
  };

  return (
    <div className="flex h-dvh flex-col">
      <TopBar
        zoom={camera.zoom}
        cellPx={cellPx}
        backend={backend}
        placedAgents={agents.length}
        tick={tick}
        playing={playing}
        stepping={stepping}
        onZoomChange={(zoom) =>
          setCamera((current) => ({ ...current, zoom: clampZoom(zoom) }))
        }
        onCellPxChange={(px) => {
          if (Number.isFinite(px)) {
            setCellPx(clampCellPx(px));
          }
        }}
        onTogglePlay={() => setPlaying((current) => !current)}
        onRestart={() => void handleRestart()}
        onResetView={() => {
          setCamera(ORIGIN_CAMERA);
          setHoverCell(null);
        }}
        onBack={goHome}
      />
      <div className="relative min-h-0 flex-1">
        <WorldCanvas
          camera={camera}
          cellPx={cellPx}
          agents={agents}
          selectedAgentId={selectedAgentId}
          visionRadius={visionRadius}
          interactionRadius={interactionRadius}
          visibleAgents={visibleAgents}
          interactionOverlay={interactionOverlayRef.current}
          interactionPulse={interactionPulse}
          onCameraChange={setCamera}
          onHoverCell={setHoverCell}
          onSelectAgent={setSelectedAgentId}
        />
        <div className="toast toast-bottom toast-start pointer-events-none z-10">
          {selectedAgentId !== null ? (
            <div className="rounded-box bg-base-200/90 px-3 py-2 text-xs shadow-lg">
              <div className="font-medium">
                Агент #{selectedAgentId}
                {agents.find((agent) => agent.id === selectedAgentId)?.state ===
                "IN_MEETING"
                  ? " · во встрече"
                  : ""}
              </div>
              <div className="opacity-70">
                жизнь{" "}
                {agents.find((agent) => agent.id === selectedAgentId)?.hp ?? 0}{" "}
                · tick {tick} · PD {lastStepPdRounds} · видит{" "}
                {visibleAgents.length} · зрение {visionRadius} · взаимодействие{" "}
                {interactionRadius}
              </div>
              <div className="mt-1 flex gap-3 text-[10px] opacity-60">
                <span className="text-[#4a7fd4]">■ видимые</span>
                <span className="text-[#2ea043]">■ взаимодействие</span>
              </div>
            </div>
          ) : null}
          <span className="badge badge-sm font-mono">
            {cellLabel.x}, {cellLabel.y}
          </span>
        </div>
      </div>
    </div>
  );
}
