import random
from collections import Counter
import matplotlib.pyplot as plt
import tkinter as tk
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ----------------------------
# Card System
# ----------------------------
class Card:
    name: str
    card_type: str  # "land", "dork", "rock", etc.
    cost: int = 0
    mana_produced: int = 0
    subtypes: List[str] = field(default_factory=list)  # e.g., ["Mountain"]
    enters_tapped_condition: Optional[Callable[[List["Card"]], bool]] = None
    tapped: bool = False  # lands and dorks can be tapped/untapped
    
    def __init__(self, name, ctype, cost=0, mana=None, enters_tapped=False,
                 summoning_sick=False, cost_reduction=None):
        self.name = name
        self.ctype = ctype              # "land", "rock", "dork", "reducer", "filler"
        self.cost = cost
        self.mana = mana or {}          # e.g. {"colorless": 1}, {"green": 1}
        self.enters_tapped = enters_tapped
        self.tapped = False
        self.summoning_sick = summoning_sick
        self.cost_reduction = cost_reduction or {}

    def enters_battlefield(self, battlefield: List["Card"]):
        """Handles ETB logic (like tapped-unless conditions)."""
        if self.card_type == "land":
            if self.enters_tapped_condition:
                # If condition is true, enters untapped. If false, tapped.
                self.tapped = not self.enters_tapped_condition(battlefield)
            else:
                self.tapped = False

    def can_produce_mana(self, turn_played, current_turn):
        """Return True if this permanent can produce mana this turn."""
        if self.ctype == "land":
            return not (self.enters_tapped and turn_played == current_turn)
        if self.ctype == "rock":
            return True
        if self.ctype == "dork":
            return current_turn > turn_played  # summoning sickness
        return False

    def produce_mana(self):
        """Return a dict of mana this card generates."""
        return self.mana

# -------------------------
# Example Conditional Functions
# -------------------------

def tapped_unless_mountain(battlefield: List[Card]) -> bool:
    """Returns True if a Mountain is already in play (so land enters untapped)."""
    return any("Mountain" in c.subtypes for c in battlefield if c.card_type == "land")

# -------------------------
# Play Land Function
# -------------------------

def play_land(card: Card, battlefield: List[Card]):
    """Play a land to the battlefield, handling tapped logic."""
    card.enters_battlefield(battlefield)
    battlefield.append(card)


# ----------------------------
# Game Simulation
# ----------------------------
class Game:
    def __init__(self, deck):
        self.turn = 0
        self.deck = deck[:]
        random.shuffle(self.deck)
        self.hand = [self.deck.pop() for _ in range(7)]
        self.battlefield = []  # list of (Card, turn_played)
        self.lands_played = 0

    def draw(self):
        if self.deck:
            self.hand.append(self.deck.pop())

    def play_land(self):
        if self.lands_played == 0:
            for card in list(self.hand):
                if card.ctype == "land":
                    self.battlefield.append((card, self.turn))
                    self.hand.remove(card)
                    self.lands_played = 1
                    return True
        return False

    def available_mana(self):
        total = {}
        for card, played_turn in self.battlefield:
            if card.can_produce_mana(played_turn, self.turn):
                for color, amount in card.produce_mana().items():
                    total[color] = total.get(color, 0) + amount
        return total

    def play_permanents(self):
        """Greedy play of rocks, dorks, reducers if affordable."""
        played = True
        while played:
            played = False
            for card in list(self.hand):
                if card.ctype in ["rock", "dork", "reducer"]:
                    if self.can_pay_cost(card.cost):
                        self.battlefield.append((card, self.turn))
                        self.hand.remove(card)
                        played = True
                        break

    def can_pay_cost(self, cost):
        """Simplified: just check if total mana >= cost."""
        return sum(self.available_mana().values()) >= cost

    def can_cast_commander(self, commander_cost):
        # Gather cost reductions
        reductions = {}
        for card, _ in self.battlefield:
            for color, amount in card.cost_reduction.items():
                reductions[color] = reductions.get(color, 0) + amount

        # Apply reductions
        effective_cost = commander_cost.copy()
        for color in effective_cost:
            effective_cost[color] = max(0, effective_cost[color] - reductions.get(color, 0))

        mana_pool = self.available_mana()

        # Check colored requirements
        for color in effective_cost:
            if color != "colorless" and mana_pool.get(color, 0) < effective_cost[color]:
                return False

        # Check total requirement
        total_available = sum(mana_pool.values())
        total_needed = sum(effective_cost.values())
        return total_available >= total_needed

    def play_until_commander(self, commander_cost, max_turns=20):
        while self.turn < max_turns:
            self.turn += 1
            self.lands_played = 0
            self.draw()
            self.play_land()
            self.play_permanents()
            if self.can_cast_commander(commander_cost):
                return self.turn
        return None


# ----------------------------
# Monte Carlo Runner
# ----------------------------
def run_simulation(deck, commander_cost, trials):
    results = []
    for _ in range(trials):
        game = Game(deck)
        turn_cast = game.play_until_commander(commander_cost)
        if turn_cast:
            results.append(turn_cast)
    counts = Counter(results)
    avg_turn = sum(results) / len(results) if results else None
    return counts, avg_turn, len(results)


# ----------------------------
# Result Display
# ----------------------------
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

    ax2 = ax1.twinx()
    ax2.plot(turns, percentages, color="red", marker="o")
    ax2.set_ylabel("Percentage (%)", color="red")
    ax2.tick_params(axis="y", labelcolor="red")

    plt.title(f"Commander Cast Turn Distribution (avg {avg_turn:.2f})")

    root = tk.Tk()
    root.title("Simulation Results")
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    tk.Label(root, text=f"Average Turn: {avg_turn:.2f}").pack()
    root.mainloop()


# ----------------------------
# Example Run
# ----------------------------
if __name__ == "__main__":
    commander_cost = {"colorless": 4, "black": 1, 'red': 1}

    # Build a mixed deck
    deck = []
    for _ in range(7):
        deck.append(Card(name="Swamp", card_type="land", mana={"black": 1}))
    for _ in range(13):
        deck.append(Card('Mountain', 'land', mana={'red': 1}))
    for _ in range(4):
        deck.append(Card("Temple", "land", mana={"black": 1}, enters_tapped=True))
    for _ in range(4):
        deck.append(Card(name="Summit Land", card_type="land", subtypes=["Swamp", "Mountain"],
            enters_tapped_condition=tapped_unless_mountain))
    # 8 rocks (2 cost, tap for 1)
    for _ in range(6):
        deck.append(Card("Mind Stone", "rock", cost=2, mana={"colorless": 1}))
    # 2 stronger rocks
    deck.append(Card("Thran Dynamo", "rock", cost=4, mana={"colorless": 3}))
    deck.append(Card("Worn Powerstone", "rock", cost=3, mana={"colorless": 2}, enters_tapped=True))
    # 4 dorks
    for _ in range(4):
        deck.append(Card("Llanowar Elves", "dork", cost=1, mana={"green": 1}, summoning_sick=True))
    # 2 cost reducers
    deck.append(Card("Jet Medallion", "reducer", cost=2, cost_reduction={"black": 1}))
    deck.append(Card("Emerald Medallion", "reducer", cost=2, cost_reduction={"green": 1}))
    # Fillers to make 99
    while len(deck) < 100:
        deck.append(Card("Filler", "filler"))

    counts, avg_turn, total_games = run_simulation(deck, commander_cost, trials=10000)
    show_results(counts, avg_turn, total_games)
