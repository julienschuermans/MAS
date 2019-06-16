import matplotlib.pyplot as plt
import csv, os, logging
from pprint import pprint

from difflib import SequenceMatcher
import numpy as np

from shutil import copyfile


def process_results(path, filename, desired_plots, avg=False):

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
        for i in range(len(var_y)): # iterate over values to plot
            yvals[i] = np.asarray(yvals[i])[indices] #reorder the y values according to their x component

            if avg: #there are multiple y values per x value, take the average plz
                if group is None:
                    new_xvals = np.unique(xvals)
                    new_yvals = np.zeros_like(new_xvals)
                    for j in range(len(new_xvals)):
                        x = new_xvals[j]
                        new_yvals[j] = np.mean(yvals[i][np.where(xvals==x)]) # take the mean of all y values at this x position

                    xvals = new_xvals
                    yvals[i] = new_yvals
                else:
                    # take the average per group
                    nb_xvals = len(np.unique(xvals))
                    groupvals = np.asarray(groupvals)[indices]
                    line_ids = np.unique(groupvals)
                    nb_groups = len(np.unique(groupvals))
                    new_xvals = np.zeros((nb_xvals*nb_groups,1))
                    new_yvals = np.zeros_like(new_xvals)
                    new_groupvals = np.zeros_like(new_xvals)
                    for k in line_ids:
                        for j in range(nb_xvals):
                            x = new_xvals[j]
                            new_yvals[k] = np.mean(yvals[i][np.where(xvals==x)]) # take the mean of all y values at this x position
                    xvals = new_xvals
                    yvals[i] = new_yvals
                    groupvals = new_groupvals

        fig = plt.figure()
        ax = fig.add_subplot(111)
        if group is not None:
            groupvals = np.asarray(groupvals)[indices]
            line_ids = np.unique(groupvals)
            for i in line_ids:
                # ax.set_yscale('log')
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

        if group is not None or len(var_y)>1:
            plt.legend()

        if save:
            filename = var_x + '_vs_' + str(var_y) +'.png'
            plt.savefig(os.path.join(path_to_figures,filename), dpi=300)
        else:
            plt.show()

    for (x,y,group) in desired_plots:
        plot(x,y,group)

def combine_results(folder):
    new_csv = os.path.join(folder, 'combined.csv')
    count = 0

    subdirs = []

    for dir,_,files in os.walk(folder):
        if 'averaged.csv' in files:
            subdirs.append(dir)

    for dir in sorted(subdirs):
        if count == 0:
            count += 1
            copyfile(os.path.join(dir,'averaged.csv'), new_csv)
        else:
            with open(os.path.join(dir,'averaged.csv'),'r') as csvfile:
                 reader = csv.reader(csvfile, delimiter=',')
                 header = 0
                 for row in reader:
                     if header > 0:
                         with open(new_csv,'a',newline='') as csv2:
                             writer = csv.writer(csv2, delimiter=',')
                             writer.writerow(row)
                     else:
                         header += 1

def calc_averages(folder):
    subdirs = []
    for dir,_,files in os.walk(folder):
        if 'results.csv' in files:
            subdirs.append(dir)

    for dir in sorted(subdirs):
        with open(os.path.join(dir,'results.csv'),'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            header = next(reader,None)
            summed_data = np.zeros(np.shape(header))
            # med_data = np.zeros_like(summed_data) # uncomment this stuff to calculate median instead of average
            # data = np.zeros((5,np.shape(header)[0]))
            counter = 0
            for line in reader:
                for x in range(len(line)):
                    summed_data[x] += float(line[x])
                    # data[counter,x] = line[x]
                counter += 1

            for x in range(len(summed_data)):
                summed_data[x] = '{:.4f}'.format(summed_data[x]/counter)
                # med_data[x] = '{:.4f}'.format(np.median(data[:,x]))
        with open(os.path.join(dir,'averaged.csv'),'w',newline='') as csv2:
            writer = csv.writer(csv2, delimiter=',')
            writer.writerow(header)
            writer.writerow(summed_data)

RUN_DEMO_ONLY = True

if RUN_DEMO_ONLY:
    desired_plots = [
    ('#agents', ['avg compression'], None),
    ('#agents', ['avg plan density'],None),
    ('#agents', ['avg time'],None),
    ]
    filename = 'results.csv'
    process_results('./demo_results/',filename,desired_plots)
else:
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


    # desired_plots = [
    # ('#agents', ['min length','avg length','max length'],None),
    # ('#agents', ['avg plan density'],None),
    # ('#agents', ['min time','avg time','max time'],None),
    # ('#agents', ['avg compression'],None)
    # ]
    # filename = 'combined.csv'
    # process_results('./experiment3/',filename,desired_plots)

    # desired_plots = [
    # ('#agents', ['single agent plan length', 'avg length', 'min length', 'max length'],None),
    # ]
    # filename = 'combined.csv'
    # process_results('./experiment5/',filename,desired_plots,avg=True)

    calc_averages('experiment6/')
    combine_results('experiment6/')

    desired_plots = [
    ('problem size', ['avg compression'], '#agents'),
    ('problem size', ['avg plan density'], '#agents'),
    ]
    filename = 'combined.csv'
    process_results('./experiment6/',filename,desired_plots)
