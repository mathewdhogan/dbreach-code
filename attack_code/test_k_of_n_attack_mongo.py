from pymongo import MongoClient
import time
import os
import subprocess
import random
from datetime import datetime
import string
import sys

filler_1 = ''.join(random.choices(string.ascii_uppercase, k=15))
filler_2 = ''.join(random.choices(string.ascii_uppercase, k=15))
filler_3 = ''.join(random.choices(string.ascii_uppercase, k=15))

def get_table_size():
     return int(subprocess.check_output(["ls", "-s", "--block-size=1", table_path]).split()[0])

def flush_and_wait_for_change():
     global old_edit_time
     client.admin.command("fsync", lock=True)
     max_sleeps = 30
     sleeps = 0
     while os.path.getmtime(table_path) == old_edit_time:
          sleeps += 1
          if sleeps > max_sleeps:
               break
          time.sleep(0.1)
     client.admin.command("fsyncUnlock")
     old_edit_time = os.path.getmtime(table_path)

def reshrink_table(compressor_size, filler_1_reset=False):
     size = get_table_size()
     # overwrite both on-disk copies of the guess string (the active and inactive one) to avoid
     # cross-guess interference
     db.test.update_one({'id' : 1}, [{'$set' : {'value' : filler_2}}])
     flush_and_wait_for_change()
     db.test.update_one({'id' : 1}, [{'$set' : {'value' : filler_3}}])
     flush_and_wait_for_change()
     if filler_1_reset:
          db.test.update_one({'id' : 3}, [{'$set' : {'value' : filler_1}}])
          flush_and_wait_for_change()
     updates = 0
     while size <= get_table_size() or updates < 2:
          updates += 1
          compressor_size += 1
          if compressor_size < 0 or compressor_size >= len(non_compressible):
               break
          db.test.update_one({'id' : 2}, [{'$set' : {'value' : compressible[:compressor_size] + non_compressible[compressor_size:]}}])
          if non_compressible[compressor_size - 1] != '*':
               flush_and_wait_for_change()


client = MongoClient("localhost")
db=client.test

possibilities = []
if sys.argv[1] == "--random":
    for _ in range(2000):
        size = random.randint(10, 20)
        secret = "".join(random.choices(string.ascii_lowercase, k=size))
        possibilities.append(secret)
if sys.argv[1] == "--english":
    with open("../resources/10000-english-long.txt") as f:
        for line in f:
            word = line.strip().lower()
            possibilities.append(word)
if sys.argv[1] == "--emails":
    with open("../resources/fake-emails.txt") as f:
        for line in f:
            email = line.strip().lower()
            possibilities.append(email)

if sys.argv[2] == "--snappy":
    compressor_str = "block_compressor=snappy"
if sys.argv[2] == "--zlib":
    compressor_str = "block_compressor=zlib"

secrets_to_try = [1]
if sys.argv[3] == "--num_secrets":
    secrets_to_try = [int(a) for a in sys.argv[4:]]

print("records_on_page,k,accuracy_n_500,accuracy_n_750,accuracy_n_1000,accuracy_n_1250,accuracy_n_1500,setup_time,per_guess_time")

max_consecutive_exceptions = 10

