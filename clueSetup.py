import math
import random
import time

import clueAgent

RESET = "\033[0m"
BOLD = "\033[1m"

COLOR_CODES = {
    "red": "\033[91m",
    "yellow": "\033[93m",
    "white": "\033[97m",
    "green": "\033[92m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
}

characterColors = {
    "scarlet": "red",
    "white": "white",
    "mustard": "yellow",
    "green": "green",
    "peacock": "blue",
    "plum": "magenta",
}

DIE_FACES = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
MAX_TURNS = 300


def colorText(text, colorName, bold=False):
    code = COLOR_CODES.get(colorName, "")
    prefix = BOLD if bold else ""
    return f"{prefix}{code}{text}{RESET}"


def promptInt(promptText, minValue, maxValue):
    while True:
        raw = input(promptText).strip()
        try:
            value = int(raw)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if minValue <= value <= maxValue:
            return value
        print(f"Please enter a number between {minValue} and {maxValue}.")


def rollDie():
    return random.randint(1, 6)


def rollDice(count=2, label=None, animate=True):
    if animate:
        for _ in range(6):
            preview = " ".join(colorText(random.choice(DIE_FACES), "cyan") for _ in range(count))
            print("\r" + preview, end="", flush=True)
            time.sleep(0.06)
        print("\r" + " " * 20 + "\r", end="")
    values = [rollDie() for _ in range(count)]
    faces = " ".join(colorText(DIE_FACES[v - 1], "cyan", bold=True) for v in values)
    total = sum(values)
    who = f"{label} rolls " if label else "Roll: "
    print(f"{who}{faces}  (total = {total})")
    return values, total


def printBoard():
    grid = [
        ["kitchen", "living", "garage"],
        ["bedroom", "bathroom", "office"],
        ["dining", "game", "courtyard"],
    ]
    cellWidth = 11
    horizontal = "+" + ("-" * cellWidth + "+") * 3
    print("\n" + colorText("=== The Mansion ===", "cyan", bold=True))
    print(horizontal)
    for row in grid:
        line = "|"
        for room in row:
            label = room.center(cellWidth)
            line += colorText(label, "green") + "|"
        print(line)
        print(horizontal)
    print()


