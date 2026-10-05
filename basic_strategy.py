"""Basic strategy for a four-or-more-deck blackjack game.

The strategy in this module assumes the rules currently configured in
``blackjack_game.py``:

* the dealer hits soft 17 (H17),
* double after split is allowed (DAS),
* late surrender is allowed, and
* the dealer peeks for blackjack.

Actions are returned as lowercase strings so they can be passed directly to
the existing game loop.
"""


HIT = "hit"
STAND = "stand"
DOUBLE = "double"
SPLIT = "split"
SURRENDER = "surrender"

VALID_ACTIONS = frozenset({HIT, STAND, DOUBLE, SPLIT, SURRENDER})


# With DAS, these pairs should be split against the listed dealer upcards.
# A value of 10 covers 10, J, Q, and K.
PAIR_SPLIT_UPCARDS = {
    2: frozenset({2, 3, 4, 5, 6, 7}),
    3: frozenset({2, 3, 4, 5, 6, 7}),
    4: frozenset({5, 6}),
    6: frozenset({2, 3, 4, 5, 6}),
    7: frozenset({2, 3, 4, 5, 6, 7}),
    8: frozenset({2, 3, 4, 5, 6, 7, 8, 9, 10, 11}),
    9: frozenset({2, 3, 4, 5, 6, 8, 9}),
    11: frozenset({2, 3, 4, 5, 6, 7, 8, 9, 10, 11}),
}


def card_value(card):
    """Return a card's blackjack value, using 11 for an ace."""
    card = str(card).upper()

    if card in {"10", "J", "Q", "K"}:
        return 10
    if card == "A":
        return 11

    try:
        value = int(card)
    except ValueError as exc:
        raise ValueError(f"Invalid card: {card!r}") from exc

    if value < 2 or value > 9:
        raise ValueError(f"Invalid card: {card!r}")
    return value


def hand_value(hand):
    """Return ``(total, is_soft)`` for a blackjack hand."""
    if not hand:
        raise ValueError("A blackjack hand cannot be empty.")

    values = [card_value(card) for card in hand]
    total = sum(values)
    aces_counted_as_eleven = values.count(11)

    while total > 21 and aces_counted_as_eleven:
        total -= 10
        aces_counted_as_eleven -= 1

    return total, aces_counted_as_eleven > 0


def pair_value(hand):
    """Return the common value for a two-card pair, or ``None``."""
    if len(hand) != 2:
        return None

    first_value = card_value(hand[0])
    second_value = card_value(hand[1])
    return first_value if first_value == second_value else None


def default_allowed_actions(hand):
    """Infer legal actions when the caller does not supply game context.

    A real game engine should pass ``allowed_actions`` because only it knows
    whether a hand came from a split, whether the split limit was reached, and
    whether enough bankroll remains to double or split.
    """
    actions = {HIT, STAND}

    if len(hand) == 2:
        actions.update({DOUBLE, SURRENDER})
        if pair_value(hand) is not None:
            actions.add(SPLIT)

    return actions


def surrender_action(total, is_soft, pair, dealer_value, allowed_actions):
    """Return surrender when H17 late-surrender strategy calls for it."""
    if SURRENDER not in allowed_actions or is_soft:
        return None

    # In an H17 game, 8,8 vs. ace is surrendered when possible; otherwise the
    # pair is split. Other hard 16 hands surrender against 9, 10, or ace.
    if pair == 8:
        return SURRENDER if dealer_value == 11 else None

    if total == 15 and dealer_value in {10, 11}:
        return SURRENDER
    if total == 16 and dealer_value in {9, 10, 11}:
        return SURRENDER
    if total == 17 and dealer_value == 11:
        return SURRENDER

    return None


