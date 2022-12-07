import lz4.frame as lz4
import random
import string
import matplotlib.pyplot as plt
import statistics
import math

def get_filler_str(data_len : int):
    return ''.join(
            random.choices(
                string.printable.replace(string.ascii_lowercase, ''),
                k=data_len))


regex = "char by char"
print(regex)
trials = 100
points = [[] for _ in range(10, 30)]
for trial in range(trials):
    middle = get_filler_str(30)
    suffix = get_filler_str(1600)
    prefix = ''.join(random.choices(string.ascii_lowercase, k=30))
    for prefix_len in range(10, 30):
        next_char = random.choice(string.ascii_lowercase)
        correct_str = prefix[:prefix_len] + next_char + middle + prefix + next_char + suffix
        correct_len = len(lz4.compress(correct_str.encode("ascii")))

        incorrect_lens = []
        for c in string.ascii_lowercase:
            if c == next_char:
                continue
            incorrect_str = prefix[:prefix_len] + next_char + middle + prefix + c + suffix
            incorrect_lens.append(len(lz4.compress(incorrect_str.encode("ascii"))))
        points[prefix_len - 10].append(correct_len - statistics.mean(incorrect_lens))


fig, ax = plt.subplots()
for trial in range(trials):
    x = [i for i in range(10, 30)]
    y = [points[i][trial] for i in range(20)]
    ax.plot(x, y)

ax.set(ylabel="compressed size at n - compressed size at n=0", xlabel = "n", title=regex)
ax.set_ylim([0, 5])
ax.set_xlim([0, 30])
ax.grid()

fig.savefig("lz4_plots/cbc.png")

