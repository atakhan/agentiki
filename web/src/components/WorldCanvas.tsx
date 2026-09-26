import { useCallback, useEffect, useRef } from "react";
import {
  clampZoom,
  screenToWorld,
  type Camera,
} from "../world/camera";
import type { Agent } from "../types/agent";
import type { VisibleAgentObs } from "../types/observation";
import { AgentAnimationController } from "../world/agentAnimation";
import { InteractionOverlay } from "../world/interactionOverlay";
import { renderAgents } from "../world/renderAgents";
import { renderGrid } from "../world/renderGrid";
import { renderInteractions } from "../world/renderInteractions";
import { renderVisionDebug } from "../world/renderVisionDebug";

type WorldCanvasProps = {
  camera: Camera;
  cellPx: number;
  agents: readonly Agent[];
  selectedAgentId: number | null;
  visionRadius: number;
  interactionRadius: number;
  visibleAgents: readonly VisibleAgentObs[];
  interactionOverlay: InteractionOverlay;
  interactionPulse: number;
  onCameraChange: (camera: Camera) => void;
  onHoverCell: (cell: { x: number; y: number } | null) => void;
  onSelectAgent: (agentId: number | null) => void;
};

const DRAG_THRESHOLD_PX = 5;

export default function WorldCanvas({
  camera,
  cellPx,
  agents,
  selectedAgentId,
  visionRadius,
  interactionRadius,
  visibleAgents,
  interactionOverlay,
  interactionPulse,
  onCameraChange,
  onHoverCell,
  onSelectAgent,
}: WorldCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const cameraRef = useRef(camera);
  const cellPxRef = useRef(cellPx);
  const agentsRef = useRef(agents);
  const selectedAgentIdRef = useRef(selectedAgentId);
  const visionRadiusRef = useRef(visionRadius);
  const interactionRadiusRef = useRef(interactionRadius);
  const visibleAgentsRef = useRef(visibleAgents);
  const animRef = useRef(new AgentAnimationController());
  const interactionOverlayRef = useRef(interactionOverlay);
  const visualMapRef = useRef(new Map<number, { worldX: number; worldY: number }>());
  const rafRef = useRef<number | null>(null);
  const dragRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    lastX: number;
    lastY: number;
  } | null>(null);
  const onCameraChangeRef = useRef(onCameraChange);
  const onHoverCellRef = useRef(onHoverCell);
  const onSelectAgentRef = useRef(onSelectAgent);

  cameraRef.current = camera;
  cellPxRef.current = cellPx;
  agentsRef.current = agents;
  selectedAgentIdRef.current = selectedAgentId;
  visionRadiusRef.current = visionRadius;
  interactionRadiusRef.current = interactionRadius;
  visibleAgentsRef.current = visibleAgents;
  interactionOverlayRef.current = interactionOverlay;
  onCameraChangeRef.current = onCameraChange;
  onHoverCellRef.current = onHoverCell;
  onSelectAgentRef.current = onSelectAgent;

  const stopAnimationLoop = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const paint = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return;
    }
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const pixelW = Math.max(1, Math.floor(width * dpr));
    const pixelH = Math.max(1, Math.floor(height * dpr));
    if (canvas.width !== pixelW || canvas.height !== pixelH) {
      canvas.width = pixelW;
      canvas.height = pixelH;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    renderGrid(ctx, {
      width,
      height,
      camera: cameraRef.current,
      cellPx: cellPxRef.current,
    });

    const visuals = animRef.current.getVisuals(
      agentsRef.current,
      performance.now(),
    );
    const visualMap = new Map<number, { worldX: number; worldY: number }>();
    for (const visual of visuals) {
      visualMap.set(visual.id, { worldX: visual.worldX, worldY: visual.worldY });
    }
    visualMapRef.current = visualMap;

    const selectedId = selectedAgentIdRef.current;
    const selectedAgent =
      selectedId === null
        ? null
        : agentsRef.current.find((agent) => agent.id === selectedId) ?? null;

    if (selectedAgent) {
      renderVisionDebug(ctx, {
        width,
        height,
        camera: cameraRef.current,
        cellPx: cellPxRef.current,
        selectedAgent,
        visionRadius: visionRadiusRef.current,
        interactionRadius: interactionRadiusRef.current,
        visibleAgents: visibleAgentsRef.current,
        agentVisuals: visualMap,
      });
    }

    renderAgents(ctx, {
      width,
      height,
      camera: cameraRef.current,
      cellPx: cellPxRef.current,
      agents: visuals,
    });

    const now = performance.now();
    const activeInteractions = interactionOverlayRef.current.getActive(now);
    const activePdRounds = interactionOverlayRef.current.getActivePdRounds(now);
    if (activeInteractions.length > 0 || activePdRounds.length > 0) {
      renderInteractions(ctx, {
        width,
        height,
        camera: cameraRef.current,
        cellPx: cellPxRef.current,
        interactions: activeInteractions,
        pdRounds: activePdRounds,
        agentPositions: visualMap,
        now,
      });
    }
  }, []);

  const startAnimationLoop = useCallback(() => {
    if (rafRef.current !== null) {
      return;
    }
    const frame = () => {
      paint();
      if (
        animRef.current.isAnimating() ||
        interactionOverlayRef.current.isActive()
      ) {
        rafRef.current = requestAnimationFrame(frame);
      } else {
        rafRef.current = null;
      }
    };
    rafRef.current = requestAnimationFrame(frame);
  }, [paint]);

  useEffect(() => {
    animRef.current.syncAgents(agents);
    paint();
    if (
      animRef.current.isAnimating() ||
      interactionOverlayRef.current.isActive()
    ) {
      startAnimationLoop();
    }
  }, [agents, paint, startAnimationLoop, interactionPulse]);

  useEffect(() => {
    paint();
  }, [
    paint,
    camera,
    cellPx,
    selectedAgentId,
    visibleAgents,
    visionRadius,
    interactionRadius,
    interactionPulse,
  ]);

  useEffect(() => stopAnimationLoop, [stopAnimationLoop]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const observer = new ResizeObserver(() => paint());
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [paint]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const cam = cameraRef.current;
      const cellPxNow = cellPxRef.current;
      const world = screenToWorld(
        event.clientX - rect.left,
        event.clientY - rect.top,
        rect.width,
        rect.height,
        cam,
        cellPxNow,
      );
      const factor = event.deltaY < 0 ? 1.1 : 1 / 1.1;
      const nextZoom = clampZoom(cam.zoom * factor);
      const nextCam: Camera = { ...cam, zoom: nextZoom };
      const worldAfter = screenToWorld(
        event.clientX - rect.left,
        event.clientY - rect.top,
        rect.width,
        rect.height,
        nextCam,
        cellPxNow,
      );
      onCameraChangeRef.current({
        x: cam.x + (world.x - worldAfter.x),
        y: cam.y + (world.y - worldAfter.y),
        zoom: nextZoom,
      });
    };
    canvas.addEventListener("wheel", onWheel, { passive: false });
    return () => canvas.removeEventListener("wheel", onWheel);
  }, []);

  const finishPointer = (event: React.PointerEvent<HTMLCanvasElement>) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) {
      return;
    }

    const moved = Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY);
    dragRef.current = null;

    if (moved < DRAG_THRESHOLD_PX) {
      const canvas = event.currentTarget;
      const rect = canvas.getBoundingClientRect();
      const world = screenToWorld(
        event.clientX - rect.left,
        event.clientY - rect.top,
        rect.width,
        rect.height,
        cameraRef.current,
        cellPxRef.current,
      );
      const cellX = Math.floor(world.x);
      const cellY = Math.floor(world.y);
      const hit = agentsRef.current.find(
        (agent) => agent.x === cellX && agent.y === cellY,
      );
      onSelectAgentRef.current(hit?.id ?? null);
    }
  };

  return (
    <canvas
      ref={canvasRef}
      role="img"
      aria-label="Карта мира"
      tabIndex={0}
      className="block h-full w-full cursor-grab touch-none active:cursor-grabbing"
      onPointerDown={(event) => {
        if (event.button !== 0) {
          return;
        }
        const canvas = event.currentTarget;
        canvas.setPointerCapture(event.pointerId);
        dragRef.current = {
          pointerId: event.pointerId,
          startX: event.clientX,
          startY: event.clientY,
          lastX: event.clientX,
          lastY: event.clientY,
        };
      }}
      onPointerMove={(event) => {
        const canvas = event.currentTarget;
        const rect = canvas.getBoundingClientRect();
        const cam = cameraRef.current;
        const world = screenToWorld(
          event.clientX - rect.left,
          event.clientY - rect.top,
          rect.width,
          rect.height,
          cam,
          cellPxRef.current,
        );
        onHoverCellRef.current({
          x: Math.floor(world.x),
          y: Math.floor(world.y),
        });

        const drag = dragRef.current;
        if (!drag || drag.pointerId !== event.pointerId) {
          return;
        }
        const size = cellPxRef.current * cam.zoom;
        const dx = event.clientX - drag.lastX;
        const dy = event.clientY - drag.lastY;
        drag.lastX = event.clientX;
        drag.lastY = event.clientY;
        onCameraChangeRef.current({
          ...cam,
          x: cam.x - dx / size,
          y: cam.y - dy / size,
        });
      }}
      onPointerUp={finishPointer}
      onPointerCancel={finishPointer}
      onPointerLeave={() => {
        if (!dragRef.current) {
          onHoverCellRef.current(null);
        }
      }}
    />
  );
}
