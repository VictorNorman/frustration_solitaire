'''Solitaire game, written by Victor Norman.
Date: Nov. 25, 2016
'''

from card import *

DEBUG = True


class Board:
    '''A representation of a board for the card game.  It keeps
    track of the location of cards in 4 rows and 13 columns.
    Checks if moves are legal, clears the board of "bad" cards
    after a round, etc.
    '''

    NUM_ROWS = 4
    NUM_COLS = 13

    def __init__(self):
        grid = []
        for i in range(self.NUM_ROWS):
            row = []
            for j in range(self.NUM_COLS):
                row.append(None)
            grid.append(row)
        self._board = grid

    def __str__(self):
        res = ''
        for row in range(self.NUM_ROWS):
            for col in range(self.NUM_COLS):
                if self._board[row][col] is None:
                    res += "    "
                else:
                    res += str(self._board[row][col]) + " "
            res += "\n"
        return res

    def reinit(self):
        for row in range(self.NUM_ROWS):
            for col in range(self.NUM_COLS):
                self._board[row][col] = None

    def getCardAt(self, row, col):
        return self._board[row][col]

    def getAllCards(self):
        '''Return a list of all cards on the board.'''
        res = []
        for row in range(self.NUM_ROWS):
            for col in range(self.NUM_COLS):
                if self._board[row][col] is not None:
                    res.append(self._board[row][col])
        return res

    def layoutCards(self, deck):
        '''Add cards from the deck to the board, replacing
        all "Nones".
        '''
        for row in range(self.NUM_ROWS):
            for col in range(self.NUM_COLS):
                if self._board[row][col] is None:
                    self._board[row][col] = deck.takeTopCard()

        # All cards should be placed now.
        assert deck.numCards() == 0

    def removeAces(self):
        '''Remove the Aces from the board and return them.'''
        aces = []
        for row in range(self.NUM_ROWS):
            for col in range(self.NUM_COLS):
                card = self._board[row][col]
                assert card is not None
                if card.getNum() == 14:  # Ace
                    aces.append(card)
                    self._board[row][col] = None
        assert len(aces) == 4
        return aces

    def _isLegalMove(self, card, toRow, toCol):
        '''Return True iff the given card can be legally
        moved to the given space at (toRow,toCol).  This
        will be True only if the number of the card to the
        left of the location is 1 less than the cards number
        (and the suits are the same) OR if the card is a 2 and the column is 0.
        '''
        # Check that the location is empty.
        if self._board[toRow][toCol] is not None:
            return False
        if card.getNum() == 2 and toCol == 0:
            return True
        leftCard = self._board[toRow][toCol-1]
        if leftCard is None:
            # Happens when two spaces are next to each other.
            return False

        return leftCard.getNum() == card.getNum() - 1 and \
            leftCard.getSuit() == card.getSuit()

    def moreMoves(self):
        '''return True iff there are more moves possible.  There are
        no more moves when all spaces are "behind" Kings.'''
        for row in range(self.NUM_ROWS):
            for col in range(self.NUM_COLS):
                if self._board[row][col] is None:
                    # empty space all the way to the left means you can move.
                    if col == 0:
                        return True
                    if self._board[row][col-1] is not None and \
                            self._board[row][col-1].getNum() != 13:  # King
                        return True
        return False

    def getMoveableCardDest(self, card):
        '''find an empty space where the given card will legally go.
        Return (row, col) or None if the card cannot be moved.
        '''
        for row in range(self.NUM_ROWS):
            for col in range(self.NUM_COLS):
                if self._board[row][col] is None:
                    if self._isLegalMove(card, row, col):
                        return (row, col)
        return None

    def gameCompletelyDone(self):
        '''The game is done when all cards are in the right order
        and the spaces are all the way to the right.'''

        for row in range(self.NUM_ROWS):
            # Check if leftmost card in the row is a 2.
            leftCard = self._board[row][0]
            if leftCard is None:
                return False
            if leftCard.getNum() != 2:
                return False
            # Check if the rightmost slot in the row is None.
            if self._board[row][self.NUM_COLS-1] is not None:
                return False

            # Get the suit "of the row".
            thisRowSuit = leftCard.getSuit()

            for col in range(1, self.NUM_COLS - 1):
                card = self._board[row][col]
                if card is None:
                    return False
                if card.getSuit() != thisRowSuit:
                    return False
                if card.getNum() != leftCard.getNum() + 1:
                    return False

                # Done checking this one: go on to the next
                # card to the right, and this card becomes
                # leftcard.
                leftCard = card
        return True

    def moveCard(self, card, fromRow, fromCol, toRow, toCol):
        assert self._board[toRow][toCol] is None
        self._board[toRow][toCol] = card
        self._board[fromRow][fromCol] = None

    def findCard(self, cardNum, cardSuit):
        '''Find a card given its number and suit.  If the card is
        not on the board, return None.  If it is found, return a
        triple: (cardobject, row, col)
        '''
        try:
            c = Card(cardNum, cardSuit)
        except Exception as e:
            print("Could not create the card with -->" +
                  cardNum + "<->" + cardSuit + "<--")
            raise e
        for row in range(self.NUM_ROWS):
            for col in range(self.NUM_COLS):
                if self._board[row][col] is not None and \
                   self._board[row][col] == c:
                    return (self._board[row][col], row, col)
        return None

    def findCardLocation(self, card: Card):
        '''Given a card, find where it is on the board and return
        a tuple (row, col). If not found (which should never happen),
        return (None, None)'''

        for row in range(self.NUM_ROWS):
            for col in range(self.NUM_COLS):
                if self._board[row][col] is not None and \
                        self._board[row][col] == card:
                    return (row, col)
        return (None, None)

    def findPlayableCards(self):
        '''Find the cards that can be played into the open spots.
        Return them as a list of tuples (card, row, col),
        where the row, col is where the card is.
        '''

        # Find the cards before the empty slots.
        res = []
        for row in range(self.NUM_ROWS):
            for col in range(self.NUM_COLS-1):
                # Skip empty spaces and Kings.
                if self._board[row][col] is None:
                    continue
                if self._board[row][col].getNum() == 13:  # King
                    continue
                # If the card to the right is an empty space...
                if self._board[row][col+1] is None:
                    res.append((self._board[row][col], row, col))

        # For each card in res, find the card that goes in the
        # slot to the right.
        res2 = []
        for card, row, col in res:
            nextCard = self.findCard(card.getNum() + 1, card.getSuit())
            res2.append(nextCard)

        # Look for empty spaces in column 0.  If there is at least one,
        # then find all 2s and add them to the list to be returned.
        roomForATwo = False
        for row in range(self.NUM_ROWS):
            if self._board[row][0] is None:
                roomForATwo = True
                break
        if roomForATwo:
            for row in range(self.NUM_ROWS):
                # Allow 2s to be moved from one row to another, so
                # don't skip looking at column 0.
                for col in range(self.NUM_COLS):
                    card = self._board[row][col]
                    if card is not None and card.getNum() == 2:
                        res2.append((card, row, col))

        if DEBUG:
            print("Playable cards: ",
                  ', '.join([str(card) for card, row, col in res2]))
        return res2

    def resetBoard(self):
        '''After there are no more moves (all blanks are to the right
        of Kings), then clear all cards that arent in the correct
        place.  Put them back in the deck, add the aces back, shuffle,
        lay them out, and remove the aces.
        Used only for the text-based version of the game.'''

        discarded = self.removeIncorrectCards()
        deck = Deck(discarded)
        # Add the aces back.
        deck.addCard(Card(14, 'D'))
        deck.addCard(Card(14, 'H'))
        deck.addCard(Card(14, 'S'))
        deck.addCard(Card(14, 'C'))
        deck.shuffle()
        self.layoutCards(deck)
        self.removeAces()

    def removeIncorrectCards(self):
        '''Remove cards that have not be placed in the correct
        positions as part of the solution.  Return them in a list.'''

        # Bad card has a number != col + 2.
        bad = []
        for row in range(self.NUM_ROWS):
            col = 0
            thisRowSuit = self._board[row][col].getSuit()
            cleaningRow = False  # true when we find first bad card.

            while col < 13:
                card = self._board[row][col]
                if cleaningRow:
                    if card is not None:
                        bad.append(card)
                        self._board[row][col] = None
                    col += 1
                else:
                    # This happens when we have a row complete
                    # and the first thing wrong we see is an
                    # empty space at the end in column 12.
                    if card is None:
                        col += 1
                        continue
                    if card.getSuit() != thisRowSuit:
                        cleaningRow = True
                    elif card.getNum() != col + 2:
                        cleaningRow = True
                    # else the card is the correct suit and
                    # correct number: it must be in place!
                    else:
                        col += 1
        return bad

    def getCardsInPlace(self):
        '''Return a list of (card, row, col) tuples for the cards that have been
        placed correctly as part of the solution.
        '''
        goodCards = []
        for row in range(self.NUM_ROWS):
            col = 0
            card = self._board[row][col]
            if card is None:
                # Whole row is bad: first card is empty slot.
                continue
            thisRowSuit = card.getSuit()

            while col < 13:
                card = self._board[row][col]
                if card is None:
                    break
                if card.getSuit() != thisRowSuit:
                    break
                elif card.getNum() != col + 2:
                    break
                # else the card is the correct suit and
                # correct number: it must be in place!
                else:
                    goodCards.append((card, row, col))
                    col += 1
        return goodCards

    def countCardsInPlace(self):
        '''Count and return the number of cards that have been
        placed correctly as part of the solution.
        '''

        badCardCt = 0
        for row in range(self.NUM_ROWS):
            col = 0
            card = self._board[row][col]
            if card is None:
                # Whole row is bad: first card is empty slot.
                badCardCt += 12
                continue
            thisRowSuit = card.getSuit()

            while col < 13:
                card = self._board[row][col]
                if card is None:
                    badCardCt += self.NUM_COLS - 1 - col
                    break
                if card.getSuit() != thisRowSuit:
                    badCardCt += self.NUM_COLS - 1 - col
                    break
                elif card.getNum() != col + 2:
                    badCardCt += self.NUM_COLS - 1 - col
                    break
                # else the card is the correct suit and
                # correct number: it must be in place!
                else:
                    col += 1
        return 48 - badCardCt

    def findLowerCard(self, card):
        '''Find the card that is one "lower" than the given card.
        E.g., if card is 7D, find 6D.  Return the card, its row, and
        column in a 3-ple.  return (None * 3) if no lower card is found.'''
        for row in range(self.NUM_ROWS):
            for col in range(self.NUM_COLS):
                lcard = self._board[row][col]
                if lcard is None:
                    continue
                if lcard.getSuit() == card.getSuit() and \
                        lcard.getNum() == card.getNum() - 1:
                    return (lcard, row, col)
        return (None, None, None)
