from dataclasses import dataclass


max_player_hands = 4
allow_resplit_aces = False
allow_double_after_split = True
dealer_hits_soft_17 = True


@dataclass(frozen=True)
class RoundResult:
    """Financial and shoe-position result from one completed round."""

    profit: float
    next_card_index: int
    hands_played: int


def deal_hands(cards, index): 
    """Deals out inital cards to single player and dealer"""
    player_cards = [cards[index + 0], cards[index + 2]]
    dealer_cards = [cards[index + 1], cards[index + 3]]
    next_card_index = index + 4
    return player_cards, dealer_cards, next_card_index



def hide_cards(player_cards, dealer_cards, hide=True):
    """Hides the dealers turned card during players turn"""
    if hide:
        print(f"Dealer: [{dealer_cards[0]}, X]")
    else:
        print(f"Dealer: {dealer_cards}")
    print(f"\nPlayer: {player_cards}")



def hit(cards, player_cards, index):
    """Function for players hit, adding card to players hand"""
    player_cards.append(cards[index])
    return index + 1



def add_hand(hand):
    """Calculates hand value"""
    value = 0
    ace_count = 0
    for card in hand:
        if card in ["J", "Q", "K"]:
            value += 10
        elif card in ["A"]:
            value += 11
            ace_count += 1
        else:
            value += int(card)
    while value > 21 and ace_count > 0:
        value -= 10
        ace_count -= 1
    return value 


def is_soft_hand(hand):
    """Return True when at least one ace is still counted as 11."""
    value = 0
    ace_count = 0

    for card in hand:
        if card in ["J", "Q", "K"]:
            value += 10
        elif card == "A":
            value += 11
            ace_count += 1
        else:
            value += int(card)

    while value > 21 and ace_count > 0:
        value -= 10
        ace_count -= 1

    return ace_count > 0



def can_split(hand, number_of_hands, from_split=False):
    """Return whether a pair can be split under the table rules."""
    if len(hand) != 2 or number_of_hands >= max_player_hands:
        return False

    same_value = add_hand([hand[0]]) == add_hand([hand[1]])
    resplitting_aces = from_split and hand[0] == "A" and hand[1] == "A"
    return same_value and (allow_resplit_aces or not resplitting_aces)


def can_surrender(hand, from_split=False):
    """Allow late surrender only on the original two-card hand."""
    return len(hand) == 2 and not from_split


def offer_insurance(dealer_cards, bet):
    """Offer a half-bet insurance wager when the dealer shows an ace."""
    if dealer_cards[0] != "A":
        return 0

    while True:
        answer = input(f"Insurance for {bet / 2}? (yes/no) ").strip().lower()
        if answer in ["yes", "y"]:
            return bet / 2
        if answer in ["no", "n"]:
            return 0
        print("Please enter yes or no.")


def settle_insurance(insurance_bet, dealer_blackjack, verbose=True):
    """Return the net profit from an insurance wager."""
    if insurance_bet == 0:
        return 0

    if dealer_blackjack:
        profit = insurance_bet * 2
        if verbose:
            print(f"Insurance wins {profit}.")
        return profit

    if verbose:
        print(f"Insurance loses {insurance_bet}.")
    return -insurance_bet



def split_hand(hand, cards, next_card_index):
    first_hand = [hand[0], cards[next_card_index]]
    next_card_index += 1
    second_hand = [hand[1], cards[next_card_index]]
    next_card_index += 1
    return first_hand, second_hand, next_card_index




def playing_player(
    player_cards,
    dealer_cards,
    cards,
    next_card_index,
    bet,
    strategy=None,
    verbose=True,
):
    player_hands = [
        {
            "cards": player_cards,
            "bet": bet,
            "from_split": False,
            "split_aces": False,
            "surrendered": False,
        }
    ]
    hand_index = 0

    while hand_index < len(player_hands):
        current_hand = player_hands[hand_index] #full hand and bet size
        hand = current_hand["cards"] #just the cards

        while True:
            if verbose:
                hide_cards(hand, dealer_cards)
                print(f"\nPlaying hand {hand_index + 1} of {len(player_hands)}")
                print(f"Value: {add_hand(hand)}")
            split_allowed = can_split(
                hand, len(player_hands), current_hand["from_split"]
            )
            if current_hand["split_aces"] and not split_allowed:
                if verbose:
                    print("Split aces receive one card each and automatically stand.")
                break

            allowed_actions = {"stand"}
            if not current_hand["split_aces"]:
                allowed_actions.add("hit")

            can_double = (
                len(hand) == 2
                and (allow_double_after_split or not current_hand["from_split"])
                and not current_hand["split_aces"]
            )
            if can_double:
                allowed_actions.add("double")

            surrender_allowed = can_surrender(hand, current_hand["from_split"])
            if surrender_allowed:
                allowed_actions.add("surrender")

            if split_allowed:
                allowed_actions.add("split")

            if strategy is None:
                action_order = ["hit", "stand", "double", "surrender", "split"]
                options = [
                    action.title()
                    for action in action_order
                    if action in allowed_actions
                ]
                answer = input(f"{', '.join(options)}? ").strip().lower()
            else:
                answer = strategy.choose_action(
                    hand,
                    dealer_cards[0],
                    allowed_actions,
                )

            if answer not in allowed_actions:
                if strategy is not None:
                    raise ValueError(
                        f"Strategy returned illegal action {answer!r}; "
                        f"allowed actions are {sorted(allowed_actions)!r}."
                    )
                if verbose:
                    print("Invalid choice")
                continue

            if answer == "split":
                split_aces = hand[0] == "A"
                first_hand, second_hand, next_card_index = split_hand(hand, cards, next_card_index)
                player_hands[hand_index:hand_index + 1] = [
                    {
                        "cards": first_hand,
                        "bet": current_hand["bet"],
                        "from_split": True,
                        "split_aces": split_aces,
                        "surrendered": False,
                    },
                    {
                        "cards": second_hand,
                        "bet": current_hand["bet"],
                        "from_split": True,
                        "split_aces": split_aces,
                        "surrendered": False,
                    },
                ]
                current_hand = player_hands[hand_index]
                hand = current_hand["cards"]
                if verbose:
                    print(f"Split into {first_hand} and {second_hand}")
                    print(f"All current hands: {[h['cards'] for h in player_hands]}")
                continue
            elif answer == "double":
                next_card_index = hit(cards, hand, next_card_index)
                if verbose:
                    print(hand)
                current_hand["bet"] *= 2
                if add_hand(hand) > 21:
                    if verbose:
                        print("Bust")
                    break
                break
            elif answer == "hit":
                next_card_index = hit(cards, hand, next_card_index)
                if verbose:
                    print(hand)
                if add_hand(hand) > 21:
                    if verbose:
                        print("Bust")
                    break
            elif answer == "stand":
                if verbose:
                    print("You stand")
                break
            elif answer == "surrender":
                current_hand["surrendered"] = True
                if verbose:
                    print("You surrender.")
                break

        hand_index += 1

    return player_hands, next_card_index



