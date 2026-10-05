import time 
import os
from tracking_count import count_range

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")
def display_cards(cards, delay):
    """Displays card with desired delay between displays"""
    for card in cards:
        clear_screen()
        print(f"\n\n          {card}")
        time.sleep(delay)
    clear_screen()
def run_trainer(shoe):
    """Main function for the card counting trainer"""
    delay = int(input("Enter integer second delay value"))
    cards = shoe[:20]

    input("Press Enter to begin...")
    start_time = time.perf_counter()
    display_cards(cards, delay)
    answer = int(input("What is the running count? "))
    end_time = time.perf_counter()
    correct_count = count_range(cards)
    total_time = end_time - start_time

    if answer == correct_count:
        print("Correct!")
    else:
        print(f"Incorrect. The correct count was {correct_count}.")

    print(f"Time: {total_time:.2f} seconds")