consecutive_exceptions = 0
while len(secrets_to_try) > 0:
    num_secrets = secrets_to_try[-1]
    secrets_to_try = secrets_to_try[:-1]
    try:
        random.shuffle(possibilities)
        for trial in range(1):
            db.test.drop()
            db.create_collection( "test", storageEngine={'wiredTiger': { 'configString': compressor_str }})
            old_edit_time = 0
            table_path = "/var/lib/mongodb/" + db.command("collstats", "test")['wiredTiger']['uri'][17:] + ".wt"
        
            guesses = []
            correct_guesses = set()

            for secret_idx in range(num_secrets):
                secret_value = possibilities[(trial + secret_idx) % len(possibilities)]
                secret = {'id' : 0, 'value' : secret_value}
                db.test.insert_one(secret)
                flush_and_wait_for_change()
                guesses.append(secret_value)
                correct_guesses.add(secret_value)

            for secret_idx in range(num_secrets, 1500):
                wrong_guess = possibilities[(trial + secret_idx) % len(possibilities)]
                guesses.append(wrong_guess)

            _500_guesses = set(guesses[:500])
            _750_guesses = set(guesses[:750])
            _1000_guesses = set(guesses[:1000])
            _1250_guesses = set(guesses[:1250])
            _1500_guesses = set(guesses[:1500])

            fillerCharSet = string.printable.replace(string.ascii_lowercase, '').replace('*', '')
            if sys.argv[1] == "--emails":
                fillerCharSet = fillerCharSet.replace('_', '').replace('.', '').replace('@', '')


            guess_lens = set([len(guess) for guess in _1500_guesses])
            fillers_len = max(guess_lens)

            filler_1 = ''.join(random.choices(fillerCharSet, k=fillers_len))
            filler_2 = ''.join(random.choices(fillerCharSet, k=fillers_len))
            filler_3 = ''.join(random.choices(fillerCharSet, k=fillers_len))

            compressible = ''.join(['*' for _ in range(5000)])
            non_compressible = ''.join(random.choices(fillerCharSet, k=5000))

            setupStart = time.time()

            s_no_str = ''.join(random.choices(fillerCharSet, k=fillers_len))
            guess = {'id' : 1, 'value' : s_no_str}
            db.test.insert_one(guess)
            flush_and_wait_for_change()
            filler_row_1 = {'id' : 3, 'value' : filler_1}
            db.test.insert_one(filler_row_1)
            compressor = {'id' : 2, 'value' : compressible}
            db.test.insert_one(compressor)
            flush_and_wait_for_change()
            size = get_table_size()
            non_compress_bytes = 0
            compressor_size = len(compressible) - 0
            while size >= get_table_size():
                non_compress_bytes += 1
                compressor_size -= 1
                db.test.update_one({'id' : 2}, [{'$set' : {'value' : compressible[:compressor_size] + non_compressible[compressor_size:]}}])
                if non_compressible[compressor_size] != '*':
                        flush_and_wait_for_change()

            s_no = non_compress_bytes

            reshrink_table(compressor_size)

            s_yeses = dict()
            s_yes_max = 0

            for glen in guess_lens:
                # calculate s_yes:
                s_yes_str = ''.join(random.choices(fillerCharSet, k=glen))
                # insert s_yes as guess:
                db.test.update_one({'id': 1}, [{'$set' : {'value' : s_yes_str}}])
                flush_and_wait_for_change()

                # add copy of s_yes_str to simulate correct guess:
                db.test.update_one({'id' : 3}, [{'$set' : {'value' : s_yes_str}}])
                flush_and_wait_for_change()

                # calc compressibility score s_yes_glen
                db.test.update_one({'id' : 2}, [{'$set' : {'value' : compressible}}])
                flush_and_wait_for_change()
                size = get_table_size()
                non_compress_bytes = s_no
                compressor_size = len(compressible) - s_no
                while size >= get_table_size():
                    non_compress_bytes += 1
                    compressor_size -= 1
                    db.test.update_one({'id' : 2}, [{'$set' : {'value' : compressible[:compressor_size] + non_compressible[compressor_size:]}}])
                    if non_compressible[compressor_size] != '*':
                            flush_and_wait_for_change()

                s_yeses[glen] = non_compress_bytes
                if non_compress_bytes > s_yes_max:
                    s_yes_max = non_compress_bytes

                reshrink_table(compressor_size, filler_1_reset=True)

            setupEnd = time.time()

            scores = []
            for name in _1500_guesses:
                db.test.update_one({'id':1}, [{'$set' : {'value' : name}}])
                flush_and_wait_for_change()
                db.test.update_one({'id':2}, [{'$set' : {'value' : compressible}}])
                flush_and_wait_for_change()
                size = get_table_size()
                non_compress_bytes = s_no - 5
                compressor_size = len(compressible) - (s_no - 5)
                while size >= get_table_size():
                     non_compress_bytes += 1
                     compressor_size -= 1
                     db.test.update_one({'id' : 2}, [{'$set' : {'value' : compressible[:compressor_size] + non_compressible[compressor_size:]}}])
                     if non_compressible[compressor_size] != '*':
                             flush_and_wait_for_change()
                scores.append((non_compress_bytes, name))
                reshrink_table(compressor_size)

            end = time.time()

            refScores = [(g, (s_no, s, s_yeses[len(g)])) for s, g in scores]
            pcts = [(1 - (b_yes - b) / max(b_yes - b_no, 1), g) for g, (b_no, b, b_yes) in refScores]
            pcts.sort(reverse=True)

            choices_500 = [(pct, g) for pct, g in pcts if g in _500_guesses]
            choices_750 = [(pct, g) for pct, g in pcts if g in _750_guesses]
            choices_1000 = [(pct, g) for pct, g in pcts if g in _1000_guesses]
            choices_1250 = [(pct, g) for pct, g in pcts if g in _1250_guesses]
            choices_1500 = pcts

            accuracy_500 = sum([1 for pct, g in choices_500[:num_secrets] if g in correct_guesses]) / num_secrets
            accuracy_750 = sum([1 for pct, g in choices_750[:num_secrets] if g in correct_guesses]) / num_secrets
            accuracy_1000 = sum([1 for pct, g in choices_1000[:num_secrets] if g in correct_guesses]) / num_secrets
            accuracy_1250 = sum([1 for pct, g in choices_1250[:num_secrets] if g in correct_guesses]) / num_secrets
            accuracy_1500 = sum([1 for pct, g in choices_1500[:num_secrets] if g in correct_guesses]) / num_secrets

            print(str(num_secrets)+","+str(num_secrets)+","+str(accuracy_500)+","+str(accuracy_750)+","+str(accuracy_1000)+","+str(accuracy_1250)+","+str(accuracy_1500)+","+str(setupEnd - setupStart) + "," + str((end - setupEnd) / 1500))
        consecutive_exceptions = 0
    except:
        consecutive_exceptions += 1
        if consecutive_exceptions == max_consecutive_exceptions:
            raise Exception("Reached maximum number of consecutive exceptions, failing")
        secrets_to_try += [num_secrets]
