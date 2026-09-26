import { useCallback, useEffect, useRef, useState } from "react";
import TopBar from "./components/TopBar";
import WorldCanvas from "./components/WorldCanvas";
import {
  fetchAgents,
  fetchObservation,
  fetchWorld,
  generateAgents,
  stepWorld,
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
const DEFAULT_AGENT_COUNT = 100;
const DEFAULT_AGENT_DENSITY = 1.0;
const PLAY_INTERVAL_MS = 1000;

export default function App() {
  const [camera, setCamera] = useState<Camera>(ORIGIN_CAMERA);
  const [cellPx, setCellPx] = useState(DEFAULT_CELL_PX);
  const [backend, setBackend] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentCount, setAgentCount] = useState(DEFAULT_AGENT_COUNT);
  const [agentDensity, setAgentDensity] = useState(DEFAULT_AGENT_DENSITY);
  const [generating, setGenerating] = useState(false);
  const [stepping, setStepping] = useState(false);
  const [playing, setPlaying] = useState(false);
  const steppingRef = useRef(false);
  const [visionRadius, setVisionRadius] = useState(3);
  const [interactionRadius, setInteractionRadius] = useState(1);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [visibleAgents, setVisibleAgents] = useState<VisibleAgentObs[]>([]);
  const [hoverCell, setHoverCell] = useState<{ x: number; y: number } | null>(
    null,
  );
  const [lastStepInteractions, setLastStepInteractions] = useState(0);
  const [lastStepPdRounds, setLastStepPdRounds] = useState(0);
  const [interactionPulse, setInteractionPulse] = useState(0);
  const interactionOverlayRef = useRef(new InteractionOverlay());

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchWorld(), fetchAgents()])
      .then(([world, agentState]) => {
        if (cancelled) {
          return;
        }
        setBackend(world.backend);
        setCellPx(clampCellPx(world.default_cell_px));
        setTick(world.tick);
        setVisionRadius(world.vision_radius);
        setInteractionRadius(world.interaction_radius);
        setAgents(agentState.agents);
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
    void refreshObservation(selectedAgentId);
  }, [selectedAgentId, agents, tick, refreshObservation]);

  const handleGenerateAgents = useCallback(async () => {
    setPlaying(false);
    setSelectedAgentId(null);
    setGenerating(true);
    try {
      const result = await generateAgents(agentCount, agentDensity);
      setAgents(result.agents);
      const world = await fetchWorld();
      setTick(world.tick);
    } catch (error) {
      console.error(error);
    } finally {
      setGenerating(false);
    }
  }, [agentCount, agentDensity]);

  const handleStep = useCallback(async (n: number) => {
    if (steppingRef.current) {
      return false;
    }
    steppingRef.current = true;
    setStepping(true);
    try {
      const result = await stepWorld(n);
      setTick(result.world.tick);
      setAgents(result.agents.agents);
      setLastStepInteractions(result.interactions.length);
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
  }, []);

  useEffect(() => {
    if (!playing || backend === null || agents.length === 0) {
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
  }, [playing, backend, agents.length, handleStep]);

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
        agentCount={agentCount}
        agentDensity={agentDensity}
        placedAgents={agents.length}
        tick={tick}
        lastStepInteractions={lastStepInteractions}
        lastStepPdRounds={lastStepPdRounds}
        generating={generating}
        stepping={stepping}
        playing={playing}
        onZoomChange={(zoom) =>
          setCamera((current) => ({ ...current, zoom: clampZoom(zoom) }))
        }
        onCellPxChange={(px) => {
          if (Number.isFinite(px)) {
            setCellPx(clampCellPx(px));
          }
        }}
        onAgentCountChange={setAgentCount}
        onAgentDensityChange={setAgentDensity}
        onGenerateAgents={handleGenerateAgents}
        onStep={handleStep}
        onTogglePlay={() => setPlaying((current) => !current)}
        onResetView={() => {
          setCamera(ORIGIN_CAMERA);
          setHoverCell(null);
        }}
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
                score{" "}
                {agents.find((agent) => agent.id === selectedAgentId)?.score ??
                  0}{" "}
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
