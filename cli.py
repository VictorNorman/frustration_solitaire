'''Play a text-only solitaire game.
Author: Victor Norman.
'''

from card import *
from board import *

d = Deck()
d.addAllCards()

bd = Board()

bd.layoutCards(d)
print(bd)

print("\nRemoving Aces...\n")
bd.removeAces()

round = 1

while True:
    print(bd)
    print("You have %d cards in place" % bd.countCardsInPlace())
    src = input("Enter card to move: ").strip().upper()
    # src could be 3H or 10S, etc.  In any case,
    # the last letter is the suit and the first letter or
    # letters are the number.
    # findCard() returns a 3-ple: (card, row, col)
    #    or None if it isn't found.
    res = bd.findCard(src[0:-1], src[-1])
    if res is None:
        print("Cannot find that card in the board")
        continue

    if bd.gameCompletelyDone():
        break

    # This is a while because after reset
    # we may have put all aces after kings again.
    while not bd.moreMoves():
        print("No more moves!")
        print(bd)
        bd.resetBoard()
        round += 1
        print("Starting round %d with %d cards in place" % (round, bd.countCardsInPlace()))

print(bd)
print("You won in %d rounds!" % round)

    


