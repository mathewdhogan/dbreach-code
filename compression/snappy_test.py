import snappy
import random
import string
import matplotlib.pyplot as plt
import math

def get_filler_str(data_len : int):
    return ''.join(
            random.choices(
                string.ascii_uppercase,
                k=data_len))

base = "jhebsrmefvaisogwryffeqwbioacednwphqljozpljtlrotqatkrplpwxzyodcvqtcexgywhhtgzdftbudljkgezhfxvfdcfadgsxhcdkgbmuwbmmwgnolypmaeeidmmotmohqccqnfiiwdgkmsxerhtijbzbgxcgfbkghndlwpqlaokhgyuipnvhggkbjvkeahilfglg"

regex = "*^(n)"
print(regex)
trials = 100
points = [[] for _ in range(len(base))]
for trial in range(trials):
    prefix_len = random.randint(0, 16000)
    prefix = get_filler_str(prefix_len)
    suffix = get_filler_str(16000 - prefix_len)
    base_size = len(snappy.compress("")) 
    for n in range(len(base)):
        raw_str = "".join(['*' for _ in range(n)])
        comp_size = len(snappy.compress(raw_str))
        points[n].append(comp_size - base_size)

fig, ax = plt.subplots()
for trial in range(trials):
    x = [i for i in range(len(base))]
    y = [points[i][trial] for i in range(len(base))]
    ax.plot(x, y)

ax.set(ylabel="compressed size at n - compressed size at n=0", xlabel = "n", title=regex)
ax.set_ylim([0, 200])
ax.set_xlim([0, 200])
ax.grid()

fig.savefig("plots/" + regex + ".png")



regex = "prefix + *^(n) + suffix"
print(regex)
trials = 100
points = [[] for _ in range(len(base))]
for trial in range(trials):
    prefix_len = random.randint(0, 16000)
    prefix = get_filler_str(prefix_len)
    suffix = get_filler_str(16000 - prefix_len)
    base_size = len(snappy.compress(prefix + suffix))
    for n in range(len(base)):
        raw_str = prefix + "".join(['*' for _ in range(n)]) + suffix
        comp_size = len(snappy.compress(raw_str))
        points[n].append(comp_size - base_size)

fig, ax = plt.subplots()
for trial in range(trials):
    x = [i for i in range(len(base))]
    y = [points[i][trial] for i in range(len(base))]
    ax.plot(x, y)

ax.set(ylabel="compressed size at n - compressed size at n=0", xlabel = "n", title=regex)
ax.set_ylim([0, 200])
ax.set_xlim([0, 200])
ax.grid()

fig.savefig("plots/" + regex + ".png")



regex = "prefix + *^(100 + n) + suffix"
print(regex)
trials = 100
points = [[] for _ in range(len(base))]
for trial in range(trials):
    prefix_len = random.randint(0, 16000)
    prefix = get_filler_str(prefix_len)
    suffix = get_filler_str(16000 - prefix_len)
    base_size = len(snappy.compress(prefix + "".join(['*' for _ in range(100)]) + suffix))
    for n in range(len(base)):
        raw_str = prefix + "".join(['*' for _ in range(100 + n)]) + suffix
        comp_size = len(snappy.compress(raw_str))
        points[n].append(comp_size - base_size)

fig, ax = plt.subplots()
for trial in range(trials):
    x = [i for i in range(len(base))]
    y = [points[i][trial] for i in range(len(base))]
    ax.plot(x, y)

ax.set(ylabel="compressed size at n - compressed size at n=0", xlabel = "n", title=regex)
ax.set_ylim([0, 200])
ax.set_xlim([0, 200])
ax.grid()

fig.savefig("plots/" + regex + ".png")


regex = "prefix + *^(100 + min(n, 100)) + ~^(max(n, 100)) + suffix"
print(regex)
trials = 100
points = [[] for _ in range(len(base))]
for trial in range(trials):
    prefix_len = random.randint(0, 16000)
    prefix = get_filler_str(prefix_len)
    suffix = get_filler_str(16000 - prefix_len)
    n = 0
    raw_str = prefix + "".join(['*' for _ in range(100 + min(n, 100))]) + "".join(['~' for _ in range(max(n, 100))]) + suffix
    base_size = len(snappy.compress(raw_str))
    for n in range(len(base)):
        raw_str = prefix + "".join(['*' for _ in range(100 + min(n, 100))]) + "".join(['~' for _ in range(max(n, 100))]) + suffix
        comp_size = len(snappy.compress(raw_str))
        points[n].append(comp_size - base_size)

fig, ax = plt.subplots()
for trial in range(trials):
    x = [i for i in range(len(base))]
    y = [points[i][trial] for i in range(len(base))]
    ax.plot(x, y)

ax.set(ylabel="compressed size at n - compressed size at n=0", xlabel = "n", title=regex)
ax.set_ylim([0, 200])
ax.set_xlim([0, 200])
ax.grid()

fig.savefig("plots/" + regex + ".png")


regex = "prefix + *^(150 + min(n, 50)) + #^(150 + max(0, min(n - 50, 50))) + `^(150 + max(0, min(n - 100, 50))) + ~^(max(n, 150)) + suffix"
print(regex)
trials = 100
points = [[] for _ in range(len(base))]
for trial in range(trials):
    prefix_len = random.randint(0, 16000)
    prefix = get_filler_str(prefix_len)
    suffix = get_filler_str(16000 - prefix_len)
    n = 0
    raw_str = prefix + "".join(['*' for _ in range(150 + min(n, 50))]) + "".join(['#' for _ in range(150 + max(0, min(n - 50, 50)))]) + "".join(['#' for _ in range(150 + max(0, min(n - 100, 50)))]) +"".join(['~' for _ in range(max(n, 150))]) + suffix
    base_size = len(snappy.compress(raw_str))
    for n in range(len(base)):
        raw_str = prefix + "".join(['*' for _ in range(150 + min(n, 50))]) + "".join(['#' for _ in range(150 + max(0, min(n - 50, 50)))]) + "".join(['#' for _ in range(150 + max(0, min(n - 100, 50)))]) +"".join(['~' for _ in range(max(n, 150))]) + suffix
        comp_size = len(snappy.compress(raw_str))
        points[n].append(comp_size - base_size)

fig, ax = plt.subplots()
for trial in range(trials):
    x = [i for i in range(len(base))]
    y = [points[i][trial] for i in range(len(base))]
    ax.plot(x, y)

ax.set(ylabel="compressed size at n - compressed size at n=0", xlabel = "n", title=regex)
ax.set_ylim([0, 200])
ax.set_xlim([0, 200])
ax.grid()

fig.savefig("plots/" + regex + ".png")

regex = "prefix + X + X[:n] + suffix"
print(regex)
trials = 100
points = [[] for _ in range(len(base))]
for trial in range(trials):
    prefix_len = random.randint(0, 16000 - len(base))
    prefix = get_filler_str(prefix_len)
    suffix = get_filler_str(16000 - len(base) - prefix_len)
    base_size = len(snappy.compress(prefix + base + suffix))
    for size in range(len(base)):
        raw_str = prefix + base + base[:size] + suffix
        comp_size = len(snappy.compress(raw_str))
        points[size].append(comp_size - base_size)

fig, ax = plt.subplots()
for trial in range(trials):
    x = [i for i in range(len(base))]
    y = [points[i][trial] for i in range(len(base))]
    ax.plot(x, y)

ax.set(ylabel="compressed size at n - compressed size at n=0", xlabel = "n", title=regex)
ax.set_ylim([0, 200])
ax.set_xlim([0, 200])
ax.grid()

fig.savefig("plots/" + regex + ".png")

