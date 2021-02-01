from browser import document, html, timer, window, template, local_storage

from card import Card, Deck
from board import Board

# So we don't have to type window.fabric.xxx so much.
fabric = window.fabric

stringify = window.JSON.stringify


DEBUG = False

# Default sizes for
CARD_PADDING = 10
CARD_AREA_WIDTH = 90
CARD_AREA_HEIGHT = 125

CARD_WIDTH = 75
CARD_HEIGHT = 109
CARDS_IN_PLACE_COLOR = "cyan"
MOVABLE_CARD_COLOR = "yellow"

CANVAS_WIDTH = CARD_AREA_WIDTH * 13 + CARD_PADDING / 2
CANVAS_HEIGHT = CARD_AREA_HEIGHT * 4 + CARD_PADDING / 2
CANVAS_COLOR = "darkgreen"


# print("CANVAS_W ", CANVAS_WIDTH)
# print("CANVAS_h ", CANVAS_HEIGHT)
if DEBUG:
    print('window w, h = ', window.innerWidth, window.innerHeight)

aspect_ratio = CANVAS_WIDTH / CANVAS_HEIGHT
# print("for this width, height is", window.innerWidth / aspect_ratio)

if (window.innerWidth / aspect_ratio < window.innerHeight):
    # Window is wider than tall
    CANVAS_WIDTH = window.innerWidth
    CANVAS_HEIGHT = window.innerWidth / aspect_ratio
else:
    # Window is taller than wide
    CANVAS_WIDTH = window.innerHeight * aspect_ratio
    CANVAS_HEIGHT = window.innerHeight


CARD_AREA_WIDTH = CANVAS_WIDTH / 13 - 5
CARD_AREA_HEIGHT = CANVAS_HEIGHT / 4 - 5
CARD_WIDTH = CARD_AREA_WIDTH / 1.2
CARD_HEIGHT = CARD_AREA_HEIGHT / 1.2

if DEBUG:
    print('CARD_AREA_W, H = ', CARD_AREA_WIDTH, CARD_AREA_HEIGHT)
    print('CANVAS_WIDTH, HEIGHT = ', CANVAS_WIDTH, CANVAS_HEIGHT)

if CARD_WIDTH >= 75:
    OUTLINE_WIDTH = 3
else:
    OUTLINE_WIDTH = 1


class CardImg:
    '''This class encapsulates an image to represent a card, reading the
    image from a file. It records where the image is on the canvas, so that
    code can find out which image was clicked.
    '''

    TRANSLATE_NUM = {2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8',
                     9: '9', 10: '10', 11: 'jack', 12: 'queen', 13: 'king', 14: 'ace'}
    TRANSLATE_SUIT = {'D': 'diamonds',
                      'H': 'hearts', 'C': 'clubs', 'S': 'spades'}

    def __init__(self, card: Card, canv):
        '''Constructor: creates the image for the given card and the
        rectangle highlight outline.
        '''
        self._card = card   # the Card object
        self._canv = canv   # fabric canvas

        # based on the card values, build up the name of the image file.
        num = card.getNum()
        num = self.TRANSLATE_NUM[num]
        suit = card.getSuit()
        suit = self.TRANSLATE_SUIT[suit]
        self._image_name = num + "_of_" + suit + ".svg"

        self._loaded = False
        self._displayed = False

        fabric.Image.fromURL(
            "Playing_Cards/SVG-cards-1.3/" + self._image_name,
            self._onload
        )
        self._draw_when_loaded = False

        self._outline = fabric.Rect.new({
            'strokeWidth': OUTLINE_WIDTH,
            'width': CARD_WIDTH + 2 * OUTLINE_WIDTH + 2,
            'height': CARD_HEIGHT + 2 * OUTLINE_WIDTH + 2,
            'selectable': False,
        })
        self._outline_displayed = False

    def _onload(self, img, bogusBoolean):
        self._loaded = True
        self._img = img
        self._img.scaleToWidth(CARD_WIDTH)
        self._img.selectable = False
        if self._draw_when_loaded:
            self._img.left = self._curr_x
            self._img.top = self._curr_y
            self._canv.add(self._img)
            self._displayed = True
            self._draw_when_loaded = False

    def drawOnCanvas(self, x, y):
        self._curr_x = x
        self._curr_y = y
        if not self._loaded:
            self._draw_when_loaded = True
        else:
            self._img.left = self._curr_x
            self._img.top = self._curr_y
            if not self._displayed:
                self._canv.add(self._img)
                self._displayed = True
            else:
                self._canv.requestRenderAll()

    def displayOutline(self, color):
        self._outline.set({
            'left': self._curr_x - OUTLINE_WIDTH - 1,
            'top': self._curr_y - OUTLINE_WIDTH - 1,
            'fill': 'transparent',
            'stroke': color,
        })
        if DEBUG:
            print('called cardimg.set')
        if not self._outline_displayed:
            self._canv.add(self._outline)
            self._outline_displayed = True
        else:
            # Updates the screen when the outline was already displayed
            # and we just set the color above.
            self._canv.requestRenderAll()

    def erase(self):
        '''remove the drawing of the card on the canvas'''
        self._canv.remove(self._img)
        self._displayed = False
        self.eraseOutline()

    def eraseOutline(self):
        self._canv.remove(self._outline)
        self._outline_displayed = False

    def __contains__(self, x_y_loc):
        x, y = x_y_loc
        return self._curr_x < x < self._curr_x + CARD_WIDTH and \
            self._curr_y < y < self._curr_y + CARD_HEIGHT

    def move(self, destx, desty):
        self._curr_x = destx
        self._curr_y = desty
        self._img.animate({'left': destx, 'top': desty},
                          {'duration': 100,
                              'onChange': self._canv.renderAll.bind(self._canv)}
                          )
        self.eraseOutline()

    def bounceBack(self, *args):
        self._img.animate('top', "+=5",
                          {
                              'duration': 100,
                              'onChange': self._canv.renderAll.bind(self._canv),
                          })

    def bounce(self):
        self._img.animate('top', "-=5",
                          {
                              'duration': 100,
                              'onChange': self._canv.renderAll.bind(self._canv),
                              'onComplete': self.bounceBack,
                          })


