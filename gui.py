'''Solitaire game, written by Victor Norman.
Date: Nov. 25, 2016
'''

from tkinter import *

from card import *
from board import *


LEFT_CARD_PADDING = 10
CARD_AREA_WIDTH = 90
CARD_AREA_HEIGHT = 125
CARD_WIDTH = 75
CARD_HEIGHT = 109


class CardImg:
    '''This class encapsulates an image to represent a card, reading the
    image from a file in images/ and creating a Canvas image for it.
    '''

    TRANSLATE_NUM = {2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8',
                     9: '9', 10: '10', 11: 'jack', 12: 'queen', 13: 'king', 14: 'ace'}
    TRANSLATE_SUIT = {'D': 'diamonds',
                      'H': 'hearts', 'C': 'clubs', 'S': 'spades'}

    def __init__(self, card, canv):
        '''Constructor: creates the image for the given card, and stores the
        tag and id for the cardimg.
        '''
        self._card = card   # the Card object
        self._canv = canv

        num = card.getNum()
        num = self.TRANSLATE_NUM[num]
        suit = card.getSuit()
        suit = self.TRANSLATE_SUIT[suit]
        self._tag = num + "_of_" + suit
        self._img = PhotoImage(file='images/' + self._tag + ".gif")

        # Create the card image at 0, 0
        self._id = self._canv.create_image(0, 0, image=self._img, tags=self._tag,
                                           anchor=NW, state=HIDDEN)

    def getImg(self):
        return self._img

    def getTag(self):
        return self._tag

    def setId(self, id):
        self._id = id

    def getId(self):
        return self._id


class BoardGui:
    '''Handle layout of cards on the BOARD.'''

    def __init__(self, board, canv):
        self._board = board
        self._canv = canv

    def displayLayout(self, card2ImgDict):
        '''Go through the cards on the board object and lay them
        out on the canvas.  Translation of the Card object to its
        corresponding CardImg object is done through the given
        card2ImgDict dictionary.
        '''

        # Each card image is 75x109 pixels.
        for ridx in range(4):
            for cidx in range(13):
                card = self._board.getCardAt(ridx, cidx)
                if card is None:
                    continue

                cardimg = card2ImgDict[id(card)]

                x = LEFT_CARD_PADDING + cidx * CARD_AREA_WIDTH
                y = LEFT_CARD_PADDING + ridx * CARD_AREA_HEIGHT
                currx, curry = self._canv.coords(cardimg.getId())
                # move() is relative so we have to figure out the diff.
                self._canv.move(cardimg.getId(), x - currx, y - curry)
                # Make sure the card can be seen.
                self._canv.itemconfig(cardimg.getTag(), state=NORMAL)

                # Put a little delay in, so it looks like the cards are
                # being dealt out one-by-one.
                self._canv.after(20)
                self._canv.update()

    def moveCard(self, cardimg, toRow, toCol):
        '''Move a cardimg from where it is not to the given
        row and col on this BoardGui.'''
        currx, curry = self._canv.coords(cardimg.getId())
        destx = LEFT_CARD_PADDING + toCol * CARD_AREA_WIDTH
        desty = LEFT_CARD_PADDING + toRow * CARD_AREA_HEIGHT
        # canvas.move is relative, so to do absolute move we have
        # to subtract currx/y from destx/y.
        self._canv.move(cardimg.getId(), destx - currx, desty - curry)


