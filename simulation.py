import random
from collections import defaultdict
from math import floor

from basic_strategy import BasicStrategy
from betting import BetRamp, DEFAULT_BET_SPREAD, calculate_true_count
from blackjack_game import run_game
from shoe import create_shoe
from tracking_count import count_range


def simulate(
    num_rounds,
    flat_bet=10,
    n_decks=4,
    penetration=0.75,
    seed=None,
    bet_spread=None,
):
    """Run basic-strategy rounds and return summary statistics.

    A new round is not started once the cut-card penetration has been reached.
    The current round always finishes before the next shuffle.

    ``flat_bet`` is the size of one betting unit. When ``bet_spread`` is
    omitted, every round uses one unit. Pass threshold/unit pairs such as
    ``DEFAULT_BET_SPREAD`` to vary the wager with the true count.
    """
    if num_rounds < 1:
        raise ValueError("num_rounds must be at least 1.")
    if flat_bet <= 0:
        raise ValueError("flat_bet must be greater than zero.")
    if n_decks < 1:
        raise ValueError("n_decks must be at least 1.")
    if not 0 < penetration < 1:
        raise ValueError("penetration must be between 0 and 1.")

    rng = random.Random(seed)
    cards = create_shoe(n_decks, rng=rng)
    card_index = 0
    running_count = 0
    strategy = BasicStrategy()
    betting = BetRamp(
        base_bet=flat_bet,
        thresholds=() if bet_spread is None else bet_spread,
    )
    cut_cards_remaining = int(len(cards) * (1 - penetration))

    total_profit = 0
    profit_history = [0]
    total_hands = 0
    total_initial_wagered = 0
    shoes_played = 1
    minimum_bet = None
    maximum_bet = None
    count_results = defaultdict(
        lambda: {"rounds": 0, "initial_wagered": 0, "profit": 0}
    )

    for _ in range(num_rounds):
        if len(cards) - card_index <= cut_cards_remaining:
            cards = create_shoe(n_decks, rng=rng)
            card_index = 0
            running_count = 0
            shoes_played += 1

        cards_remaining = len(cards) - card_index
        true_count = calculate_true_count(running_count, cards_remaining)
        true_count_bucket = floor(true_count)
        bet = betting.bet_for(true_count)
        round_start_index = card_index

        result = run_game(
            cards,
            start_index=card_index,
            bet=bet,
            strategy=strategy,
            verbose=False,
        )

        card_index = result.next_card_index
        running_count += count_range(cards[round_start_index:card_index])
        total_profit += result.profit
        profit_history.append(total_profit)
        total_hands += result.hands_played
        total_initial_wagered += bet
        minimum_bet = bet if minimum_bet is None else min(minimum_bet, bet)
        maximum_bet = bet if maximum_bet is None else max(maximum_bet, bet)

        bucket_result = count_results[true_count_bucket]
        bucket_result["rounds"] += 1
        bucket_result["initial_wagered"] += bet
        bucket_result["profit"] += result.profit

    return {
        "rounds": num_rounds,
        "hands": total_hands,
        "shoes": shoes_played,
        "profit": total_profit,
        "profit_per_round": total_profit / num_rounds,
        "total_initial_wagered": total_initial_wagered,
        "average_bet": total_initial_wagered / num_rounds,
        "minimum_bet": minimum_bet,
        "maximum_bet": maximum_bet,
        "count_results": dict(sorted(count_results.items())),
        "profit_history": profit_history,
    }


def plot_profit(profit_history):
    """Plot cumulative profit after each simulated round."""
    if not profit_history:
        raise ValueError("profit_history cannot be empty.")

    import matplotlib.pyplot as plt

    figure, axes = plt.subplots()
    axes.plot(range(len(profit_history)), profit_history)
    axes.axhline(y=0, color="black", linestyle="--")
    axes.set_title("Cumulative Profit Across Simulated Rounds")
    axes.set_xlabel("Round")
    axes.set_ylabel("Profit")
    axes.grid(alpha=0.25)
    figure.tight_layout()
    plt.show()

    return figure, axes


def compact_summary(results):
    """Remove detailed histories from a result before printing it."""
    excluded_keys = {"profit_history", "count_results"}
    return {
        key: value
        for key, value in results.items()
        if key not in excluded_keys
    }


if __name__ == "__main__":
    simulation_results = simulate(
        num_rounds=100_000,
        bet_spread=DEFAULT_BET_SPREAD,
    )
    print(compact_summary(simulation_results))
    plot_profit(simulation_results["profit_history"])
