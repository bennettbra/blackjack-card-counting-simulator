"""Bet sizing policies for blackjack simulations."""

import math
from dataclasses import dataclass


# Each entry is (minimum integer true count, number of betting units).
# Counts below +1 use the minimum of one unit.
DEFAULT_BET_SPREAD = (
    (1, 2),
    (2, 4),
    (3, 8),
    (4, 12),
)


@dataclass(frozen=True)
class BetRamp:
    """Convert a floored true count into a wager.

    ``thresholds`` contains ``(minimum_true_count, units)`` entries. For
    example, ``((1, 2), (2, 4))`` bets two units at true count +1 and four
    units at +2 or higher. Counts below the first threshold use
    ``minimum_units``.
    """

    base_bet: float = 10
    thresholds: tuple = DEFAULT_BET_SPREAD
    minimum_units: float = 1

    def __post_init__(self):
        if not math.isfinite(self.base_bet) or self.base_bet <= 0:
            raise ValueError("base_bet must be a positive, finite number.")
        if not math.isfinite(self.minimum_units) or self.minimum_units <= 0:
            raise ValueError("minimum_units must be a positive, finite number.")

        try:
            normalized_thresholds = tuple(
                (float(threshold), float(units))
                for threshold, units in self.thresholds
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "thresholds must contain (minimum_true_count, units) pairs."
            ) from exc

        if any(
            not math.isfinite(threshold)
            or not math.isfinite(units)
            or units <= 0
            for threshold, units in normalized_thresholds
        ):
            raise ValueError("Bet-ramp thresholds must be finite and units positive.")

        threshold_values = [threshold for threshold, _ in normalized_thresholds]
        if len(threshold_values) != len(set(threshold_values)):
            raise ValueError("Bet-ramp thresholds cannot be repeated.")

        object.__setattr__(
            self,
            "thresholds",
            tuple(sorted(normalized_thresholds)),
        )

    def units_for(self, true_count):
        """Return betting units for a true count, floored to an integer."""
        if not math.isfinite(true_count):
            raise ValueError("true_count must be finite.")

        count_bucket = math.floor(true_count)
        units = self.minimum_units

        for threshold, threshold_units in self.thresholds:
            if count_bucket < threshold:
                break
            units = threshold_units

        return units

    def bet_for(self, true_count):
        """Return the wager for a true count."""
        return self.base_bet * self.units_for(true_count)


def calculate_true_count(running_count, cards_remaining):
    """Normalize a Hi-Lo running count by the decks remaining."""
    if cards_remaining <= 0:
        raise ValueError("cards_remaining must be greater than zero.")

    decks_remaining = cards_remaining / 52
    return running_count / decks_remaining
