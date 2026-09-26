export type Agent = {
  id: number;
  x: number;
  y: number;
  pos_x: number;
  pos_y: number;
  score: number;
  state: "FREE" | "IN_MEETING";
  meeting_id: number | null;
};

export type AgentsResponse = {
  count: number;
  agents: Agent[];
};
