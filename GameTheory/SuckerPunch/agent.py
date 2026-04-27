# =============================================================================
# agent.py — Agent
# =============================================================================
# Wraps a player role and strategy with accumulated game history and a
# fitness score. Agents are the unit of selection in the evolutionary
# simulation — strategies that produce higher fitness agents reproduce
# more frequently in the next generation.
#
# Responsibilities:
#   - Hold a player role (P1 or P2) and a Strategy instance
#   - Record win/loss/draw outcomes across many games
#   - Compute a fitness score from that history
#   - Support history reset between evolutionary generations
#   - Support strategy replacement (used by mutation in population.py)
# =============================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from config import Outcome
from options import Player
from strategy import Strategy


@dataclass
class Agent:
    """
    Represents one agent in the evolutionary population.

    Each agent has a fixed role (P1 or P2) and carries a Strategy that
    determines its choices in every game it plays. Results are accumulated
    across all games in a generation and converted to a fitness score at
    the end of that generation.

    Attributes:
        player:   the role this agent occupies — P1 or P2
        strategy: the Strategy instance used to make choices each round
        wins:     number of games won this generation
        losses:   number of games lost this generation
        draws:    number of games drawn this generation (cap exhaustion tiebreak)
    """
    player:   Player
    strategy: Strategy
    wins:     int = field(default=0, init=False)
    losses:   int = field(default=0, init=False)
    draws:    int = field(default=0, init=False)

    # ------------------------------------------------------------------
    # Result recording
    # ------------------------------------------------------------------

    def record_result(self, outcome: Outcome) -> None:
        """
        Records the result of one completed game for this agent.

        Interprets the outcome relative to this agent's role:
        - P1_WINS → win  for P1 agents, loss for P2 agents
        - P2_WINS → loss for P1 agents, win  for P2 agents

        Args:
            outcome: the concrete final Outcome of the completed game.
                    Must be P1_WINS or P2_WINS — SUBGAME and PROBABILISTIC
                    are never final outcomes and should never be passed here.

        Raises:
            ValueError: if an unexpected outcome is passed
        """
        if outcome == Outcome.P1_WINS:
            if self.player == Player.P1:
                self.wins   += 1
            else:
                self.losses += 1

        elif outcome == Outcome.P2_WINS:
            if self.player == Player.P2:
                self.wins   += 1
            else:
                self.losses += 1

        else:
            raise ValueError(
                f"record_result() received unexpected outcome: {outcome}. "
                f"Only P1_WINS and P2_WINS are valid final outcomes."
            )

    # ------------------------------------------------------------------
    # Fitness
    # ------------------------------------------------------------------

    @property
    def games_played(self) -> int:
        """Total number of games recorded this generation."""
        return self.wins + self.losses + self.draws

    @property
    def win_rate(self) -> float:
        """
        Fraction of games won this generation.
        Returns 0.0 if no games have been played yet.
        """
        if self.games_played == 0:
            return 0.0
        return self.wins / self.games_played

    @property
    def fitness(self) -> float:
        """
        Scalar fitness score used by population.py for replicator selection.

        Fitness = win_rate, bounded to [0.0, 1.0].

        This is intentionally simple — win rate is the cleanest measure of
        evolutionary success for this game. The replicator dynamics in
        population.py compares each agent's fitness to the population mean,
        so only relative differences between agents matter, not absolute scale.

        If no games have been played, returns 0.0. population.py handles
        the edge case of all-zero fitness by falling back to uniform sampling.
        """
        return self.win_rate

    # ------------------------------------------------------------------
    # Generation reset
    # ------------------------------------------------------------------

    def reset_history(self) -> None:
        """
        Clears win/loss/draw counters at the start of a new generation.
        Strategy is preserved — only the accumulated results are wiped.
        Called by population.py at the beginning of each generation.
        """
        self.wins   = 0
        self.losses = 0
        self.draws  = 0

    # ------------------------------------------------------------------
    # Strategy replacement (mutation)
    # ------------------------------------------------------------------

    def replace_strategy(self, new_strategy: Strategy) -> None:
        """
        Replaces this agent's strategy with a new one.
        Called by population.py during the mutation step.

        The agent's accumulated history is NOT reset here — mutation happens
        after results are recorded and before the next generation begins,
        so history is irrelevant at this point. reset_history() is called
        separately at the start of each new generation.

        Args:
            new_strategy: the Strategy to assign to this agent
        """
        self.strategy = new_strategy

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def strategy_name(self) -> str:
        """
        Returns a human-readable name for this agent's current strategy.
        Used by population.py for tracking strategy frequency history
        and by analysis.py for reporting results.
        """
        return repr(self.strategy)

    def summary(self) -> dict:
        """
        Returns a snapshot of this agent's current state as a dictionary.
        Used for logging and analysis export.

        Returns:
            dict with keys: player, strategy, wins, losses, draws,
                            games_played, win_rate, fitness
        """
        return {
            "player":       self.player.value,
            "strategy":     self.strategy_name(),
            "wins":         self.wins,
            "losses":       self.losses,
            "draws":        self.draws,
            "games_played": self.games_played,
            "win_rate":     round(self.win_rate, 4),
            "fitness":      round(self.fitness, 4),
        }

    def __repr__(self) -> str:
        return (
            f"Agent("
            f"player={self.player.value}, "
            f"strategy={self.strategy_name()}, "
            f"W/L/D={self.wins}/{self.losses}/{self.draws}, "
            f"fitness={self.fitness:.3f}"
            f")"
        )