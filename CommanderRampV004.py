import random
from collections import Counter
import matplotlib.pyplot as plt

# ---------------------------
# Card Classes
# ---------------------------

class Card:
    def __init__(self, name):
        self.name = name

class Land(Card):
    def __init__(self, name, produces=("C",), enters_tapped=False):
        super().__init__(name)
        self.produces = produces
        self.enters_tapped = enters_tapped

    def play(self, battlefield, turn):
        """Returns True if this land enters tapped, False otherwise"""
        return self.enters_tapped

class ConditionalLand(Land):
    def __init__(self, name, produces=("R",), condition=None):
        super().__init__(name, produces=produces)
        self.condition = condition

    def play(self, battlefield, turn):
        """Check if condition is met, otherwise enters tapped"""
        if self.condition and self.condition(battlefield):
            return False
        return True

class ManaRock(Card):
    def __init__(self, name, cost, produces=("C",)):
        super().__init__(name)
        self.cost = cost
        self.produces = produces

class ManaDork(Card):
    def __init__(self, name, cost, produces=("B",)):
        super().__init__(name)
        self.cost = cost
        self.produces = produces
        self.summoning_sick = True

# ---------------------------
# Deck Setup
# ---------------------------

def has_mountain(battlefield):
    return any(isinstance(card, Land) and "R" in card.produces for card in battlefield)

def build_deck():
    deck = []

    # Lands
    for _ in range(20):
        deck.append(Land("Mountain", produces=("R",)))
    for _ in range(10):
        deck.append(Land("Swamp", produces=("B",)))
    for _ in range(5):
        deck.append(ConditionalLand("MountainCheckLand", produces=("R",), condition=has_mountain))

    # Mana rocks
    for _ in range(10):
        deck.append(ManaRock("Signet", cost=2, produces=("R","B")))

    # Mana dorks
    for _ in range(1):
        deck.append(ManaDork("Lead Myr", cost=1, produces=("B",)))

    # Fillers
    while len(deck) < 100:
        deck.append(Card("Other"))

    return deck

# ---------------------------
# Game Simulation
# ---------------------------

def simulate_game(deck, commander_cost=6, max_turns=15):
    random.shuffle(deck)
    hand = deck[:7]
    library = deck[7:]

    battlefield = []
    mana_sources = []
    turn = 0

    while turn < max_turns:
        turn += 1

        # Draw
        if library:
            hand.append(library.pop(0))

        # Play a land if possible
        for card in hand:
            if isinstance(card, Land):
                tapped = card.play(battlefield, turn)
                battlefield.append(card)
                if not tapped:
                    mana_sources.append(card)
                hand.remove(card)
                break

        # Cast mana rocks/dorks if possible
        mana_available = len(mana_sources)
        playable = True
        while playable:
            playable = False
            for card in list(hand):
                if isinstance(card, ManaRock) and mana_available >= card.cost:
                    mana_available -= card.cost
                    battlefield.append(card)
                    mana_sources.append(card)
                    hand.remove(card)
                    playable = True
                    break
                if isinstance(card, ManaDork) and mana_available >= card.cost:
                    mana_available -= card.cost
                    battlefield.append(card)
                    card.summoning_sick = True
                    hand.remove(card)
                    playable = True
                    break

        # Calculate total mana
        total_mana = len([c for c in battlefield if isinstance(c, Land)])
        total_mana += len([c for c in battlefield if isinstance(c, ManaRock)])
        total_mana += len([c for c in battlefield if isinstance(c, ManaDork) and not c.summoning_sick])

        # Remove summoning sickness
        for c in battlefield:
            if isinstance(c, ManaDork):
                c.summoning_sick = False

        # Can we cast commander?
        if total_mana >= commander_cost:
            return turn

    return None  # never cast

# ---------------------------
# Run Simulations
# ---------------------------

def run_simulations(trials=10000):
    deck = build_deck()
    results = []
    for _ in range(trials):
        turn = simulate_game(deck)
        if turn is not None:
            results.append(turn)

    distribution = Counter(results)
    total = sum(distribution.values())

    print("Commander Cast Turn Distribution:")
    for turn, count in sorted(distribution.items()):
        percent = 100 * count / total
        print(f"Turn {turn}: {count} ({percent:.2f}%)")

    # Plot histogram
    turns = sorted(distribution.keys())
    counts = [distribution[t] for t in turns]
    percents = [100 * c / total for c in counts]

    fig, ax1 = plt.subplots()

    ax1.bar(turns, counts, alpha=0.7, label="Counts")
    ax1.set_xlabel("Turn")
    ax1.set_ylabel("Counts")
    ax1.set_title("Commander Cast Turn Distribution")

    ax2 = ax1.twinx()
    ax2.plot(turns, percents, color="red", marker="o", label="Percentages")
    ax2.set_ylabel("Percentage (%)")

    fig.legend(loc="upper right")
    plt.show()

# ---------------------------
# Main
# ---------------------------

if __name__ == "__main__":
    run_simulations(5000)