class App:
    '''The main card game application.  This GUI creates a Deck and Board
    model objects and uses them to keep track of legal moves, where the
    cards are on the board, etc., and then displays card images for the
    cards on a created BoardGui (the GUI view).
    '''

    def __init__(self, window):
        '''Store the main window, create the Board and Deck models;
        create the main Canvas and all the buttons and labels to allow
        the user to manipulate the game.
        '''

        self._window = window

        self._board = Board()
        self._deck = Deck()
        self._deck.addAllCards()
        # We'll fill this in when we remove the aces from the board.
        self._removedAces = []

        self._canv = Canvas(window, bg="darkgreen", width=13 * CARD_AREA_WIDTH,
                            height=4 * CARD_AREA_HEIGHT)
        self._canv.pack()

        self._buttonFr = Frame(window)
        self._buttonFr.pack()

        btNewGame = Button(self._buttonFr, text="New Game",
                           command=self.newGame)
        btNewGame.pack(side=LEFT, padx=10)

        self._roundNum = 1
        self._roundNumLbl = Label(self._buttonFr, text="Round: 1  ")
        self._roundNumLbl.pack(side=LEFT)

        self._cardsInPlaceText = StringVar()
        self._cardsInPlace = self._board.countCardsInPlace()
        self._cardsInPlaceText.set("Cards in place: %d" % self._cardsInPlace)
        cardsInPlaceNum = Label(
            self._buttonFr, textvariable=self._cardsInPlaceText)
        cardsInPlaceNum.pack(side=LEFT)
        self_score = 0
        self._scoreText = StringVar()
        self._scoreText.set("Score: 0 (10 pts per card this round)")
        self._scoreLabel = Label(self._buttonFr, textvariable=self._scoreText)
        self._scoreLabel.pack(side=LEFT)

        self._btNextRound = Button(self._buttonFr, text="Next Round", state=DISABLED,
                                   command=self.nextRound)
        self._btNextRound.pack(side=LEFT, padx=10)

        self._dispPtsLabel = None
        self._dispPtsLabelId = None

        try:
            f = open("./highscores.txt", "r")
            self._highScore = int(f.read().strip())
            f.close()
        except:
            self._highScore = 0

        self._highScoreLbl = Label(
            self._buttonFr, text="High Score: " + str(self._highScore))
        self._highScoreLbl.pack(side=RIGHT)

        self._boardGui = BoardGui(self._board, self._canv)

        # A mapping from canvas id to the CardImg object for each image.
        self._imgDict = {}

        # A mapping from card object to CardImg object.  We do it this way
        # so that the card object (in the model) remains agnostic of the view
        # being used on it.
        self._card2ImgDict = {}

        # A mapping from Card object to CardImg object.  This is needed so
        # that we map a card in the board layout to the CardImg, which should
        # then be placed at a certain location.  (We don't keep a reference to
        # the CardImg in Card because it just shouldn't know how it is displayed.)

        cards = self._deck.getCards()
        for card in cards:
            cardimg = CardImg(card, self._canv)

            imgid = cardimg.getId()
            self._imgDict[imgid] = cardimg
            self._canv.tag_bind(imgid, "<ButtonPress-1>", self.onCardClick)

            self._card2ImgDict[id(card)] = cardimg

        self.initNewGame()

    def removeAces(self):
        '''Go through the board and remove the aces from the board.
        Then hide the corresponding CardImgs in the BoardGui for the
        aces.
        '''
        self._removedAces = self._board.removeAces()
        for card in self._removedAces:
            self._canv.itemconfig(
                self._card2ImgDict[id(card)].getTag(), state=HIDDEN)

        if self.isEndOfRoundOrGame():
            return

        self.highlightMovableCards()

    def highlightMovableCards(self):
        '''Get the cards that have a space after them, find the cards
        that could go in those spaces, and draw a rectangle around those
        cards.
        '''
        # Return is a list of tuples (card, row, col)
        # where the row, col is where the card is
        crc = self._board.findPlayableCards()
        for cardinfo in crc:
            # row, col is where it can go... which we don't care about.
            # break cardinfo into 3-ple, where row, col is where the card is.
            card, row, col = cardinfo
            self.drawOutline(row, col, "yellow", "movable")

    def drawOutline(self, row, col, color, tag):
            # draw highlight around row,col card spot.
        x = LEFT_CARD_PADDING + col * CARD_AREA_WIDTH
        y = LEFT_CARD_PADDING + row * CARD_AREA_HEIGHT
        self._canv.create_rectangle(x-5, y-5, x + CARD_WIDTH + 5, y + CARD_HEIGHT + 5,
                                    width=3, tag=tag, outline=color)

    def nextRound(self):
        '''Callback for when the user clicks the "Next Round" button.
        Increment the round number counter;
        Remove the cards from the board that are not in the correct place;
        Add those cards, and the aces, back to the deck; shuffle it;
        Update the display to show the good cards only, for 1 second;
        Register nextRoundContined() to be called.
        '''

        self._roundNum += 1
        self._roundNumLbl.config(text="Round: " + str(self._roundNum) + "  ")
        discarded = self._board.removeIncorrectCards()
        assert self._deck.numCards() == 0
        self._deck.addCards(discarded)
        # Add the aces back to the deck.
        for card in self._removedAces:
            self._deck.addCard(card)
        self._deck.shuffle()

        # display the board with only "good cards" for 1 second.
        for card in discarded:
            cardimg = self._card2ImgDict[id(card)]
            self._canv.itemconfig(cardimg.getTag(), state=HIDDEN)

        self._scoreText.set("Score: %d (%d pts per card this round)" %
                            (self._score, self._getPtsPerCard()))

        self._canv.after(1000, self.nextRoundContinued)

    def nextRoundContinued(self):
        '''Continuation of nextRound():
        Lay out all the cards from the deck on the board;
        Update the button states;
        Wait to 2 seconds, then call removeAces().
        '''

        # Deck is shuffled.  Now, add cards to the board.
        self._board.layoutCards(self._deck)
        self._boardGui.displayLayout(self._card2ImgDict)

        self._btNextRound.config(state=DISABLED)
        # After 1.5 seconds of showing all cards, remove the aces.
        self._canv.after(1500, self.removeAces)

    def newGame(self):
        '''Called back when New Game button is pressed.
        Similar steps to nextRound/__init__.
        '''

        self._roundNum = 1
        self._roundNumLbl.config(text="Round: " + str(self._roundNum) + "  ")
        assert self._deck.numCards() == 0

        # Add all the cards on the board to the deck.
        self._deck.addCards(self._board.getAllCards())
        if self._deck.numCards() == 48:
            # The board had aces removed, so add the aces back to the deck.
            for card in self._removedAces:
                self._deck.addCard(card)
        self._deck.shuffle()
        self._board.reinit()

        self.initNewGame()

    def initNewGame(self):
        self._canv.delete("good-outlines")
        self._board.layoutCards(self._deck)
        self._boardGui.displayLayout(self._card2ImgDict)
        self._cardsInPlace = self._board.countCardsInPlace()
        self._cardsInPlaceText.set("Cards in place: %d" % self._cardsInPlace)
        self._score = self._cardsInPlace * 10
        self._scoreText.set(
            "Score: %d (10 pts per card this round)" % self._score)
        self.redrawGoodCardOutlines()

        # Disable the "next round" button.
        self._btNextRound.config(state=DISABLED)
        self._canv.after(1500, self.removeAces)

    def onCardClick(self, event):
        '''Called back when a card is clicked to be moved into an open spot:
        Figure out when card was clicked using the _imgDict to map id to cardImg.
        Find the related card object in the board, and from that, the cards
          current row/col.
        Check with the board object to see if the card can be moved and if so
          what is the dest row/col.
        Move the card in the board and in the boardGui.
        Check if there are more moves, the game is done, etc.
        '''

        # print("onCardClick", event.widget, "at", event.x, ",", event.y)
        item = event.widget.find_closest(event.x, event.y)
        # print(item)
        # Item is a one-ple (id, ) (only 1 thing in it)
        item = item[0]
        cardimg = self._imgDict[item]
        # print(cardimg._card)
        cardName = str(cardimg._card)

        # card._card is like "9C" or "10D" or "JH"...
        # print("Looking for -->%s<--, -->%s<--" % (cardName[0:-1], cardName[-1]))
        res = self._board.findCard(cardName[0:-1].strip(), cardName[-1])
        # findCard() returns a 3-ple: (card, row, col)
        #    or None if it isn't found.
        if res is None:
            print("Card %s not found" % cardName)
            return
        card, fromRow, fromCol = res  # split into the 3 parts.

        assert cardimg._card == card

        res = self._board.getMoveableCardDest(card)
        if res is None:
            print("Cannot move that card.")
            return
        toRow, toCol = res   # split into the 2 parts.
        # print("Can be moved to %d, %d" % (toRow, toCol))

        # remove all outlines around possible cards to move.
        self._canv.delete("movable")

        cardsInPlaceBeforeMove = self._cardsInPlace
        self._board.moveCard(card, fromRow, fromCol, toRow, toCol)
        self._boardGui.moveCard(cardimg, toRow, toCol)
        self._cardsInPlace = self._board.countCardsInPlace()

        newCardsInPlace = self._cardsInPlace - cardsInPlaceBeforeMove
        if newCardsInPlace > 0:
            self._cardsInPlaceText.set(
                "Cards in place: %d" % self._cardsInPlace)
            ptsPerCard = self._getPtsPerCard()
            newPts = newCardsInPlace * ptsPerCard
            self._score += newPts
            self.displayNewPts(newPts)
            self._scoreText.set("Score: %d (%d pts per card this round)" %
                                (self._score, ptsPerCard))
            self.redrawGoodCardOutlines()

        self._canv.update()

        if self.isEndOfRoundOrGame():
            return

        # Redraw outlines around cards that can be moved.
        self.highlightMovableCards()

    def isEndOfRoundOrGame(self):
        '''Check if the game is over or the round is over.  Return True
        if it is.
        '''
        if self._board.gameCompletelyDone():
            newhigh = False
            # Display the congratulations message for 5 seconds.
            try:
                if self._highScore < self._score:
                    self._highScore = self._score
                    f = open("./highscores.txt", "w")
                    f.write(str(self._highScore) + "\n")
                    f.close()
                    newhigh = True
            except:
                # Cannot write out to the file system.
                newhigh = True

            text = "Congratulations!  You finished the game in %d rounds with a score of %d.\n" % (
                self._roundNum, self._score)
            if newhigh:
                text += "This is a new high score!\n"
                self._highScoreLbl.config(
                    text="High Score: " + str(self._highScore))
            text += "Click the New Game button to play again."

            self.displayMesg(text, 5000)
            return True

        if not self._board.moreMoves():
            self.displayMesg(
                "No more moves. Click Next Round to continue.", 2000)
            self._btNextRound.config(state=NORMAL)
        return False

    def displayMesg(self, mesg, time):
        '''Display the given message on a white rectangle on the board for
        the given number of milliseconds.
        '''
        border = 150
        rect = self._canv.create_rectangle(border, border,
                                           self._canv.winfo_reqwidth() - border,
                                           self._canv.winfo_reqheight() - border,
                                           fill="white")
        self._canv.tag_raise(rect)
        id = self._canv.create_text(self._canv.winfo_reqwidth() / 2,
                                    self._canv.winfo_reqheight() / 2,
                                    text=mesg, font=("Helvetica", 20))
        self._canv.tag_raise(id)
        self._canv.update()
        self._canv.after(time)
        self._canv.delete(id)
        self._canv.delete(rect)
        self._canv.update()

    def _getPtsPerCard(self):
        '''10 pts for round 1, 9 for round 2, etc...'''
        return 11 - self._roundNum

    def displayNewPts(self, pts):
        '''Display a little floating window when a card is put in
        place, to display the new points that were scored.  This is totally
        GUI bling.'''
        self._displayPts = pts
        self._displayNewPtsWinY = self._canv.winfo_reqheight() - 20
        self._dispPtsWinTime = 0
        if self._dispPtsLabel is not None:
            self._canv.delete(self._dispPtsLabelId)
        self._dispPtsLabel = Label(self._canv, text="+" + str(pts),
                                   bg="yellow", fg="black")
        self._dispPtsLabelId = self._canv.create_window(self._canv.winfo_reqwidth() / 2,
                                                        self._displayNewPtsWinY,
                                                        window=self._dispPtsLabel)
        self.updateNewPtsWin()

    def updateNewPtsWin(self):
        self._dispPtsWinTime += 1
        if self._dispPtsWinTime >= 10:
            self._canv.delete(self._dispPtsLabelId)
            self._dispPtsLabel = None
            return
        self._canv.move(self._dispPtsLabelId, 0, -1)
        self._canv.after(100, self.updateNewPtsWin)

    def redrawGoodCardOutlines(self):
        '''Redraw all the black outlines around good cards.'''
        self._canv.delete("good-outlines")
        goodCards = self._board.getCardsInPlace()
        for card, r, c in goodCards:
            self.drawOutline(r, c, "black", "good-outlines")


if __name__ == "__main__":
    root = Tk()
    root.title("Cards")
    app = App(root)
    root.mainloop()
