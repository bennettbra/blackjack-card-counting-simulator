from shoe import create_shoe
from tracking_count import plot_count
from count_trainer import run_trainer
from blackjack_game import run_game
from simulation import compact_summary, plot_profit, simulate
from betting import DEFAULT_BET_SPREAD

shoe = create_shoe(n_decks = 4)


def main(): 
    #plot_count(shoe,true_count=True)
    #run_trainer(shoe)
    #run_game(shoe)
    simulation_results = simulate(num_rounds=100_000, bet_spread = DEFAULT_BET_SPREAD)
    print(compact_summary(simulation_results))
    plot_profit(simulation_results["profit_history"])
    
if __name__ == "__main__":
    """Ensure only run when this file is the one being called."""
    main()
