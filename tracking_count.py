def count_value(card):
    """Counts single card"""
    if card in ["2", "3", "4", "5", "6"]:
        return 1
    elif card in ["10", "J", "Q", "K", "A"]:
        return -1
    else: 
        return 0 
def count_range(cards):
    """Uses single counting function to count a range"""
    count = 0 
    for card in cards:
        count += count_value(card)
    return count

def plot_count(cards, true_count=False):
    """Plots running count throughout the shoe"""
    """True count normalizes count to the number of decks remaining in the shoe"""
    import matplotlib.pyplot as plt

    count = 0
    count_history = [0]

    for i, card in enumerate(cards):
        if true_count:
            cards_remaining = len(cards) - (i + 1)
            if cards_remaining < 52: #break simulates a reshuffle when down to one deck
                break
            count += count_value(card)
            decks_remaining = cards_remaining / 52
            current_count = count / decks_remaining
        else:
            count += count_value(card)
            current_count = count
        count_history.append(current_count)
    
    plt.plot(count_history)
    if true_count: 
        plt.title("True Running Count Throughout the Shoe")
        plt.ylabel("True Count")
    else: 
        plt.title("Running Count Throughout the Shoe")
        plt.ylabel("Count")
    plt.xlabel("Cards Dealt")
    plt.axhline(y=0, linestyle="--")
    plt.show()
