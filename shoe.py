import random


def create_shoe(n_decks, rng=None):
    """Create and shuffle a blackjack shoe.

    Passing a ``random.Random`` instance makes simulations reproducible while
    preserving the existing behavior when ``rng`` is omitted.
    """
    if n_decks < 1:
        raise ValueError("n_decks must be at least 1.")

    deck = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"] * 4
    shoe = deck * n_decks
    shuffler = rng if rng is not None else random
    shuffler.shuffle(shoe)
    return shoe