class BoardGui:
    '''Handle layout of cards on the board.'''

    def __init__(self, board, canv, card2ImgDict):
        self._board = board
        self._canv = canv
        self._card2ImgDict = card2ImgDict

    def clear(self):
        '''remove all cards from the canvas'''
        for ridx in range(4):
            for cidx in range(13):
                card = self._board.getCardAt(ridx, cidx)
                if card is None:
                    continue
                cardimg = self._card2ImgDict[id(card)]
                cardimg.erase()

    def displayLayout(self):
        '''Go through the cards on the board object and lay them
        out on the canvas.  Translation of the Card object to its
        corresponding CardImg object is done through the given
        card2ImgDict dictionary.
        '''

        # return the closure so it can be called with no parameters
        # from set_timeout() below.
        def displayCard(cardimg, x, y):
            def inner():
                cardimg.drawOnCanvas(x, y)
            return inner

        delay_time = 100
        for ridx in range(4):
            for cidx in range(13):
                card = self._board.getCardAt(ridx, cidx)
                if card is None:
                    continue

                cardimg = self._card2ImgDict[id(card)]
                x = CARD_PADDING + cidx * CARD_AREA_WIDTH
                y = CARD_PADDING + ridx * CARD_AREA_HEIGHT
                timer.set_timeout(displayCard(cardimg, x, y), delay_time)
                delay_time += 20

    def moveCard(self, card, toRow, toCol):
        '''Move a cardimg from where it is not to the given
        row and col on this BoardGui.'''
        cardimg = self._card2ImgDict[id(card)]
        # cardimg.erase()
        # self.drawCard(card, toRow, toCol)
        destx = CARD_PADDING + toCol * CARD_AREA_WIDTH
        desty = CARD_PADDING + toRow * CARD_AREA_HEIGHT
        cardimg.move(destx, desty)

    def drawCard(self, card, row, col):
        cardimg = self._card2ImgDict[id(card)]
        destx = CARD_PADDING + col * CARD_AREA_WIDTH
        desty = CARD_PADDING + row * CARD_AREA_HEIGHT
        cardimg.drawOnCanvas(destx, desty)


