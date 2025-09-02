import random
from collections import Counter
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Deck builder ---
def build_deck(lands, rocks, fillers):
    deck = []
    for _ in range(lands):
        deck.append({"name": "Land", "type": "land", "cost": 0, "mana": {"colorless": 1}})
    for _ in range(rocks):
        deck.append({"name": "Rock", "type": "rock", "cost": 2, "mana": {"colorless": 1}})
    for _ in range(fillers):
        deck.append({"name": "Filler", "type": "filler", "cost": 0, "mana": {}})
    return deck

# --- Game simulation ---
class Game:
    def __init__(self, deck):
        self.turn = 0
        self.deck = deck[:]
        random.shuffle(self.deck)
        self.hand = [self.deck.pop() for _ in range(7)]
        self.battlefield = []
        self.lands_played = 0

    def draw(self):
        if self.deck:
            self.hand.append(self.deck.pop())

    def available_mana(self):
        return sum(card["mana"].get("colorless", 0) for card in self.battlefield)

    def play_land(self):
        if self.lands_played == 0:
            for card in self.hand:
                if card["type"] == "land":
                    self.battlefield.append(card)
                    self.hand.remove(card)
                    self.lands_played = 1
                    return True
        return False

    def play_rocks(self):
        played = True
        while played:
            played = False
            for card in list(self.hand):
                if card["type"] == "rock" and self.available_mana() >= card["cost"]:
                    self.battlefield.append(card)
                    self.hand.remove(card)
                    played = True
                    break

    def play_until_commander(self, commander_cost=6, max_turns=20):
        while self.turn < max_turns:
            self.turn += 1
            self.lands_played = 0
            self.draw()
            self.play_land()
            self.play_rocks()
            if self.available_mana() >= commander_cost:
                return self.turn
        return None

# --- Monte Carlo ---
def run_simulation(trials, lands, rocks, fillers):
    deck = build_deck(lands, rocks, fillers)
    results = []
    for _ in range(trials):
        game = Game(deck)
        turn_cast = game.play_until_commander()
        if turn_cast:
            results.append(turn_cast)
    counts = Counter(results)
    avg_turn = sum(results) / len(results)
    return counts, avg_turn, len(results)

# --- Display results ---
def show_results(counts, avg_turn, total_games):
    print("Results:")
    for turn in sorted(counts.keys()):
        count = counts[turn]
        pct = 100 * count / total_games
        print(f"Turn {turn}: {count} games ({pct:.1f}%)")
    print(f"\nAverage turn commander cast: {avg_turn:.2f}")

    # Plot histogram
    turns = sorted(counts.keys())
    values = [counts[t] for t in turns]
    percentages = [100 * counts[t] / total_games for t in turns]

    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax1.bar(turns, values, color="skyblue", edgecolor="black")
    ax1.set_xlabel("Turn number")
    ax1.set_ylabel("Games (count)", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    # Second y-axis for percentages
    ax2 = ax1.twinx()
    ax2.plot(turns, percentages, color="red", marker="o")
    ax2.set_ylabel("Percentage (%)", color="red")
    ax2.tick_params(axis="y", labelcolor="red")

    plt.title(f"Commander Cast Turn Distribution (avg {avg_turn:.2f})")

    # Embed in Tkinter window
    root = tk.Tk()
    root.title("Simulation Results")
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    tk.Label(root, text=f"Average Turn: {avg_turn:.2f}").pack()
    root.mainloop()

# --- Run ---
if __name__ == "__main__":
    counts, avg_turn, total_games = run_simulation(trials=10000, lands=33, rocks=14, fillers=53)
    show_results(counts, avg_turn, total_games)