def hard_action(total, dealer_value, allowed_actions):
    """Choose an action for a hard total."""
    if total <= 8:
        preferences = (HIT,)
    elif total == 9:
        preferences = (DOUBLE, HIT) if dealer_value in {3, 4, 5, 6} else (HIT,)
    elif total == 10:
        preferences = (DOUBLE, HIT) if dealer_value <= 9 else (HIT,)
    elif total == 11:
        # Doubling 11 vs. ace is one of the H17 changes.
        preferences = (DOUBLE, HIT)
    elif total == 12:
        preferences = (STAND,) if dealer_value in {4, 5, 6} else (HIT,)
    elif total <= 16:
        preferences = (STAND,) if dealer_value in {2, 3, 4, 5, 6} else (HIT,)
    else:
        preferences = (STAND,)

    return first_allowed(preferences, allowed_actions)


def soft_action(total, dealer_value, allowed_actions):
    """Choose an action for a hand containing an ace still valued at 11."""
    if total in {13, 14} and dealer_value in {5, 6}:
        preferences = (DOUBLE, HIT)
    elif total in {15, 16} and dealer_value in {4, 5, 6}:
        preferences = (DOUBLE, HIT)
    elif total == 17 and dealer_value in {3, 4, 5, 6}:
        preferences = (DOUBLE, HIT)
    elif total <= 17:
        preferences = (HIT,)
    elif total == 18:
        if dealer_value in {2, 3, 4, 5, 6}:
            # H17 adds the double against dealer 2. If doubling is unavailable,
            # standing is the correct fallback.
            preferences = (DOUBLE, STAND)
        elif dealer_value in {7, 8}:
            preferences = (STAND,)
        else:
            preferences = (HIT,)
    elif total == 19 and dealer_value == 6:
        # Doubling soft 19 vs. 6 is another H17-specific change.
        preferences = (DOUBLE, STAND)
    else:
        preferences = (STAND,)

    return first_allowed(preferences, allowed_actions)


def first_allowed(preferences, allowed_actions):
    """Return the first preferred action that is legal."""
    for action in preferences:
        if action in allowed_actions:
            return action

    raise ValueError(
        f"None of the strategy actions {preferences!r} are allowed; "
        f"received {sorted(allowed_actions)!r}."
    )


def choose_action(hand, dealer_upcard, allowed_actions=None):
    """Return the H17/DAS/late-surrender basic-strategy action.

    Args:
        hand: The player's cards, such as ``["A", "7"]``.
        dealer_upcard: The dealer's visible card.
        allowed_actions: Legal action strings for the current hand. If omitted,
            legality is inferred from the number and values of the cards.

    Returns:
        One of ``"hit"``, ``"stand"``, ``"double"``, ``"split"``, or
        ``"surrender"``.
    """
    hand = list(hand)
    dealer_value = card_value(dealer_upcard)
    total, is_soft = hand_value(hand)
    pair = pair_value(hand)

    if allowed_actions is None:
        allowed_actions = default_allowed_actions(hand)
    else:
        allowed_actions = {str(action).lower() for action in allowed_actions}
        unknown_actions = allowed_actions - VALID_ACTIONS
        if unknown_actions:
            raise ValueError(f"Unknown actions: {sorted(unknown_actions)!r}")
        if not allowed_actions:
            raise ValueError("allowed_actions cannot be empty.")

    action = surrender_action(
        total,
        is_soft,
        pair,
        dealer_value,
        allowed_actions,
    )
    if action is not None:
        return action

    if (
        pair in PAIR_SPLIT_UPCARDS
        and dealer_value in PAIR_SPLIT_UPCARDS[pair]
        and SPLIT in allowed_actions
    ):
        return SPLIT

    if is_soft:
        return soft_action(total, dealer_value, allowed_actions)
    return hard_action(total, dealer_value, allowed_actions)


class BasicStrategy:
    """Decision-policy wrapper for use by an automated game engine."""

    def choose_action(self, hand, dealer_upcard, allowed_actions=None):
        return choose_action(hand, dealer_upcard, allowed_actions)
