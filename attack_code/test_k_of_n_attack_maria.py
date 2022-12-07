import utils.mariadb_utils as utils
import dbreacher
import dbreacher_impl
import decision_attacker
import random
import string
import time
import sys

maxRowSize = 200

control = utils.MariaDBController("testdb")

table = "victimtable"
control.drop_table(table)
control.create_basic_table(table,
            varchar_len=maxRowSize,
        compressed=True,
        encrypted=True)

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

secrets_to_try = [1]
if sys.argv[2] == "--num_secrets":
    secrets_to_try = [int(a) for a in sys.argv[3:]]

print("records_on_page,k,accuracy_n_500,accuracy_n_750,accuracy_n_1000,accuracy_n_1250,accuracy_n_1500,setup_time,per_guess_time")

for num_secrets in secrets_to_try:
    random.shuffle(possibilities)
    for trial in range(1):
        success = False
        control.drop_table(table)
        control.create_basic_table(table,
            varchar_len=maxRowSize,
            compressed=True,
            encrypted=True)
        guesses = []
        correct_guesses = set()
        for secret_idx in range(num_secrets):
            secret = possibilities[(trial + secret_idx) % len(possibilities)]
            control.insert_row(table, secret_idx, secret)
            guesses.append(secret)
            correct_guesses.add(secret)
        
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
        dbreacher = dbreacher_impl.DBREACHerImpl(control, table, num_secrets, maxRowSize, fillerCharSet, ord('*'))

        attacker = decision_attacker.decisionAttacker(dbreacher, guesses)
        while not success:
            setupStart = time.time()
            success = attacker.setUp()
            setupEnd = time.time()
            if success:
                success = attacker.tryAllGuesses()
            end = time.time()
        refScores = attacker.getGuessAndReferenceScores()
        pcts = [(1 - (b - b_yes) / max(b_no, 1), g) for g, (b_no, b, b_yes) in refScores]
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
       