def playing_dealer(dealer_cards, cards, index):
    while (
        add_hand(dealer_cards) < 17
        or (
            dealer_hits_soft_17
            and add_hand(dealer_cards) == 17
            and is_soft_hand(dealer_cards)
        )
    ):
        dealer_cards.append(cards[index])
        index += 1
    return index





def run_game(
    shoe,
    start_index=0,
    bet=None,
    strategy=None,
    verbose=True,
):
    """Play one round and return its profit and ending shoe position."""
    if bet is None:
        bet = int(input("Place your bet: "))
    if bet <= 0:
        raise ValueError("bet must be greater than zero.")
    if start_index < 0 or len(shoe) - start_index < 4:
        raise ValueError("The shoe does not contain enough cards to deal a round.")

    player_cards, dealer_cards, next_card_index = deal_hands(shoe, start_index)
    #Shows dealt cards

    #checking for default blackjacks
    player_blackjack = add_hand(player_cards) == 21
    dealer_blackjack = add_hand(dealer_cards) == 21
    if verbose and dealer_cards[0] == "A":
        hide_cards(player_cards, dealer_cards)

    # Basic strategy does not take insurance. Interactive play can still offer
    # it, and its net result is included in the round's returned profit.
    insurance_bet = offer_insurance(dealer_cards, bet) if strategy is None else 0
    insurance_profit = settle_insurance(
        insurance_bet,
        dealer_blackjack,
        verbose,
    )

    if player_blackjack and dealer_blackjack:
        if verbose:
            print("Push, both have blackjack.")
            hide_cards(player_cards, dealer_cards, hide=False)
        return RoundResult(insurance_profit, next_card_index, 1)
    if player_blackjack:
        blackjack_profit = bet * 1.5
        if verbose:
            print(f"Blackjack! You win {blackjack_profit}.")
            hide_cards(player_cards, dealer_cards, hide=False)
        return RoundResult(
            blackjack_profit + insurance_profit,
            next_card_index,
            1,
        )
    if dealer_blackjack:
        if verbose:
            print(f"Dealer blackjack. You lose {bet}.")
            hide_cards(player_cards, dealer_cards, hide=False)
        return RoundResult(-bet + insurance_profit, next_card_index, 1)

    player_hands, next_card_index = playing_player(
        player_cards,
        dealer_cards,
        shoe,
        next_card_index,
        bet,
        strategy,
        verbose,
    )

    if any(
        not current_hand["surrendered"]
        and add_hand(current_hand["cards"]) <= 21
        for current_hand in player_hands
    ):
        next_card_index = playing_dealer(dealer_cards, shoe, next_card_index)

    if verbose:
        print(f"Dealer: {dealer_cards}")

    #Final hand value comparison
    dealer_value = add_hand(dealer_cards)
    profit = insurance_profit

    for hand_number, current_hand in enumerate(player_hands, start=1):
        hand = current_hand["cards"]
        hand_bet = current_hand["bet"]

        player_value = add_hand(hand)

        if verbose:
            print(f"\nHand {hand_number}: {hand}")
            print(f"Player value: {player_value}")
            print(f"Dealer value: {dealer_value}")

        if current_hand["surrendered"]:
            hand_profit = -hand_bet / 2
            message = f"You lose {hand_bet / 2} — surrendered."
        elif player_value > 21:
            hand_profit = -hand_bet
            message = f"You lose {hand_bet} — bust."
        elif dealer_value > 21:
            hand_profit = hand_bet
            message = f"You win {hand_bet} — dealer bust."
        elif player_value > dealer_value:
            hand_profit = hand_bet
            message = f"You win {hand_bet}."
        elif player_value < dealer_value:
            hand_profit = -hand_bet
            message = f"You lose {hand_bet}."
        else:
            hand_profit = 0
            message = "Push."

        profit += hand_profit
        if verbose:
            print(message)

    return RoundResult(profit, next_card_index, len(player_hands))
