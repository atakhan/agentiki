export type VisibleAgentObs = {
  agent_id: number;
  relative_x: number;
  relative_y: number;
};

export type ObservationResponse = {
  observer_id: number;
  vision_radius: number;
  interaction_radius: number;
  visible_agents: VisibleAgentObs[];
};
