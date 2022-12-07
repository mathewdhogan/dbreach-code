import utils.mariadb_utils as utils
import random

'''
Parent class for all DBREACHers
'''
class DBREACHer():
    def __init__(self, controller : utils.MariaDBController, tablename : str, startIdx : int, maxRowSize: int, fillerCharSet : set, compressCharAscii : int):
        self.control = controller
        self.table = tablename
        self.startIdx = startIdx
        numFillerRows = 200
        self.fillers = [''.join(random.choices(fillerCharSet, k=maxRowSize)) for _ in range(numFillerRows)]
        self.compressChar = chr(compressCharAscii)
        self.numFillerRows = 200
        self.fillerCharSet = fillerCharSet
        self.maxRowSize = maxRowSize

    # child classes must override this method
    # return True if successful
    def insertFillers(self) -> bool:
        return False

    # child classes must override this method
    # return True if table shrunk from inserting guess
    def insertGuessAndCheckIfShrunk(self, guess : str) -> bool:
        return False

    # child classes must override this method
    # return True if table shrunk from adding one compressible byte
    def addCompressibleByteAndCheckIfShrunk(self) -> bool:
        return False

    # child classes must override this method
    # return compressibility score of current guess, or None if it cannot yet be calculated
    def getCompressibilityScoreOfCurrentGuess(self) -> float:
        return None