# ----------------------------- main -------------------------------
class App:
    '''The main card game application.  This GUI creates a Deck and Board
    model objects and uses them to keep track of legal moves, where the
    cards are on the board, etc., and then displays card images for the
    cards on a created BoardGui (the GUI view).
    '''

    def __init__(self, document, canv):
        '''Store the main window, create the Board and Deck models;
        create all the buttons and labels to allow the user to manipulate the game.
        '''

        self._doc = document
        self._canv = canv    # fabric Canvas object

        self._canv.on("mouse:up", self.onCardClick)

        self.loadCardMoveSound()
        self.loadCardInPlaceSound()
        self.loadEndOfRoundSound()
        self.loadFanfareSound()
        self._playSounds = True

        self._board = Board()
        self._deck = Deck()
        self._deck.addAllCards()
        # We'll fill this in when we remove the aces from the board.
        self._removedAces = []

        # keeps track of cards that can be moved: each item is a tuple:
        # (card, row, col)
        self._moveableCards = []

        # A mapping from card object to CardImg object.  We do it this way
        # so that the card object (in the model) remains agnostic of the view
        # being used on it.
        self._card2ImgDict = {}

        self._score = 0
        # a list of templates of high scores we can update when high scores
        # change, so the screen changes immediately
        self._score_val = []
        self._storage = local_storage.storage
        self.loadSettingsFromStorage()

        # count of cards correctly placed, per round. 1st round is in
        # index 0, and initialized to 0 cards placed.
        self._cardsPlacedPerRound = [0]

        self._roundNum = 1

        # 2 rows of info about the game.
        self._game_info_elem = html.DIV(Class="game-info")
        self._doc <= self._game_info_elem
        self._game_info2_elem = html.DIV(Class="game-info")
        self._doc <= self._game_info2_elem

        self._next_round_btn = html.BUTTON(
            "Next Round", Class="button", disabled=True)
        self._next_round_btn.bind('click', self.nextRound)
        self._game_info_elem <= self._next_round_btn

        self._round_info_elem = \
            html.SPAN("Round: {roundNum}",
                      Class="info-text", id="round_num")
        self._game_info_elem <= self._round_info_elem
        self._round_num_val = template.Template(self._round_info_elem)
        self.updateRoundNum()

        self._cardsInPlace = self._board.countCardsInPlace()
        self._cards_in_place_elem = html.SPAN(
            "Cards in place: {cardsInPlace}", Class="info-text")
        self._game_info_elem <= self._cards_in_place_elem
        self._cardsInPlace_val = template.Template(self._cards_in_place_elem)
        self.updateCardsInPlace()

        self._score_info_elem = html.SPAN(
            "Score: {score}", Class="info-text")
        self._game_info_elem <= self._score_info_elem
        self._scoreInfo_val = template.Template(self._score_info_elem)

        self._pts_per_card_info_elem = html.SPAN(
            "Pts per card: {ptsPerCard}", Class="info-text")
        self._game_info_elem <= self._pts_per_card_info_elem
        self._ptsPerCardInfo_val = template.Template(
            self._pts_per_card_info_elem)
        self.updateScore()

        self._new_game_btn = html.BUTTON(
            "New Game", Class="button", disabled=True)
        self._new_game_btn.bind('click', self.newGameClickHandler)
        self._game_info_elem <= self._new_game_btn

        self._messageDiv = self.createMessageDiv()

        self._status_elem = html.SPAN("{status}")
        self._game_info2_elem <= self._status_elem
        self._status_val = template.Template(self._status_elem)
        self.setStatus("Cards placed this round: 0")

        self._playSoundsSpan = html.SPAN()
        self._game_info2_elem <= self._playSoundsSpan
        self._playSoundsLabel = html.LABEL("Play sounds: ")
        self._playSoundsSpan <= self._playSoundsLabel
        self._playSoundsCheckBox = html.INPUT(
            type="checkbox", checked=self._playSounds)
        self._playSoundsCheckBox.bind('click', self.togglePlaySounds)
        self._playSoundsSpan <= self._playSoundsCheckBox

        # A mapping from Card object to CardImg object.  This is needed so
        # that we map a card in the board layout to the CardImg, which should
        # then be placed at a certain location.  (We don't keep a reference to
        # the CardImg in Card because it just shouldn't know how it is displayed.)
        cards = self._deck.getCards()
        for card in cards:
            cardimg = CardImg(card, self._canv)
            self._card2ImgDict[id(card)] = cardimg

        self._boardGui = BoardGui(self._board, self._canv, self._card2ImgDict)

        self.loadHighScores()

        self.initNewGame()

    def initNewGame(self):

        self._board.layoutCards(self._deck)
        self._boardGui.displayLayout()
        self._cardsInPlace = self._board.countCardsInPlace()
        self._cardsPlacedPerRound = [self._cardsInPlace]

        self.updateCardsInPlace()
        self.updateScore()

        # Disable the "next round" button.
        self.disableNextRoundBtn()
        timer.set_timeout(self.removeAces, 1500)

    def removeAces(self):
        '''Go through the board and remove the aces from the board.
        Then hide the corresponding CardImgs in the BoardGui for the
        aces.
        '''
        self._removedAces = self._board.removeAces()
        for card in self._removedAces:
            self._card2ImgDict[id(card)].erase()

        self.enableNewGameButton()

        if self.isEndOfRoundOrGame():
            return

        self._moveableCards = self._board.findPlayableCards()
        self.highlightMovableCards()
        self.markGoodCards()

    def isEndOfRoundOrGame(self):
        '''Check if the game is over or the round is over.  Return True
        if it is.
        '''
        if self._board.gameCompletelyDone():
            score = self.currentScore()
            self.displayMessageOverCanvas(
                f"Congratulations!\n\nYou finished the game in {self._roundNum} rounds\n" +
                f"with a score of {score}.\n" +
                "Click 'New Game' to try again.", 5000)
            self.addScoreToHighScoresTable(score)
            self.setStatus("Cards placed this round: " +
                           str(self._cardsPlacedPerRound[self._roundNum - 1]))
            self.playFanfareSound()
            return True

        if not self._board.moreMoves():
            self.setStatus("No more moves")
            # enable the next round button by deleting the disabled attribute
            self.playEndOfRoundSound()
            self.enableNextRoundBtn()
        return False

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
        if DEBUG:
            print('Got click!')

        # print("number of objects = ", len(self._canv.getObjects()))

        ptr = self._canv.getPointer(event)
        x = ptr.x
        y = ptr.y
        card = self.getClickedCard(x, y)
        if card is None:
            return

        if DEBUG:
            print('got card')
        if self.cardIsMoveable(card):

            fromRow, fromCol = self._board.findCardLocation(card)
            if DEBUG:
                print('got card location')

            res = self._board.getMoveableCardDest(card)
            if res is None:
                print("Cannot move that card.")
                return
            toRow, toCol = res   # split into the 2 parts.
            if DEBUG:
                print('got card dest')

            self.eraseMovableCardHighlights()
            cardsInPlaceBeforeMove = self._cardsInPlace
            self._board.moveCard(card, fromRow, fromCol, toRow, toCol)
            self._boardGui.moveCard(card, toRow, toCol)
            self._cardsInPlace = self._board.countCardsInPlace()
            if DEBUG:
                print('moved card')
            newCardsInPlace = self._cardsInPlace - cardsInPlaceBeforeMove
            if newCardsInPlace > 0:
                self.playCardInPlaceSound()
                if DEBUG:
                    print('played card in place sound')
                self._cardsPlacedPerRound[self._roundNum-1] += newCardsInPlace
                if DEBUG:
                    print('calced cardsPlacedPerRound')
                self.updateCardsInPlace()
                if DEBUG:
                    print('updates Cards in palce')
                self.updateScore()
                if DEBUG:
                    print('scores udpated')
                self.markGoodCards()
                if DEBUG:
                    print('marked good cards')
                self.setStatus("Cards placed this round: " +
                               str(self._cardsPlacedPerRound[self._roundNum - 1]))
            else:
                # just a normal move
                self.playCardMoveSound()

            if DEBUG:
                print('checking if end of round or game')
            if self.isEndOfRoundOrGame():
                return

            if DEBUG:
                print('updating movable cards')
            self._moveableCards = self._board.findPlayableCards()
            if DEBUG:
                print('updated movable cards')
            self.highlightMovableCards()
            if DEBUG:
                print('highlighted movable cards')

        else:
            # user clicked another card: so highlight the card it would
            # have to go to the right of.
            # E.g., you click 7D, highlight 6D
            (card, row, col) = self._board.findLowerCard(card)
            if card is not None:
                self.flashLowerCard(card, row, col)

    def newGameClickHandler(self, ev):
        '''Call back when New Game button is pressed.
        '''

        self.disableNewGameButton()

        self._boardGui.clear()

        self._roundNum = 1
        self.updateRoundNum()
        self._cardsPlacedPerRound = [0]

        # Add all the cards on the board to the deck.
        self._deck.addCards(self._board.getAllCards())
        if self._deck.numCards() == 48:
            # The board had aces removed, so add the aces back to the deck.
            for card in self._removedAces:
                self._deck.addCard(card)
        self._deck.shuffle()
        self._board.reinit()

        self.initNewGame()

    def nextRound(self, ev):
        '''Callback for when the user clicks the "Next Round" button.
        Increment the round number counter;
        Remove the cards from the board that are not in the correct place;
        Add those cards, and the aces, back to the deck; shuffle it;
        Update the display to show the good cards only, for 1 second;
        Register nextRoundContined() to be called.
        '''

        self.disableNewGameButton()

        # No cards placed yet in this round
        self._cardsPlacedPerRound.append(0)
        self._roundNum += 1
        self.updateRoundNum()
        discarded = self._board.removeIncorrectCards()
        self._deck.addCards(discarded)
        # Add the aces back to the deck.
        for card in self._removedAces:
            self._deck.addCard(card)
        self._deck.shuffle()

        # display the board with only "good cards" for 1 second.
        for card in discarded:
            cardimg = self._card2ImgDict[id(card)]
            cardimg.erase()
        self.updateScore()

        self.setStatus("Cards placed this round: " +
                       str(self._cardsPlacedPerRound[self._roundNum - 1]))

        timer.set_timeout(self.nextRoundContinued, 1000)

    def nextRoundContinued(self):
        '''Continuation of nextRound():
        Lay out all the cards from the deck on the board;
        Update the button states;
        Wait a bit, then call removeAces().
        '''

        # Deck is shuffled.  Now, add cards to the board.
        self._board.layoutCards(self._deck)
        self._boardGui.displayLayout()

        self.disableNextRoundBtn()
        # After 1.5 seconds of showing all cards, remove the aces.
        timer.set_timeout(self.removeAces, 1500)

    def getClickedCard(self, x, y):
        cards = self._board.getAllCards()
        for card in cards:
            cardImg = self._card2ImgDict[id(card)]
            if (x, y) in cardImg:
                return card
        return None

    def cardIsMoveable(self, card):
        for mcard, row, col in self._moveableCards:
            if mcard == card:
                return True
        return False

    def eraseMovableCardHighlights(self):
        for card, row, col in self._moveableCards:
            self.eraseOutline(card)

    def highlightMovableCards(self):
        '''Get the cards that have a space after them, find the cards
        that could go in those spaces, and draw a rectangle around those
        cards.
        '''
        for card, row, col in self._moveableCards:
            self.drawOutline(card, MOVABLE_CARD_COLOR)

    def markGoodCards(self):
        '''Redraw all the outlines around good cards.'''
        goodCards = self._board.getCardsInPlace()
        if DEBUG:
            print('got cards in place')
        for card, r, c in goodCards:
            self.drawOutline(card, CARDS_IN_PLACE_COLOR)

    def flashLowerCard(self, card, row, col):
        cardimg = self._card2ImgDict[id(card)]
        cardimg.bounce()

    # def unflashLowerCard(self):
    #     self.eraseOutline(self._flashingCard)
    #     # the card that was flashed may have been one of these others
    #     # so we have to redraw everything.
    #     self.highlightMovableCards()
    #     self.markGoodCards()

    def drawOutline(self, card, color):
        cardimg = self._card2ImgDict[id(card)]
        cardimg.displayOutline(color)

    def eraseOutline(self, card):
        cardimg = self._card2ImgDict[id(card)]
        cardimg.eraseOutline()

    def enableNextRoundBtn(self):
        del self._next_round_btn.attrs['disabled']

    def disableNextRoundBtn(self):
        self._next_round_btn.attrs['disabled'] = True

    def getPtsPerCard(self):
        '''10 pts for round 1, 9 for round 2, etc...'''
        return 11 - self._roundNum

    def currentScore(self):
        '''Compute the total score each time by summing the number of
        cards placed correctly in a round * the value of a card per round.'''
        res = 0
        for rnd in range(len(self._cardsPlacedPerRound)):
            res += (10 - rnd) * self._cardsPlacedPerRound[rnd]
        return res

    def updateScore(self):
        self._scoreInfo_val.render(score=self.currentScore())
        self._ptsPerCardInfo_val.render(ptsPerCard=self.getPtsPerCard())

    def updateCardsInPlace(self):
        self._cardsInPlace_val.render(cardsInPlace=self._cardsInPlace)

    def updateRoundNum(self):
        self._round_num_val.render(roundNum=self._roundNum)

    def setStatus(self, status):
        self._status_val.render(status=status)

    def enableNewGameButton(self):
        del self._new_game_btn.attrs['disabled']

    def disableNewGameButton(self):
        self._new_game_btn.attrs['disabled'] = True

    def createMessageDiv(self):
        elem = html.DIV(Class="message-box")
        elem.style.top = f"{CANVAS_HEIGHT / 3}px"
        elem.style.left = f"{CANVAS_WIDTH / 3}px"
        elem.style.width = f"{CANVAS_WIDTH / 3}px"
        # elem.style.height = f"{CANVAS_HEIGHT / 3}px"
        return elem

    def displayMessageOverCanvas(self, msg, ms):
        '''Split msg on newlines and put each result into its own div,
        which is then centered in the containing div, and displayed
        on over the canvas.  Undisplay it after *ms* milliseconds.
        '''
        self._messageDiv.style.display = "block"
        lines = msg.split('\n')
        htmls = [html.DIV(line, Class="center") for line in lines]
        print('htmls len', len(htmls))
        for h in htmls:
            self._messageDiv <= h
        self._doc <= self._messageDiv
        timer.set_timeout(self.eraseMessageBox, ms)

    def eraseMessageBox(self):
        self._messageDiv.style.display = "none"
        self._messageDiv.clear()

    def loadCardMoveSound(self):
        self._moveCardSound = self.loadSound("snap3.wav")

    def loadCardInPlaceSound(self):
        self._cardInPlaceSound = self.loadSound("inplace.wav")

    def loadEndOfRoundSound(self):
        self._endOfRoundSound = self.loadSound("lose.wav")

    def loadFanfareSound(self):
        self._fanfareSound = self.loadSound("fanfare.wav")

    def loadSound(self, file):
        sound = document.createElement("audio")
        sound.src = file
        sound.setAttribute("preload", "auto")
        sound.setAttribute("controls", "none")
        sound.style.display = "none"
        self._doc <= sound
        return sound

    def playCardMoveSound(self):
        if self._playSounds:
            self._moveCardSound.play()

    def playCardInPlaceSound(self):
        if self._playSounds:
            self._cardInPlaceSound.play()

    def playEndOfRoundSound(self):
        if self._playSounds:
            self._endOfRoundSound.play()

    def playFanfareSound(self):
        if self._playSounds:
            self._fanfareSound.play()

    def togglePlaySounds(self, ev):
        self._playSounds = ev.target.checked
        self.storePlaySoundsSetting()

    def loadHighScores(self):
        # storing up to 5 high scores.
        self._score = [0] * 5
        try:   # there may be less than 5 values stored so far.
            for i in range(5):
                self._score[i] = int(self._storage[f'highScore{i}'])
        except:
            pass
        self._scores_span = html.SPAN()
        self._game_info2_elem <= self._scores_span

        header = html.SPAN('High Scores: ')
        self._scores_span <= header

        for i in range(5):
            span = html.SPAN("{score}")
            self._score_val.append(template.Template(span))
            self._scores_span <= span
            self._score_val[i].render(score=self._score[i])

    def addScoreToHighScoresTable(self, score):
        changed = False
        for i in range(5):
            if score >= self._score[i]:
                self._score.insert(i, score)
                changed = True
                break
        if changed:
            for i in range(5):
                self._storage[f'highScore{i}'] = str(self._score[i])
                # update the screen
                self._score_val[i].render(score=self._score[i])

    def loadSettingsFromStorage(self):
        try:
            self._playSounds = self._storage['playSounds'] == "True"
        except:
            print("no playsounds in storage")
            # If we haven't stored a choice, the default is True
            self._playSounds = True

    def storePlaySoundsSetting(self):
        self._storage['playSounds'] = str(self._playSounds)


# Use brython to create the canvas.
real_canvas = html.CANVAS(width=CANVAS_WIDTH, height=CANVAS_HEIGHT, id='c')
document <= real_canvas


def windowChange(ev):
    print(window.innerWidth, window.innerHeight)


window.bind('resize', windowChange)


# Use the canvas in fabric
canvas = fabric.Canvas.new('c', {
    'width': CANVAS_WIDTH,
    'height': CANVAS_HEIGHT,
    'selectable': False,
    'backgroundColor': 'darkgreen'
})
app = App(document, canvas)

document <= html.H2(
    html.A("Instructions", href="instructions.html", Class="right-edge"))
