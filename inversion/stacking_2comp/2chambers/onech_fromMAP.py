#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 14:21:02 2020

@author: aroman
"""

import matplotlib.pyplot as plt
import numpy as np
from onech_lib import *
import numpy as np
import emcee
import pickle
from preparedata import preparation
from multiprocessing import Pool
import os
import sys
np.random.seed(1234567284)
path_results = '../../../../results/onech/'
pathMAP = 'locErr/'
    

pathrun = 'dxshort'

model_type = 'UF'

stations  = ['UWD']
date = '07-03-2018'
flaglocation = 'N'      # This is the flag for locations priors, F for Uniform, N for Normal

def parameters_init(mt):
    #Initialize parameters
    dxmax = 7
    dxmin = 3.0

    Ncycmin = 20
    Ncycmax = 120

    if mt == 'UF':
        bounds = np.array([[+8,12],[+7,+11],[dxmin,dxmax],[Ncycmin,Ncycmax],[1,10],[0.5,2]])
        boundsLoc = np.array([[-1000,1000],[1200,2500],[500,1500],[-1500,+1500],[-1500,2500],[2000,4000]])
    elif mt == 'LF':                                                 
        bounds = np.array([[+8,+12],[+7,+11],[dxmin,dxmax],[Ncycmin,Ncycmax],[1,10],[0.5,2]])
        boundsLoc = np.array([[-1000,+1000],[-1000,1000],[2000,5000],[-500,0],[1500,2000],[500,1300]])

    bndtiltconst = 2000
    bndGPSconst = 200
    tiltErr = 1e-5
    GPSErr = 1e-2
    locErrFact = 5
    
    a_parameter = 2
    thin = 10
    nwalkers = 64

    rho = 2600
    g = 9.8
    #Conduit parameters
    ls = 4e+4
    mu = 100
    #Elastic properties
    poisson = 0.25
    lame = 3e+9
    #Cylinder parameters
    Rcyl = 1.0e+3
    ndim = len(bounds)
    const = -9. /(4 * 3.14) * (1 - poisson) / lame
    S = 3.14 * Rcyl**2 
    rhog = rho * g
    return bounds,boundsLoc,bndtiltconst,bndGPSconst,tiltErr,GPSErr,locErrFact,a_parameter,thin,nwalkers,ls,mu,ndim,const,S,rhog






if len(stations) > 1:
    pathtrunk = 'priors' + flaglocation +  '/' + model_type + '/' + str(len(stations)) + 'st'
else:
    pathtrunk = 'priors' + flaglocation +  '/' + model_type + '/' + stations[0]


pathtrunk = pathtrunk + '/' + date + '/'

pathgg = pathtrunk + pathrun
pathgg  =  pathgg + '/'
pathgg = path_results + pathgg
pathMAP =  os.path.join(os.path.dirname(os.path.dirname(pathgg)),pathMAP)

if not os.path.exists(pathgg):
    os.makedirs(pathgg)
    descr =input('Briefly describe the run: ')
    f =  open(pathgg + 'description.txt','w')
    f.write(descr)
    f.close()
else:
    print('Directory exists! CHeck that everything is ok!')
    
f = open(path_results+'dir_current_run.txt','w')
f.write(os.path.abspath(pathgg))
f.close()
if  os.path.isfile(pathgg + 'progress.h5'):
    Nst,nstation,x,y,tTilt,tx,ty,tGPS,GPS,locTruth,locErr,t0= pickle.load(open(pathgg + 'data.pickle','rb'))
    a = pickle.load(open(pathgg + 'parameters.pickle','rb'))
    if len(a)== 17:
        bounds,bndtiltconst,bndGPSconst,tiltErr,GPSErr,bndp0,locErrFact,a_parameter,thin,nwalkers,ls,ld,mu,ndim,const,S,rhog = a
        boundsLoc = 0
    elif len(a)== 18:
        bounds,boundsLoc,bndtiltconst,bndGPSconst,tiltErr,GPSErr,bndp0,locErrFact,a_parameter,thin,nwalkers,ls,ld,mu,ndim,const,S,rhog = a
    reader = emcee.backends.HDFBackend(pathgg + 'progress.h5', read_only=True)
    niter  = reader.iteration
    print('The current run is: ',os.path.abspath(pathgg))
    answer = input('Found past run with ' + str(niter) +' samples. Do you want to continue this run? Enter the number of iteration that additionally you want to do: ')
    moreiter = int(answer)
    print('Restarting!!!!')
    nwalkers,ndim = reader.shape
    filename = pathgg + "progress.h5"
    backend = emcee.backends.HDFBackend(filename)
    move = emcee.moves.StretchMove(a=a_parameter)
    with Pool() as pool:
        if model_type == 'UF':
            sampler = emcee.EnsembleSampler(nwalkers, ndim, log_probability_UF,
                                            args=(x,y,
                                                  ls,ld,mu,
                                                  rhog,const,S,
                                                  tTilt,tGPS,tx,ty,GPS,
                                                  tiltErr,GPSErr,bounds,boundsLoc,bndGPSconst,bndtiltconst,bndp0,locTruth,locErr,nstation,flaglocation),moves = [move], backend = backend, pool = pool)
        elif model_type =='LF':
            sampler = emcee.EnsembleSampler(nwalkers, ndim, log_probability_LF,
                                            args=(x,y,
                                                  ls,ld,mu,
                                                  rhog,const,S,
                                                  tTilt,tGPS,tx,ty,GPS,
                                                  tiltErr,GPSErr,bounds,boundsLoc,bndGPSconst,bndtiltconst,bndp0,locTruth,locErr,nstation,flaglocation),moves = [move], backend = backend, pool = pool)
        sampler.run_mcmc(None, moreiter, progress=True,thin = thin)



else:
    print('The put of the current run is: ',pathgg)
    niter = input('How many iteration you want to run? ')
    bounds,boundsLoc,bndtiltconst,bndGPSconst,tiltErr,GPSErr,locErrFact,a_parameter,thin,nwalkers,ls,mu,ndim,const,S,rhog = parameters_init(model_type)
    Nst,nstation,x,y,tTilt,tx,ty,tGPS,GPS,locTruth,locErr,t0 = preparation(stations,date,locErrFact,model_type)
    locTruth = locTruth[:3]
    locErr = locErr[:3]
    pos,nwalkers,ndim = walkers_init_MAP(pathMAP,Nst)
    pickle.dump((Nst,nstation,x,y,tTilt,tx,ty,tGPS,GPS,locTruth,locErr,t0),open(pathgg + 'data.pickle','wb'))
    pickle.dump((bounds,boundsLoc,bndtiltconst,bndGPSconst,tiltErr,GPSErr,locErrFact,a_parameter,thin,nwalkers,ls,mu,ndim,const,S,rhog),open(pathgg + 'parameters.pickle','wb'))
    filename = pathgg + "progress.h5"
    backend = emcee.backends.HDFBackend(filename)
    move = emcee.moves.StretchMove(a=a_parameter)
    with Pool() as pool:
        sampler = emcee.EnsembleSampler(nwalkers, ndim, log_probability,
                                        args=(x,y,
                                            ls,mu,
                                            rhog,const,S,
                                            tTilt,tGPS,tx,ty,GPS,
                                            tiltErr,GPSErr,bounds,boundsLoc,bndGPSconst,bndtiltconst,locTruth,locErr,nstation,flaglocation),moves = [move], backend = backend, pool = pool)
       
        print('Running main sampling')
        sampler.run_mcmc(pos,niter, progress = True,thin = thin)
        