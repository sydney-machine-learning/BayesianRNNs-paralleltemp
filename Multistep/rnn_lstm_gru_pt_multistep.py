#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 12:02:16 2019
@author: ashrey
"""
import torch
import torch.nn as nn
import numpy as np
import random
import matplotlib.pyplot as plt
import math
import os
import copy
import argparse
import time
import datetime
import multiprocessing
import gc
import matplotlib as mpl
import pandas as pd
from model import Model

mpl.use('agg')
weightdecay = 0.01
#Initialise and parse inputs
parser=argparse.ArgumentParser(description='PTBayeslands modelling')
parser.add_argument('-n','--net', help='Choose rnn net, "1" for RNN, "2" for GRU, "3" for LSTM', default = 1, dest="net",type=int)
parser.add_argument('-s','--samples', help='Number of samples', default=100000, dest="samples",type=int)
parser.add_argument('-r','--replicas', help='Number of chains/replicas, best to have one per availble core/cpu', default=10,dest="num_chains",type=int)
parser.add_argument('-t','--temperature', help='Demoninator to determine Max Temperature of chains (MT=no.chains*t) ', default=3,dest="mt_val",type=int)
parser.add_argument('-swap','--swap', help='Swap Ratio', dest="swap_ratio",default=0.1,type=float)
parser.add_argument('-b','--burn', help='How many samples to discard before determing posteriors', dest="burn_in",default=0.25,type=float)
parser.add_argument('-pt','--ptsamples', help='Ratio of PT vs straight MCMC samples to run', dest="pt_samples",default=0.5,type=float)
parser.add_argument('-step','--step', help='Step size for proposals (0.02, 0.05, 0.1 etc)', dest="step_size",default=0.05,type=float)
parser.add_argument('-lr','--learn', help='learn rate for langevin gradient', dest="learn_rate",default=0.1,type=float)
args = parser.parse_args()

def f(): raise Exception("Found exit()")


def data_loader(filename):
    f=open(filename,'r')
    x=[[[]]]
    count=0
    y=[[[]]]
    while(True):
        count+=1
        #print(count)
        text = f.readline()
        #print(text)
        if(text==''):
           break
        if(len(text.split()) == 0):
            #print(text)
            text=f.readline()
        if(text==''):
           break
        #print(text)
        t=int(text)
        a=[[]]
        ya=[[]]
        for i in range(0,t):
            temp=f.readline().split(' ')
            b=0.0
            for j in range(0,len(temp)):
                b=[float(temp[j])]
            a.append(b)
        del a[0]
        x.append(a)
        temp=f.readline().split(' ')
        #print(temp)
        for j in range(0,len(temp)):
            if temp[j] != "\n":
                ya.append([float(temp[j])])
        del ya[0]
        y.append(ya)
    del x[0]
    del y[0]
    return x,y
def print_data(x,y):
    # assuming x is 3 dimensional and y is 2 dimensional
    for i in range(0,len(x)):
        for j in range(0,len(x[i])):
            print(x[i][j])
        print(y[i])
        print(' ')
def shuffledata(x,y):
    a=[]
    for i in range(0,len(x)):
        a.append(i)
    random.shuffle(a)
    x1 = []
    y1=[]
    for item in a:
        x1.append(x[item])
        y1.append(y[item])
    return x1,y1
def load_horizontal(fname):
    f = open(fname,'r')
    x=[[]]
    count=0
    y=[]
    while(True):
        count+=1
        #print(count)
        text = f.readline()
        #print(text)
        if(text==''):
           break
        if(len(text.split()) == 0):
            #print(text)
            text=f.readline()
        if(text==''):
           break
        #print(text)
        a=[]
        for i in range(0,len(text.split(' '))-1):
            #print(text.split(' ')[i].strip())
            temp = float(text.split(' ')[i].strip())
            a.append([temp])
        y.append([float(text.split(' ')[-1].strip())])
        if a[0] == []:
            del a[0]
        x.append(a)
        #print(count)
    if (x[0]) == [] or x[0] == [[]] :
        del x[0]
    if y[0] == [] or y[0] == [[]]:
        del y[0]
    return x,y
def main():
    networks = ['RNN','GRU','LSTM']
    net = networks[args.net-1]
    networks = ['RNN']
    n_steps_in, n_steps_out = 5,10
    for net in networks:
        for j in range(4, 5) :
            print(j, ' out of 15','\n\n\n\n\n\n\n')
            i = j//2
            problem=i
            folder = "data/MultiStepAhead"
            if problem ==1:
                TrainData = pd.read_csv(folder+"/data/Lazer/train1.csv",index_col = 0)
                TrainData = TrainData.values
                TestData = pd.read_csv(folder+"/data/Lazer/test1.csv",index_col = 0)
                TestData = TestData.values
                name= "Lazer"
            if problem ==2:
                TrainData = pd.read_csv("/data/Sunspot/train1.csv",index_col = 0)
                TrainData = TrainData.values
                TestData = pd.read_csv("/data/Sunspot/test1.csv",index_col = 0)
                TestData = TestData.values
                name= "Sunspot"
            if problem ==3:
                TrainData = pd.read_csv("../data/Mackey/train1.csv",index_col = 0)
                TrainData = TrainData.values
                TestData = pd.read_csv("../data/Mackey/test1.csv",index_col = 0)
                TestData = TestData.values
                name="Mackey"
            if problem ==4:
                TrainData = pd.read_csv("../data/Lorenz/train1.csv",index_col = 0)
                TrainData = TrainData.values
                TestData = pd.read_csv("../data/Lorenz/test1.csv",index_col = 0)
                TestData = TestData.values  
                name= "Lorenz"
            if problem ==5:
                TrainData = pd.read_csv("../data/Rossler/train1.csv",index_col = 0)
                TrainData = TrainData.values
                TestData = pd.read_csv("../data/Rossler/test1.csv",index_col = 0)
                TestData = TestData.values
                name= "Rossler"
            if problem ==6:
                TrainData = pd.read_csv("../data/Henon/train1.csv",index_col = 0)
                TrainData = TrainData.values
                TestData = pd.read_csv("../data/Henon/test1.csv",index_col = 0)
                TestData = TestData.values
                name= "Henon"
            if problem ==7:
                TrainData = pd.read_csv("../data/ACFinance/train1.csv",index_col = 0)
                TrainData = TrainData.values
                TestData = pd.read_csv("../data/ACFinance/test1.csv",index_col = 0)
                TestData = TestData.values
                name= "ACFinance" 
            
            train_x = np.array(TrainData[:,0:n_steps_in])
            train_y = np.array(TrainData[:,n_steps_in : n_steps_in+n_steps_out ])
            test_x = np.array(TestData[:,0:n_steps_in])
            test_y = np.array(TestData[:,n_steps_in : n_steps_in+n_steps_out])
            
            train_x = train_x.reshape(train_x.shape[0],train_x.shape[1],1)
            train_y = train_y.reshape(train_y.shape[0],train_y.shape[1],1)
            test_x = test_x.reshape(test_x.shape[0],test_x.shape[1],1)
            test_y = test_y.reshape(test_y.shape[0],test_y.shape[1],1)
            print("shapes of train x and y",train_x.shape,train_y.shape)
            # shapes of train x and y (585, 5) (585, 10)
            ###############################
            #THESE ARE THE HYPERPARAMETERS#
            ###############################
            Hidden = 5
            #ip = 4 #input
            #output = 1
            topology = [n_steps_in, Hidden,n_steps_out]
            NumSample = args.samples
            #NumSample = 500
            ###############################
            #THESE ARE THE HYPERPARAMETERS#
            ###############################
            netw = topology
            #print(traindata)
            #y_test =  testdata[:,netw[0]]
            #y_train =  traindata[:,netw[0]]
            maxtemp = args.mt_val
            #swap_ratio =  0.04
            swap_ratio = args.swap_ratio
            num_chains =  args.num_chains
            swap_interval = int(swap_ratio * NumSample/num_chains)    # int(swap_ratio * (NumSample/num_chains)) #how ofen you swap neighbours. note if swap is more than Num_samples, its off
            burn_in = args.burn_in
            learn_rate = args.learn_rate  # in case langevin gradients are used. Can select other values, we found small value is ok.
            langevn = ""
            if j%2 == 1:
                use_langevin_gradients = True  # False leaves it as Random-walk proposals. Note that Langevin gradients will take a bit more time computationally
                langevn = "T"
            else:
                use_langevin_gradients = False
                langevn = "F"
                pass # we dont want to execute this.
            problemfolder = os.getcwd()+'/Res_LG-Lprob_'+net+'/'  #'/home/rohit/Desktop/PT/Res_LG-Lprob/'  # change this to your directory for results output - produces large datasets
            problemfolder_db = 'Res_LG-Lprob_'+net+'/'  # save main results
            filename = ""
            run_nb = 0
            while os.path.exists( problemfolder+name+langevn+'_%s' % (run_nb)):
                run_nb += 1
            if not os.path.exists( problemfolder+name+langevn+'_%s' % (run_nb)):
                os.makedirs(  problemfolder+name+langevn+'_%s' % (run_nb))
                path = (problemfolder+ name+langevn+'_%s' % (run_nb))
            filename = ""
            run_nb = 0
            while os.path.exists( problemfolder_db+name+langevn+'_%s' % (run_nb)):
                run_nb += 1
            if not os.path.exists( problemfolder_db+name+langevn+'_%s' % (run_nb)):
                os.makedirs(  problemfolder_db+name+langevn+'_%s' % (run_nb))
                path_db = (problemfolder_db+ name+langevn+'_%s' % (run_nb))
            resultingfile = open( path+'/master_result_file.txt','a+')
            resultingfile_db = open( path_db+'/master_result_file.txt','a+')
            timer = time.time()
            langevin_prob = 1/10
            pt = ParallelTempering( use_langevin_gradients,  learn_rate,  train_x,train_y,test_x,test_y, topology, num_chains, maxtemp, NumSample, swap_interval, langevin_prob, path,rnn_net = net)
            directories = [  path+'/predictions/', path+'/posterior', path+'/results', path+'/surrogate', path+'/surrogate/learnsurrogate_data', path+'/posterior/pos_w',  path+'/posterior/pos_likelihood',path+'/posterior/surg_likelihood',path+'/posterior/accept_list'  ]
            for d in directories:
                pt.make_directory((filename)+ d)
            pt.initialize_chains(  burn_in)
            pos_w, fx_train, fx_test,  rmse_train, rmse_test, acc_train, acc_test,   likelihood_rep , swap_perc,    accept_vec, accept = pt.run_chains()
            list_end = accept_vec.shape[1]
            #print(accept_vec.shape)
            #print(accept_vec)
            accept_ratio = accept_vec[:,  list_end-1:list_end]/list_end
            accept_per = np.mean(accept_ratio) * 100
            print(accept_per, ' accept_per')
            timer2 = time.time()
            timetotal = (timer2 - timer) /60
            print ((timetotal), 'min taken')
            #PLOTS
            '''acc_tr = np.mean(acc_train [:])
            acctr_std = np.std(acc_train[:])
            acctr_max = np.amax(acc_train[:])
            acc_tes = np.mean(acc_test[:])
            acctest_std = np.std(acc_test[:])
            acctes_max = np.amax(acc_test[:])'''
            rmse_tr = np.mean(rmse_train[:])
            rmsetr_std = np.std(rmse_train[:])
            rmsetr_max = np.amin(rmse_train[:])
            rmse_tes = np.mean(rmse_test[:])
            rmsetest_std = np.std(rmse_test[:])
            rmsetes_max = np.amin(rmse_test[:])
            outres = open(path+'/result.txt', "a+")
            outres_db = open(path_db+'/result.txt', "a+")
            resultingfile = open(problemfolder+'/master_result_file.txt','a+')
            resultingfile_db = open( problemfolder_db+'/master_result_file.txt','a+')
            xv = name+langevn+'_'+ str(run_nb)
            allres =  np.asarray([ problem, NumSample, maxtemp, swap_interval, langevin_prob, learn_rate,  rmse_tr, rmsetr_std, rmsetr_max, rmse_tes, rmsetest_std, rmsetes_max, swap_perc, accept_per, timetotal])
            np.savetxt(outres_db,  allres   , fmt='%1.4f', newline=' '  )
            np.savetxt(resultingfile_db,   allres   , fmt='%1.4f',  newline=' ' )
            np.savetxt(resultingfile_db, [xv]   ,  fmt="%s", newline=' \n' )
            np.savetxt(outres,  allres   , fmt='%1.4f', newline=' '  )
            np.savetxt(resultingfile,   allres   , fmt='%1.4f',  newline=' ' )
            np.savetxt(resultingfile, [xv]   ,  fmt="%s", newline=' \n' )
            x = np.linspace(0, rmse_train.shape[0] , num=rmse_train.shape[0])
            '''plt.plot(x, rmse_train, '.',   label='Test')
            plt.plot(x, rmse_test,  '.', label='Train')
            plt.legend(loc='upper right')
            plt.xlabel('Samples', fontsize=12)
            plt.ylabel('RMSE', fontsize=12)
            plt.savefig(path+'/rmse_samples.png')
            plt.clf()	'''
            plt.plot(  rmse_train, '.',  label='Test')
            plt.plot(  rmse_test,  '.',  label='Train')
            plt.legend(loc='upper right')
            plt.xlabel('Samples', fontsize=12)
            plt.ylabel('RMSE', fontsize=12)
            plt.savefig(path_db+'/rmse_samples.pdf')
            plt.clf()
            plt.plot( rmse_train, '.',   label='Test')
            plt.plot( rmse_test, '.',   label='Train')
            plt.legend(loc='upper right')
            plt.xlabel('Samples', fontsize=12)
            plt.ylabel('RMSE', fontsize=12)
            plt.savefig(path+'/rmse_samples.pdf')
            plt.clf()
            likelihood = likelihood_rep[:,0] # just plot proposed likelihood
            likelihood = np.asarray(np.split(likelihood, num_chains))
        # Plots
            plt.plot(likelihood.T)
            plt.xlabel('Samples', fontsize=12)
            plt.ylabel(' Log-Likelihood', fontsize=12)
            plt.savefig(path+'/likelihood.png')
            plt.clf()
            plt.plot(likelihood.T)
            plt.xlabel('Samples', fontsize=12)
            plt.ylabel(' Log-Likelihood', fontsize=12)
            plt.savefig(path_db+'/likelihood.png')
            plt.clf()
            plt.plot(accept_vec.T )
            plt.xlabel('Samples', fontsize=12)
            plt.ylabel(' Number accepted proposals', fontsize=12)
            plt.savefig(path_db+'/accept.png')
            plt.clf()
            #mpl_fig = plt.figure()
            #ax = mpl_fig.add_subplot(111)
            # ax.boxplot(pos_w)
            # ax.set_xlabel('[W1] [B1] [W2] [B2]')
            # ax.set_ylabel('Posterior')
            # plt.legend(loc='upper right')
            # plt.title("Boxplot of Posterior W (weights and biases)")
            # plt.savefig(path+'/w_pos.png')
            # plt.savefig(path+'/w_pos.svg', format='svg', dpi=600)
            # plt.clf()
            #dir()
            gc.collect()
            outres.close()
            resultingfile.close()
            resultingfile_db.close()
            outres_db.close()
if __name__ == "__main__": main()