'''Solitaire game, written by Victor Norman.
Date: Nov. 25, 2016
'''

import random

DEBUG = True


class Card:
    '''Card class: contains num and suit and allows one to compare
    two cards for equality -- based on number only.
    Ace is 14.
    String representation is NNS -- two spaces for the number and 1
    space for the suit.  J = jack, Q = queen, K = king, A = ace.
    '''

    def __init__(self, num, suit):
        '''Hold information about a card: its num and suit, whether it is
        showing or not, whether it is locked down or not, its x,y position, etc.'''

        # num is a string ('2', '3', ... 'jack', 'queen', etc.): convert to
        # integer 2 - 14.
        try:
            self._num = int(num)
        except:
            # Must be jack, queen, etc.
            if num == 'J':
                self._num = 11
            elif num == 'Q':
                self._num = 12
            elif num == 'K':
                self._num = 13
            else:
                self._num = 14
        self._suit = suit

        # For use in games, when a card is worth a certain number of points.
        self._points = 0

    def __eq__(self, other):
        return self._num == other._num and self._suit == other._suit

    def getNum(self):
        return self._num

    def getSuit(self):
        return self._suit

    def getPoints(self):
        return self._points

    def setPoints(self, pts):
        if DEBUG:
            print('for card', str(self), 'points set to ', pts)
        self._points = pts

    def __str__(self):
        if self._num <= 10:
            res = str(self._num)
        elif self._num == 11:
            res = 'J'
        elif self._num == 12:
            res = 'Q'
        elif self._num == 13:
            res = 'K'
        else:
            res = 'A'
        return "%3s" % (res + self._suit)


class Deck:
    '''Deck class: contains a list of card objects.'''

    NUMS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    SUITS = ['C', 'H', 'D', 'S']

    def __init__(self, cards=None):
        self._deck = []
        if cards is not None:
            self._deck.extend(cards)

    def __str__(self):
        res = []
        for card in self._deck:
            res.append(str(card))
        return str(res)

    def addCard(self, card):
        self._deck.append(card)

    def addCards(self, cards):
        self._deck.extend(cards)

    def shuffle(self):
        random.shuffle(self._deck)

    def addAllCards(self):
        '''Create all card for a deck and shuffle the deck.
        '''
        for numIdx in range(len(self.NUMS)):
            for suitIdx in range(len(self.SUITS)):
                card = Card(self.NUMS[numIdx], self.SUITS[suitIdx])
                self.addCard(card)
        self.shuffle()

    def takeTopCard(self):
        return self._deck.pop(0)

    def numCards(self):
        return len(self._deck)

    def getCards(self):
        '''Return the list of card objects.'''
        return self._deck

    def makeCopy(self):
        return Deck(self._deck)
