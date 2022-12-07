import csv
import numpy as np
import matplotlib.pyplot as plt
import sys

text_type = sys.argv[1].replace("--", "")

fig, ax = plt.subplots()
ax.set(xlabel="threshold", ylabel="accuracy", title="Accuracy of decision attack for different threshold values")
for c in ["snappy", "zlib"]:
    true_labels = []
    ref_scores = []
    with open('decision-data-results/decision-data-mongo-' + text_type + '-' + c + '.csv') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if(row[0] == "0" or row[0] == "1"):
                true_labels.append(int(row[0]))
                ref_scores.append((int(row[2]) if row[2] != "0" else 1, int(row[3]), int(row[4])))
            else:
                pass
                #print(row)
    true_labels = np.array(true_labels)
    pcts = [1 - (b_yes - b) / max(b_yes - b_no, 1) for b_no, b, b_yes in ref_scores]

    print(len(pcts))

    thresholds = np.arange(-0.5, 1.5, 0.001)
    accuracies = []
    for threshold in thresholds:
        labels = np.array([pct >= threshold for pct in pcts])
        accuracy = 1 - np.sum(np.abs(labels - true_labels)) / labels.shape[0]
        accuracies.append(accuracy)

    ax.plot(thresholds, accuracies, label=c)
    
    f = open(text_type + "_" + c+"_threshold_data.csv", "w")
    f.write("threshold,accuracy\n")
    for i in range(0,len(thresholds)):
    	f.write(str(thresholds[i])+","+str(accuracies[i]) + "\n")
    f.close()
    #print(c + " thresholds: "+ str(thresholds))
    #print(c + " accuracies: "+ str(accuracies))

    maximum_accuracy = np.max(accuracies)
    maximum_threshold = -0.5 + 0.001*np.argmax(accuracies)
    print(c + ": maximum accuracy achieved: " + str(maximum_accuracy))
    print(c + ": maximum accuracy threshold: " + str(maximum_threshold))

    '''
    print("Errors:")
    labels = np.array([pct >= maximum_threshold for pct in pcts])
    for idx, label in enumerate(labels):
        l = 1 if label else 0
        if l != true_labels[idx]:
            print(str(idx) + "," + str(true_labels[idx]) + ": " + str(pcts[idx]))
    '''

plt.legend()
ax.grid()
plt.savefig("threshold-accuracy.png")
plt.show()

