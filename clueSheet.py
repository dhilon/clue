weaponsAll = ["pipe", "wrench", "candlestick", "pistol", "dagger", "rope"]
roomsAll = ["kitchen", "living", "garage", "bedroom", "bathroom", "office", "dining", "game", "courtyard"]
peopleAll = ["scarlet", "white", "mustard", "green", "peacock", "plum"]

weapons = weaponsAll.copy()
rooms = roomsAll.copy()
people = peopleAll.copy()


def GameIsNotOver(w, r, p):
    if len(w) == 1 and len(r) == 1 and len(p) == 1:
        return False
    return True


def printOptionsLeft():
    print("Weapons left: " + ", ".join(weapons))
    print("Rooms left: " + ", ".join(rooms))
    print("People left: " + ", ".join(people))


def printTable(numberOfPlayers, couldBeIn, guaranteedCards, skippedCards, yourPlayer):
    print("\n=== Player Table ===")
    for i in range(numberOfPlayers):
        label = f"Player {i + 1}" + (" (you)" if i + 1 == yourPlayer else "")
        guaranteed = ", ".join(sorted(guaranteedCards[i])) if guaranteedCards[i] else "none"
        potential = ", ".join(sorted(couldBeIn[i])) if couldBeIn[i] else "none"
        ruledOut = ", ".join(sorted(skippedCards[i])) if skippedCards[i] else "none"
        print(f"{label}: guaranteed = [{guaranteed}] | potential = [{potential}] | ruled out (skipped) = [{ruledOut}]")
    print("====================\n")


def categoryOf(card):
    if card in weaponsAll:
        return weapons
    if card in roomsAll:
        return rooms
    if card in peopleAll:
        return people
    return None


def isValidCard(card):
    return card in weaponsAll or card in roomsAll or card in peopleAll


def eliminateCard(card):
    lst = categoryOf(card)
    if lst is not None and card in lst:
        lst.remove(card)


def computeSkippedPlayers(asker, answerer, n):
    skipped = []
    i = asker % n + 1
    while i != answerer:
        skipped.append(i)
        i = i % n + 1
    return skipped


def promptInt(promptText, minValue, maxValue, allowFalse=False):
    while True:
        raw = input(promptText).strip()
        if allowFalse and raw.lower() == "false":
            return None
        try:
            value = int(raw)
        except ValueError:
            print("Please enter a whole number" + (" or 'False'." if allowFalse else "."))
            continue
        if minValue <= value <= maxValue:
            return value
        print(f"Please enter a number between {minValue} and {maxValue}.")


def promptAsker(promptText, minValue, maxValue, default):
    while True:
        raw = input(promptText).strip()
        if raw == "":
            return default
        try:
            value = int(raw)
        except ValueError:
            print("Please enter a whole number, or press Enter to accept the suggestion.")
            continue
        if minValue <= value <= maxValue:
            return value
        print(f"Please enter a number between {minValue} and {maxValue}.")


numberOfPlayers = promptInt("How many people are playing? ", 2, 6)

totalDealtCards = len(weaponsAll) + len(roomsAll) + len(peopleAll) - 3
extraCount = totalDealtCards % numberOfPlayers
if extraCount:
    print(
        f"{totalDealtCards} cards can't be split evenly among {numberOfPlayers} players "
        f"({extraCount} left over)."
    )
    while True:
        middleCards = input(
            f"What {extraCount} card(s) are shown face-up in the middle? "
        ).split()
        if len(middleCards) == extraCount and all(isValidCard(c) for c in middleCards):
            break
        print(f"Please enter exactly {extraCount} valid card name(s).")
    for card in middleCards:
        eliminateCard(card)

printOptionsLeft()

firstLeads = input("What are your first leads? ").split()
index = 0
while index < len(firstLeads):
    card = firstLeads[index]
    if isValidCard(card):
        eliminateCard(card)
        index += 1
    else:
        print("Invalid entry:", card)
        firstLeads[index] = input("Provide corrected lead: ")

yourPlayer = promptInt("Enter what position player you are: ", 1, numberOfPlayers)

couldBeOut = [set() for _ in range(numberOfPlayers)]
couldBeIn = [set() for _ in range(numberOfPlayers)]
guaranteedCards = [set() for _ in range(numberOfPlayers)]
skippedCards = [set() for _ in range(numberOfPlayers)]
guaranteedCards[yourPlayer - 1].update(firstLeads)

solutionWeapon = None
solutionRoom = None
solutionPerson = None

nextAsker = 1
while GameIsNotOver(weapons, rooms, people):
    printTable(numberOfPlayers, couldBeIn, guaranteedCards, skippedCards, yourPlayer)
    printOptionsLeft()

    askerNum = promptAsker(
        f"Which player is asking (1-{numberOfPlayers})? [Enter for Player {nextAsker}] ",
        1, numberOfPlayers, nextAsker
    )

    while True:
        playerQuestion = input(
            f"Player {askerNum}, what three cards did they ask about (weapon room person)? "
        ).split()
        if (len(playerQuestion) == 3
                and playerQuestion[0] in weaponsAll
                and playerQuestion[1] in roomsAll
                and playerQuestion[2] in peopleAll):
            break
        print("Please enter a valid weapon, room, and person, in that order.")

    whoAnswered = promptInt(
        f"Which player answered Player {askerNum}'s question? Type 'False' if no one could. ",
        1, numberOfPlayers, allowFalse=True
    )

    if whoAnswered is None:
        solutionWeapon, solutionRoom, solutionPerson = playerQuestion
        break

    skippedPlayers = computeSkippedPlayers(askerNum, whoAnswered, numberOfPlayers)
    for playerNum in skippedPlayers:
        couldBeOut[playerNum - 1].update(playerQuestion)
        skippedCards[playerNum - 1].update(playerQuestion)
    if skippedPlayers:
        print("Deduced that these players couldn't help:", ", ".join(f"Player {p}" for p in skippedPlayers))

    if askerNum == yourPlayer:
        while True:
            giveCard = input(f"Player {whoAnswered}, what card did they show you? ")
            if giveCard in playerQuestion:
                break
            print("That has to be one of the three cards you just asked about.")
        eliminateCard(giveCard)
        guaranteedCards[whoAnswered - 1].add(giveCard)
        for i in range(numberOfPlayers):
            couldBeOut[i].discard(giveCard)
            couldBeIn[i].discard(giveCard)
    else:
        couldBeIn[whoAnswered - 1].update(playerQuestion)

    changed = True
    while changed:
        changed = False
        for i in range(numberOfPlayers):
            before = len(couldBeIn[i])
            couldBeIn[i] -= couldBeOut[i]
            if len(couldBeIn[i]) != before:
                changed = True
            if len(couldBeIn[i]) == 1:
                card = next(iter(couldBeIn[i]))
                eliminateCard(card)
                guaranteedCards[i].add(card)
                couldBeIn[i].clear()
                for j in range(numberOfPlayers):
                    if j != i and card not in couldBeOut[j]:
                        couldBeOut[j].add(card)
                        changed = True

    nextAsker = askerNum % numberOfPlayers + 1

if solutionWeapon is None:
    solutionWeapon = weapons[0]
    solutionRoom = rooms[0]
    solutionPerson = people[0]

print("It was", solutionPerson, "with the", solutionWeapon, "in the", solutionRoom)