def buildSeatingTable(playerInfo):
    width, height = 50, 13
    canvas = [[" "] * width for _ in range(height)]

    tableLeft, tableRight = 14, width - 15
    tableTop, tableBottom = 4, height - 5
    for x in range(tableLeft, tableRight + 1):
        canvas[tableTop][x] = "-"
        canvas[tableBottom][x] = "-"
    for y in range(tableTop, tableBottom + 1):
        canvas[y][tableLeft] = "|"
        canvas[y][tableRight] = "|"
    canvas[tableTop][tableLeft] = "+"
    canvas[tableTop][tableRight] = "+"
    canvas[tableBottom][tableLeft] = "+"
    canvas[tableBottom][tableRight] = "+"

    label = "CLUE"
    startX = (tableLeft + tableRight) // 2 - len(label) // 2
    midY = (tableTop + tableBottom) // 2
    for i, ch in enumerate(label):
        canvas[midY][startX + i] = ch

    n = len(playerInfo)
    centerX, centerY = width // 2, height // 2
    radiusX, radiusY = width // 2 - 3, height // 2 - 1
    placements = []
    for i, (name, colorName) in enumerate(playerInfo):
        angle = -math.pi / 2 + (2 * math.pi * i / n)
        px = int(centerX + radiusX * math.cos(angle))
        py = int(centerY + radiusY * math.sin(angle))
        startX2 = max(0, min(width - len(name), px - len(name) // 2))
        for j, ch in enumerate(name):
            if 0 <= py < height and 0 <= startX2 + j < width:
                canvas[py][startX2 + j] = ch
        placements.append((name, colorName))

    lines = ["".join(row) for row in canvas]
    for name, colorName in placements:
        colored = colorText(name, colorName, bold=True)
        for i, line in enumerate(lines):
            if name in line:
                lines[i] = line.replace(name, colored, 1)
    return "\n".join(lines)


def assignPlayers(numberOfPlayers):
    available = clueAgent.peopleAll.copy()
    print("\nYou are always seated as Player 1.")
    print("Available characters:", ", ".join(available))
    while True:
        choice = input("Choose your character: ").strip().lower()
        if choice in available:
            available.remove(choice)
            break
        print("Please choose one of the listed characters.")

    players = [{
        "num": 1,
        "character": choice,
        "color": characterColors[choice],
        "isHuman": True,
    }]

    random.shuffle(available)
    for i in range(2, numberOfPlayers + 1):
        character = available.pop()
        players.append({
            "num": i,
            "character": character,
            "color": characterColors[character],
            "isHuman": False,
            "mixEvery": random.randint(2, 4),
        })
    return players


def printRoster(players):
    print("\n" + colorText("=== Players ===", "cyan", bold=True))
    for p in players:
        role = "you" if p["isHuman"] else "agent"
        label = colorText(f"Player {p['num']}: {p['character'].capitalize()} ({role})", p["color"], bold=True)
        print(label)
    print()


def dealCards(players):
    n = len(players)
    solution = (
        random.choice(clueAgent.weaponsAll),
        random.choice(clueAgent.roomsAll),
        random.choice(clueAgent.peopleAll),
    )
    deck = [c for c in clueAgent.weaponsAll + clueAgent.roomsAll + clueAgent.peopleAll if c not in solution]
    random.shuffle(deck)

    extraCount = len(deck) % n
    faceUp = deck[:extraCount]
    remaining = deck[extraCount:]

    hands = {p["num"]: set() for p in players}
    perPlayer = len(remaining) // n
    idx = 0
    for p in players:
        for _ in range(perPlayer):
            hands[p["num"]].add(remaining[idx])
            idx += 1
    return solution, hands, faceUp


def initTrackers(players, hands, faceUp):
    """Each player gets their own private tracker: their own hand is
    guaranteed knowledge, and everything else is built up turn by turn
    from what they personally witness (or are told, if they're the asker).
    """
    trackers = {}
    for viewer in players:
        vNum = viewer["num"]
        guaranteed = {p["num"]: set() for p in players}
        guaranteed[vNum] = set(hands[vNum])
        trackers[vNum] = {
            "viewerNum": vNum,
            "hand": hands[vNum],
            "guaranteed": guaranteed,
            "couldBeOut": {p["num"]: set() for p in players},
            # each clause is "this player holds >= 1 of these cards";
            # kept separate per event so unrelated clues can never merge
            # into a false certainty.
            "clauses": {p["num"]: [] for p in players},
            "askCounts": {},
            "turnCount": 0,
        }
    return trackers


def markGuaranteed(tracker, targetNum, card):
    if card in tracker["guaranteed"][targetNum]:
        return
    tracker["guaranteed"][targetNum].add(card)
    tracker["clauses"][targetNum] = [c for c in tracker["clauses"][targetNum] if card not in c]
    for otherNum in tracker["couldBeOut"]:
        if otherNum != targetNum:
            markOut(tracker, otherNum, card)


def markOut(tracker, targetNum, card):
    if card in tracker["couldBeOut"][targetNum]:
        return
    tracker["couldBeOut"][targetNum].add(card)
    remainingClauses = []
    for clause in tracker["clauses"][targetNum]:
        if card not in clause:
            remainingClauses.append(clause)
            continue
        reduced = clause - {card}
        if len(reduced) == 1:
            markGuaranteed(tracker, targetNum, next(iter(reduced)))
        elif len(reduced) > 1:
            remainingClauses.append(reduced)
        # len == 0 would mean a contradiction upstream; drop it defensively.
    tracker["clauses"][targetNum] = remainingClauses


def addClause(tracker, targetNum, question):
    if any(c in tracker["guaranteed"][targetNum] for c in question):
        return
    remaining = [c for c in question if c not in tracker["couldBeOut"][targetNum]]
    if len(remaining) == 1:
        markGuaranteed(tracker, targetNum, remaining[0])
    elif len(remaining) > 1:
        tracker["clauses"][targetNum].append(frozenset(remaining))


def applyEvent(trackers, players, askerNum, whoAnswered, question, revealedCard):
    n = len(players)
    if whoAnswered is not None:
        skipped = clueAgent.computeSkippedPlayers(askerNum, whoAnswered, n)
    else:
        skipped = [p["num"] for p in players if p["num"] != askerNum]

    for vNum, tracker in trackers.items():
        for s in skipped:
            if s != vNum:
                for card in question:
                    markOut(tracker, s, card)

        if whoAnswered is not None and whoAnswered != vNum:
            if vNum == askerNum:
                markGuaranteed(tracker, whoAnswered, revealedCard)
            else:
                addClause(tracker, whoAnswered, question)


def computePools(tracker, players, faceUp):
    """Remaining solution candidates per category, from this viewer's
    private knowledge. A card is ruled out once it's attributed to some
    hand, is face-up, or (via elimination) has been shown to belong to
    every *other* player's couldBeOut -- which, combined with it not
    being the viewer's own, leaves the solution as the only possibility.
    """
    allGuaranteed = set()
    for cards in tracker["guaranteed"].values():
        allGuaranteed.update(cards)

    pools = {}
    for key, allCards in (
        ("weapon", clueAgent.weaponsAll),
        ("room", clueAgent.roomsAll),
        ("person", clueAgent.peopleAll),
    ):
        candidates = []
        for card in allCards:
            if card in allGuaranteed or card in faceUp:
                continue
            excludedEverywhere = all(
                card in tracker["couldBeOut"][p["num"]]
                for p in players
                if p["num"] != tracker["viewerNum"]
            )
            if excludedEverywhere:
                candidates = [card]
                break
            candidates.append(card)
        pools[key] = candidates
    return pools


def resolveAnswer(players, askerNum, question, hands):
    n = len(players)
    i = askerNum % n + 1
    while i != askerNum:
        matches = [c for c in question if c in hands[i]]
        if matches:
            return i, matches
        i = i % n + 1
    return None, []


def reveal(solution):
    weapon, room, person = solution
    print(colorText(f"\nThe solution was: {person} with the {weapon} in the {room}.", "magenta", bold=True))


def printHumanStatus(tracker, players, hand, pools):
    print("\nYour hand:", ", ".join(sorted(hand)) or "none")
    print("Weapons still possible:", ", ".join(pools["weapon"]))
    print("Rooms still possible:", ", ".join(pools["room"]))
    print("People still possible:", ", ".join(pools["person"]))
    print("\n=== What you've deduced ===")
    for p in players:
        if p["isHuman"]:
            continue
        pNum = p["num"]
        guaranteed = ", ".join(sorted(tracker["guaranteed"][pNum])) or "none"
        potential = set().union(*tracker["clauses"][pNum]) if tracker["clauses"][pNum] else set()
        print(f"Player {pNum} ({p['character'].capitalize()}): guaranteed=[{guaranteed}] potential=[{', '.join(sorted(potential)) or 'none'}]")
    print()


def readSuggestion(prompt, fallback):
    while True:
        raw = input(prompt).strip()
        if raw == "" and fallback is not None:
            return fallback
        parts = raw.split()
        if (len(parts) == 3
                and parts[0] in clueAgent.weaponsAll
                and parts[1] in clueAgent.roomsAll
                and parts[2] in clueAgent.peopleAll):
            return tuple(parts)
        print("Please enter a valid weapon, room, and person, in that order.")


def runGame(players, hands, solution, faceUp, trackers, humanMixEvery):
    n = len(players)
    turnIndex = 0
    turnsTaken = 0

    if faceUp:
        print("\nFace-up in the middle:", ", ".join(faceUp))

    while turnsTaken < MAX_TURNS:
        turnsTaken += 1
        current = players[turnIndex]
        curNum = current["num"]
        tracker = trackers[curNum]
        tracker["turnCount"] += 1
        mixEvery = humanMixEvery if current["isHuman"] else current["mixEvery"]
        pools = computePools(tracker, players, faceUp)

        label = colorText(f"Player {curNum} ({current['character'].capitalize()})", current["color"])
        rollDice(2, label=label, animate=current["isHuman"])

        if current["isHuman"]:
            print(colorText(f"\n--- Your turn (Player {curNum}) ---", "cyan", bold=True))
            printHumanStatus(tracker, players, hands[curNum], pools)
            action = input("Type 'ask' to suggest, 'accuse' to name the solution, or 'pass': ").strip().lower()

            if action == "accuse":
                guess = input("Weapon room person: ").split()
                if tuple(guess) == solution:
                    print(colorText("Correct! You win!", "green", bold=True))
                    reveal(solution)
                    return
                print("Incorrect. The game continues.")
                turnIndex = (turnIndex + 1) % n
                continue

            if action == "pass":
                turnIndex = (turnIndex + 1) % n
                continue

            suggestion, rationale = clueAgent.suggestQuestion(
                pools["weapon"], pools["room"], pools["person"],
                hands[curNum], tracker["askCounts"], tracker["turnCount"], mixEvery,
            )
            print("Suggested question: " + " / ".join(suggestion))
            for line in rationale:
                print("  - " + line)
            question = readSuggestion("Press Enter to use it, or type 'weapon room person': ", suggestion)
        else:
            suggestion, rationale = clueAgent.suggestQuestion(
                pools["weapon"], pools["room"], pools["person"],
                hands[curNum], tracker["askCounts"], tracker["turnCount"], mixEvery,
            )
            question = suggestion
            print(f"\n{label} suggests: " + " / ".join(question))

        for card in question:
            for t in trackers.values():
                t["askCounts"][card] = t["askCounts"].get(card, 0) + 1

        whoAnswered, matches = resolveAnswer(players, curNum, question, hands)
        revealedCard = None

        if whoAnswered is not None:
            answerer = players[whoAnswered - 1]
            if current["isHuman"]:
                revealedCard = random.choice(matches)
                print(f"Player {whoAnswered} ({answerer['character'].capitalize()}) shows you: {revealedCard}")
            elif answerer["isHuman"]:
                print(f"Player {curNum} ({current['character'].capitalize()}) asks you to disprove.")
                print("Your matching card(s):", ", ".join(matches))
                while True:
                    revealedCard = input("Which card do you show them? ").strip()
                    if revealedCard in matches:
                        break
                    print("Must be one of your matching cards.")
            else:
                revealedCard = random.choice(matches)
                print(f"Player {whoAnswered} ({answerer['character'].capitalize()}) shows Player {curNum} a card.")
        else:
            print("No one could disprove the suggestion.")

        applyEvent(trackers, players, curNum, whoAnswered, question, revealedCard)

        if not current["isHuman"]:
            pools = computePools(tracker, players, faceUp)
            if all(len(pools[k]) == 1 for k in pools):
                guess = (pools["weapon"][0], pools["room"][0], pools["person"][0])
                label = colorText(f"Player {curNum} ({current['character'].capitalize()})", current["color"])
                print(f"\n{label} accuses: " + " / ".join(guess) + "!")
                if guess == solution:
                    print(colorText("They were right! Game over.", "yellow", bold=True))
                    reveal(solution)
                    return
                print("They were wrong -- unusual, but play continues.")

        turnIndex = (turnIndex + 1) % n

    print("\nNo one solved it within the turn limit.")
    reveal(solution)


def main():
    print(colorText("\n########  CLUE TABLE SETUP  ########", "magenta", bold=True))
    numberOfPlayers = promptInt("How many people are playing? ", 2, 6)
    players = assignPlayers(numberOfPlayers)

    printRoster(players)
    printBoard()
    print(buildSeatingTable([(f"P{p['num']}:{p['character'][:6]}", p["color"]) for p in players]))

    print(colorText("\nYou go first.", "cyan", bold=True))
    humanMixEvery = promptInt("Mix in one of your own cards how often (every N suggestions)? ", 1, 10)

    solution, hands, faceUp = dealCards(players)
    trackers = initTrackers(players, hands, faceUp)

    print(colorText("\n=== Game start ===", "cyan", bold=True))
    runGame(players, hands, solution, faceUp, trackers, humanMixEvery)


if __name__ == "__main__":
    main()
