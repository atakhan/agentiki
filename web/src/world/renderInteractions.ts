import { screenCellSize, type Camera } from "./camera";
import type { InteractionEvent } from "../types/interaction";
import type { PDRoundEvent } from "../types/pd";

type RenderInteractionsOptions = {
  width: number;
  height: number;
  camera: Camera;
  cellPx: number;
  interactions: readonly (InteractionEvent & { shownAt: number })[];
  pdRounds: readonly (PDRoundEvent & { shownAt: number })[];
  agentPositions: ReadonlyMap<number, { worldX: number; worldY: number }>;
  now: number;
};

const FADE_MS = 1500;

function continueSymbol(choice: "CONTINUE" | "LEAVE"): string {
  return choice === "CONTINUE" ? "↔" : "→";
}

export function renderInteractions(
  ctx: CanvasRenderingContext2D,
  options: RenderInteractionsOptions,
): void {
  const {
    width,
    height,
    camera,
    cellPx,
    interactions,
    pdRounds,
    agentPositions,
    now,
  } = options;

  for (const interaction of interactions) {
    const age = now - interaction.shownAt;
    if (age >= FADE_MS) {
      continue;
    }
    const alpha = 1 - age / FADE_MS;
    const posA = agentPositions.get(interaction.agent_a);
    const posB = agentPositions.get(interaction.agent_b);
    if (!posA || !posB) {
      continue;
    }

    const size = screenCellSize(cellPx, camera.zoom);
    const halfW = width / 2;
    const halfH = height / 2;
    const screenA = {
      x: (posA.worldX - camera.x) * size + halfW,
      y: (posA.worldY - camera.y) * size + halfH,
    };
    const screenB = {
      x: (posB.worldX - camera.x) * size + halfW,
      y: (posB.worldY - camera.y) * size + halfH,
    };

    ctx.save();
    ctx.strokeStyle = `rgba(255, 196, 64, ${alpha * 0.9})`;
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(screenA.x, screenA.y);
    ctx.lineTo(screenB.x, screenB.y);
    ctx.stroke();

    const midX = (screenA.x + screenB.x) / 2;
    const midY = (screenA.y + screenB.y) / 2;
    ctx.fillStyle = `rgba(255, 196, 64, ${alpha})`;
    ctx.beginPath();
    ctx.arc(midX, midY, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  for (const round of pdRounds) {
    const age = now - round.shownAt;
    if (age >= FADE_MS) {
      continue;
    }
    const alpha = 1 - age / FADE_MS;
    const posA = agentPositions.get(round.agent_a_id);
    const posB = agentPositions.get(round.agent_b_id);
    if (!posA || !posB) {
      continue;
    }

    const size = screenCellSize(cellPx, camera.zoom);
    const halfW = width / 2;
    const halfH = height / 2;
    const screenA = {
      x: (posA.worldX - camera.x) * size + halfW,
      y: (posA.worldY - camera.y) * size + halfH,
    };
    const screenB = {
      x: (posB.worldX - camera.x) * size + halfW,
      y: (posB.worldY - camera.y) * size + halfH,
    };
    const midX = (screenA.x + screenB.x) / 2;
    const midY = (screenA.y + screenB.y) / 2 - 12;

    const pdLabel = `${round.choice_a[0]}/${round.choice_b[0]} +${round.payoff_a}/${round.payoff_b}`;
    const stayLabel = `${continueSymbol(round.continue_a)} ${continueSymbol(round.continue_b)}`;
    const endLabel = round.meeting_finished ? " · конец" : "";

    ctx.save();
    ctx.font = "bold 10px monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    const drawOutlinedText = (text: string, x: number, y: number) => {
      ctx.lineWidth = 3;
      ctx.strokeStyle = `rgba(255, 255, 255, ${alpha * 0.85})`;
      ctx.strokeText(text, x, y);
      ctx.fillStyle = `rgba(45, 51, 59, ${alpha})`;
      ctx.fillText(text, x, y);
    };

    drawOutlinedText(pdLabel, midX, midY - 7);
    drawOutlinedText(`${stayLabel}${endLabel}`, midX, midY + 7);

    if (round.meeting_finished) {
      ctx.strokeStyle = `rgba(220, 80, 80, ${alpha * 0.85})`;
      ctx.lineWidth = 2;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(screenA.x, screenA.y);
      ctx.lineTo(screenB.x, screenB.y);
      ctx.stroke();
    }

    ctx.restore();
  }
}
