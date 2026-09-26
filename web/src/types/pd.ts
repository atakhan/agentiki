export type PDRoundEvent = {
  meeting_id: number;
  agent_a_id: number;
  agent_b_id: number;
  round_number: number;
  choice_a: "COOPERATE" | "DEFECT";
  choice_b: "COOPERATE" | "DEFECT";
  payoff_a: number;
  payoff_b: number;
  continue_a: "CONTINUE" | "LEAVE";
  continue_b: "CONTINUE" | "LEAVE";
  meeting_finished: boolean;
  tick: number;
};
