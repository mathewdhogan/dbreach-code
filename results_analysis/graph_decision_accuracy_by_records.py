import csv
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import sys

fig, ax = plt.subplots()
ax.set(xlabel="Records on page", ylabel="accuracy", title="Accuracy of decision attack vs. number of records on page")

text_type = sys.argv[1].replace("--", "")

# fill in thresholds with chosen t_yes values:
thresholds = dict()
thresholds["snappy"] = 0.492
thresholds["zlib"] = 0.515 
#thresholds["lz4"] = 0.78

# if graphing for MariaDB, add "lz4" back to thist list & uncomment lz4 line above
for c in ["snappy", "zlib"]:
    ref_scores = defaultdict(lambda: [])
    true_labels = defaultdict(lambda: [])
    with open('decision-data-results/decision-data-mongo-' + text_type + '-' + c + '.csv') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0]=="0" or row[0]=="1":
                true_labels[int(row[1])].append(int(row[0]))
                ref_scores[int(row[1])].append((int(row[2]) if row[2] != "0" else 1, int(row[3]), int(row[4])))

    threshold = thresholds[c]
    accuracies = []
    for records_on_page in ref_scores.keys():
        pcts = [1 - (b_yes - b) / max(b_yes - b_no, 1) for b_no, b, b_yes in ref_scores[records_on_page]]
        labels = np.array([pct >= threshold for pct in pcts])
        accuracy = 1 - np.sum(np.abs(labels - true_labels[records_on_page])) / labels.shape[0]
        accuracies.append((records_on_page, accuracy))

    accuracies.sort()

    print(c + ": " + str(accuracies))

    ax.plot([recs_on_page for recs_on_page, accuracy in accuracies], [accuracy for recs_on_page, accuracy in accuracies], label=c)

plt.legend()
ax.grid()
plt.ylim([0.0,1.0])
plt.yticks(np.arange(0, 1.0, 0.1))
plt.savefig("decision-records-accuracy.png")
plt.show()

