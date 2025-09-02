import random
from collections import Counter

# Example decklist: 36 lands, 10 rocks, rest filler
def build_deck(lands=36, rocks=10, fillers=54):
    deck = []
    for _ in range(lands):
        deck.append({"name": "Land", "type": "land", "cost": 0, "mana": {"colorless": 1}})
    for _ in range(rocks):
        deck.append({"name": "Rock", "type": "rock", "cost": 2, "mana": {"colorless": 1}})
    for _ in range(fillers):
        deck.append({"name": "Filler", "type": "filler", "cost": 0, "mana": {}})
    return deck

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
        # Simple greedy: play any rock you can afford
        played = True
        while played:
            played = False
            for card in list(self.hand):
                if card["type"] == "rock" and self.available_mana() >= card["cost"]:
                    # pay cost by tapping mana sources (abstracted)
                    # here we just reduce "virtual mana" temporarily
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
        return None  # never castable in time window


def run_simulation(trials=10000, lands=36, rocks=10, fillers=54):
    deck = build_deck(lands, rocks, fillers)
    results = []
    for _ in range(trials):
        game = Game(deck)
        turn_cast = game.play_until_commander()
        if turn_cast:
            results.append(turn_cast)
    counts = Counter(results)
    avg_turn = sum(results) / len(results)
    return counts, avg_turn

if __name__ == "__main__":
    counts, avg_turn = run_simulation(10000, lands=33, rocks=14, fillers=53)
    print("Distribution:", counts)
    print("Average turn commander cast:", avg_turn)
