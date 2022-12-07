from pymongo import MongoClient
import time
import os
import subprocess
import random
from datetime import datetime
import string
import sys
import numpy as np

filler_1 = ''.join(random.choices(string.ascii_uppercase, k=15))
filler_2 = ''.join(random.choices(string.ascii_uppercase, k=15))
filler_3 = ''.join(random.choices(string.ascii_uppercase, k=15))

def get_table_size():
     return int(subprocess.check_output(["ls", "-s", "--block-size=1", table_path]).split()[0])

def flush_and_wait_for_change():
     global old_edit_time
     client.admin.command("fsync", lock=True)
     max_sleeps = 10
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
     while size <= get_table_size():
          compressor_size += 1
          db.test.update_one({'id' : 2}, [{'$set' : {'value' : compressible[:compressor_size] + non_compressible[compressor_size:]}}])
          if non_compressible[compressor_size - 1] != '*':
               flush_and_wait_for_change()

client = MongoClient("localhost")
db=client.test

possibilities = []
if sys.argv[1] == "--random":
    for _ in range(2000):
        size = np.random.randint(10, 20)
        secret = "".join(random.choices(string.ascii_lowercase, k=size))
        possibilities.append(secret)
if sys.argv[1] == "--english":
    with open("../res/10000-english-long.txt") as f:
        for line in f:
            word = line.strip().lower()
            possibilities.append(word)
if sys.argv[1] == "--emails":
    with open("../res/fake-emails.txt") as f:
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

for num_secrets in secrets_to_try:
    random.shuffle(possibilities)
    for trial in range(0, 200, num_secrets):
        success = False
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

        for secret_idx in range(num_secrets, num_secrets*2):
            wrong_guess = possibilities[(trial + secret_idx) % len(possibilities)]
            guesses.append(wrong_guess)

        fillerCharSet = string.printable.replace(string.ascii_lowercase, '').replace('*', '')
        if sys.argv[1] == "--emails":
            fillerCharSet = fillerCharSet.replace('_', '').replace('.', '').replace('@', '')

        guess_lens = set([len(guess) for guess in guesses])
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
        for name in guesses:
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
        for guess, score_tuple in refScores:
            label = 1 if guess in correct_guesses else 0
            print(str(label)+","+str(num_secrets)+","+str(score_tuple[0])+","+str(score_tuple[1])+","+str(score_tuple[2]) +","+str(setupEnd - setupStart)+","+str((end-setupEnd)/num_secrets) +","+str(s_yes_max))
