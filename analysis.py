import matplotlib.pyplot as plt
import csv, os, logging
from pprint import pprint

from difflib import SequenceMatcher
import numpy as np

def process_results(path, filename, desired_plots):

    assert(os.path.isdir(path))
    path_to_csv = os.path.join(path,filename)
    path_to_figures = os.path.join(path,'figures')
    assert(not os.path.exists(path_to_figures))
    os.mkdir(path_to_figures)

    # read results
    with open(path_to_csv,'r') as csvfile:
         reader = csv.reader(csvfile, delimiter=',')
         header = next(reader,None)
         data = {}
         counter = 0
         for line in reader:
             counter += 1
             data[counter] = line # data maps row indices to the array with the whole line

    def plot(var_x, var_y, group=None, save=True):

        xvals = []
        yvals = {}
        x_index = header.index(var_x)
        y_index = []
        for i in range(len(var_y)):
            y_index.append(header.index(var_y[i]))
        if group is not None:
            groupvals = []
            group_index = header.index(group)
        for i in range(len(var_y)):
            yvals[i] = []
            for line in data.values():
                yvals[i].append(float(line[y_index[i]]))
        for line in data.values():
            xvals.append(float(line[x_index]))
            if group is not None:
                groupvals.append(float(line[group_index]))

        indices = np.argsort(xvals) #make sure the x values are always ordered low-to-high

        xvals = np.asarray(xvals)[indices]
        for i in range(len(var_y)):
            yvals[i] = np.asarray(yvals[i])[indices]

        fig = plt.figure()
        ax = fig.add_subplot(111)
        if group is not None:
            groupvals = np.asarray(groupvals)[indices]
            line_ids = np.unique(groupvals)
            for i in line_ids:
                ax.plot(xvals[np.where(groupvals==i)], yvals[0][np.where(groupvals==i)], label=group + '=' + '{:d}'.format(int(i)))
        else:
            for i in range(len(var_y)):
                ax.plot(xvals, yvals[i], label=var_y[i])
        ax.set_xlabel(var_x)

        if len(var_y) == 1:
            ax.set_ylabel(var_y[0])
        else:
            match = SequenceMatcher(None, var_y[0], var_y[1]).find_longest_match(0, len(var_y[0]), 0, len(var_y[1]))

            ax.set_ylabel(var_y[0][match.a: match.a + match.size])

        all_y_values = [y for yy in yvals.values() for y in yy]
        plt.axis([0.9*min(xvals),1.1*max(xvals),0.9*min(all_y_values),1.1*max(all_y_values)])
        plt.legend()

        if save:
            filename = var_x + '_vs_' + str(var_y) +'.png'
            plt.savefig(os.path.join(path_to_figures,filename), dpi=300)
        else:
            plt.show()

    for (x,y,group) in desired_plots:
        plot(x,y,group)


# x,y (can be multiple if group = None)
# group=optional


# desired_plots = [
# ('problem size', ['avg length'], '#agents'),
# ('problem size', ['avg plan density'], '#agents'),
# ('problem size', ['avg time'], '#agents'),
# ('problem size', ['avg compression'], '#agents'),
# ('#agents', ['avg length'], 'problem size'),
# ('#agents', ['avg plan density'],'problem size'),
# ('#agents', ['avg time'], 'problem size'),
# ('#agents', ['avg compression'], 'problem size'),
# ]
# filename = 'combined.csv'
# process_results('./experiment05/',filename,desired_plots)


desired_plots = [
('#agents', ['min length','avg length','max length'],None),
('#agents', ['avg plan density'],None),
('#agents', ['min time','avg time','max time'],None),
('#agents', ['avg compression'],None)
]
filename = 'combined.csv'
process_results('./experiment3/',filename,desired_plots)
