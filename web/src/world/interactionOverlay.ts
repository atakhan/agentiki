import type { InteractionEvent } from "../types/interaction";
import type { PDRoundEvent } from "../types/pd";

const FADE_MS = 1500;

type TimedInteraction = InteractionEvent & { shownAt: number };
type TimedPDRound = PDRoundEvent & { shownAt: number };

export class InteractionOverlay {
  private items: TimedInteraction[] = [];
  private pdRounds: TimedPDRound[] = [];

  add(events: readonly InteractionEvent[], now: number = performance.now()): void {
    for (const event of events) {
      this.items.push({ ...event, shownAt: now });
    }
  }

  addPdRounds(
    events: readonly PDRoundEvent[],
    now: number = performance.now(),
  ): void {
    for (const event of events) {
      this.pdRounds.push({ ...event, shownAt: now });
    }
  }

  getActive(now: number = performance.now()): TimedInteraction[] {
    this.items = this.items.filter((item) => now - item.shownAt < FADE_MS);
    return this.items;
  }

  getActivePdRounds(now: number = performance.now()): TimedPDRound[] {
    this.pdRounds = this.pdRounds.filter((item) => now - item.shownAt < FADE_MS);
    return this.pdRounds;
  }

  isActive(now: number = performance.now()): boolean {
    return this.getActive(now).length > 0 || this.getActivePdRounds(now).length > 0;
  }

  clear(): void {
    this.items = [];
    this.pdRounds = [];
  }
}
