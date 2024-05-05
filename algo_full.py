# -*- coding: utf-8 -*-
"""Algo_full.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1iVSiZZyQicK020n5bd_JFZJTVFiAJMUp
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random as rn
from sklearn import preprocessing
import math
from scipy.stats import multinomial
from sklearn.cluster import KMeans
from scipy.stats import multivariate_normal
from scipy.special import logit, expit
from scipy.stats import multivariate_normal
from scipy.special import factorial
from collections import defaultdict
from algorithm_alpha import algorithm_alpha

def cross_log(pi, y):
  interm = []
  for i in range(len(y)):
    interm.append(math.log((pi[i] ** y[i]) * ((1 - pi[i]) ** (1 - y[i]) )))
  return interm

def poisson_log_loss(lam, y):
    log_loss = []
    for i in range(len(y)):
      log_loss = y[i] * math.log(lam[i]) + lam[i] + math.log(math.factorial(y[i]))
    return log_loss

def all_mydmultinom_log(V, prob, v):
    if v == 1:
      result = np.zeros(len(V))
      for j in range(len(V)):
        if V.iloc[j] == 1:
          esito = [V.iloc[j], 0]
        else:
          esito = [V.iloc[j], 1]
        result[j] = np.log(multinomial.pmf(esito, n=1, p=[prob[0], 1-prob[0]]))
    else :
      result = np.zeros(V.shape[0])
      for i in range(v):
        for j in range(len(V.iloc[:,i])):
          if V.iloc[j,i] == 1:
            esito = [V.iloc[j,i], 0]
          else:
            esito = [V.iloc[j,i], 1]
          result[j] += np.log(multinomial.pmf(esito, n=1, p=[prob[i], 1-prob[i]]))
    return result

def mymult3(w, arr1, U):
    result = np.zeros((U.shape[1], U.shape[1]))
    for i in range(arr1.shape[0]):
        result += w[i] * np.outer(arr1.iloc[i, :], arr1.iloc[i, :])
    return result

def mymult4(w, V):
    result = np.sum(w * V, axis=0)
    return result

def initialize_params(data, y,U, C, num_fix, num_group, alpha, mod, num_obs_groups,group_name, name_fix, y_name, V=None):

  # initialization of the weights w using k-means
  kmeans_result = KMeans(n_clusters=C, n_init=10)
  kmeans_result.fit(U)
  w = [np.sum(kmeans_result.labels_ == c) / U.shape[0] for c in range(C)]
  params = {"w": w}

  # initialization of mu and sigma
  initial_z = np.zeros((U.shape[0], C), dtype=int)
  mu = kmeans_result.cluster_centers_
  sigma = np.zeros((U.shape[1], U.shape[1], C))
  for c in range(C):
    cluster_indices = np.where(kmeans_result.labels_ == c)
    cluster_data = U.iloc[cluster_indices[0]]
    sigma[:, :, c] = np.cov(cluster_data, rowvar=False)
    initial_z[cluster_indices,c] = 1


  params["mu"] = mu
  params["sigma"] = sigma


  # initialization of lambda
  if V is not None:
    forma = V.shape
    if len(forma) > 1:
      v = forma[1]
    else:
      v = 1

    lambda_list = []

    for c in range(C):
      cluster_indices = np.where(kmeans_result.labels_ == c)
      lambda_c = []
      if v ==1:
        vec = V.iloc[cluster_indices[0]]
        lambda_c.append(np.sum(vec, axis=0) / vec.shape[0])
      else :
        for i in range(v):
          vec = V.iloc[cluster_indices[0], i]
          lambda_c.append(np.sum(vec, axis=0) / vec.shape[0])

      lambda_list.append(lambda_c)

    params["lam"] = lambda_list


  # initialization of parameters of SPGLMM

  fitted_values = []
  fix_param = []
  groups = []
  interc = []
  knots_save = []
  hessiana = []

  fitted_cluster = np.zeros(len(data['y']))
  for i in range(len(data['y'])):
     fitted_cluster[i] = np.argmax(initial_z[i])

  for c in range(C):
    # raggruppare le osservazioni rispetto ai gruppi
    data_c = data[fitted_cluster == c]
    y_c = list(data_c.groupby(group_name)['y'].apply(np.array).values)
    lengths_c = np.array(data_c.groupby(group_name).count().reset_index().iloc[:,1])
    num_group_c = len(data_c.groupby(group_name).count().reset_index()[group_name])
    data_fix = defaultdict(list)
    for i in range(num_fix):
      data_fix[i] = data_c.groupby(group_name)[name_fix[i]].apply(np.array).values.tolist()

    knots, par, W, hess_ran, hess_fix, others = algorithm_alpha(ran_var=False , ran_int=True,
                                                       n_fix=num_fix, sim=False,
                                                       tol=alpha, model=mod,
                                                       fix=data_fix, lengths=lengths_c,
                                                       y=y_c, N=num_group_c, t=None, data=data_c, 
                                                       name_fix=name_fix, name_output='y', name_group=group_name)

    fix_param.append(par)
    knots_save.append(knots)
    hessiana.append(hess_fix)

    #creo i gruppi
    group = np.zeros((num_group_c, 1))
    for i in range(num_group_c):
      group[i] = int(np.argmax(W[i, :]))
    groups.append(group)

   #fitted values
    X = pd.DataFrame({'cluster': range(len(knots)), 'knots': knots})
    Y = pd.DataFrame({'Group': data_c.groupby(group_name).count().reset_index()[group_name], 'cluster': group[:,0]})
    Z = Y.merge(X, on=['cluster'])
    data_copy_c = data_c.copy()
    data_copy_c.loc[:, 'Group'] = data_copy_c.loc[:, group_name]
    data_copy_c = data_copy_c.merge(data_copy_c.merge(Z, how='left', on='Group', sort=False))
    interc.append(data_copy_c['knots'])

    if mod == 'B':
      value = data_copy_c['knots'] + np.dot(data_copy_c[name_fix], par)
      fitted_values.append(1 / (1 + np.exp(-value)))
    elif mod == 'P':
      value = data_copy_c['knots'] + np.dot(data_copy_c[name_fix], par)
      fitted_values.append(np.round(np.exp(value)))

  params["rand_inter"] = interc
  params["fix_param"] = fix_param
  params["groups"] = groups
  params["fitted_values"] = fitted_values
  params["z"] = initial_z
  params["knots"] = knots_save
  params["hessian_fix"] = hessiana

  return params

def E_step(y, U, C, mod, params=None, V=None):

    # Carica i parametri dal dizionario 'params'
    w_old = params["w"]
    mu_old = params["mu"]
    sigma_old = params["sigma"]
    rand_inter_old = params["rand_inter"]
    fix_param_old = params["fix_param"]
    groups_old = params["groups"]
    fitted_values_old = params["fitted_values"]
    z_old = params["z"]
    if V is not None:
      lam_old = params["lam"]

    if V is not None:
      forma = V.shape
      if len(forma) > 1:
         v = forma[1]
      else:
         v = 1
    else:
      v = 0
    multinom_density = np.zeros((len(y), C))

    if V is not None:
        for i in range(C):
          if v == 1:
            multinom_density[z_old[:,i]==1, i] = all_mydmultinom_log(V.iloc[z_old[:,i]==1], lam_old[i], v)
          else:
            multinom_density[z_old[:,i]==1, i] = all_mydmultinom_log(V.iloc[z_old[:,i]==1,:], lam_old[i], v)


    z = np.zeros((U.shape[0], C))
    
    fitted_cluster = np.zeros(len(y))
    for i in range(len(y)):
       fitted_cluster[i] = np.argmax(z_old[i])
    
    for i in range(C):
      c_l = np.zeros(len(y))
      if mod == 'B':
        c_l[fitted_cluster==i] = cross_log(fitted_values_old[i], list(y[fitted_cluster==i]))
      else :
        c_l[z_old[:,i]==1] = poisson_log_loss(fitted_values_old[i], list(y[fitted_cluster==i]))
      log_likelihood = (np.log(w_old[i]) + c_l +
                         multivariate_normal.logpdf(U, mean=mu_old[i], cov=sigma_old[:,:,i], allow_singular=True) +
                         multinom_density[:,i])

      z[:, i] = np.exp(log_likelihood)

    for i in range(len(z)):
      divisor =  np.sum(z[i])
      for j in range(len(z[i])):
         z[i][j] = z[i][j] / divisor

    z = np.round(z)
    return z

def M_step(data, y, U, C, z, params, num_fix, num_group, alpha, mod, num_obs_groups, group_name, name_fix, y_name, V=None):

  # Carica i parametri dal dizionario 'params'
  w_old = params["w"]
  mu_old = params["mu"]
  sigma_old = params["sigma"]
  rand_inter_old = params["rand_inter"]
  fix_param_old = params["fix_param"]
  groups_old = params["groups"]
  fitted_values_old = params["fitted_values"]

  if V is not None:
    lam_old = params["lam"]

  new_params = {}
  sum_z = np.sum(z, axis=0)

  # update parameter w
  w = sum_z / data.shape[0]
  new_params["w"] = w

  # update parameters related to U
  mu = np.dot(z.T, U)
  for i in range(C):
    mu[i] = mu[i]/sum_z[i]
  sigma = np.zeros((U.shape[1], U.shape[1], C))
  for c in range(C):
    j = U - np.tile(mu[c], (U.shape[0], 1))
    s = mymult3(z[:, c], j, U)
    s = s / sum_z[c]
    sigma[:, :, c] = s
  new_params["mu"] = mu
  new_params["sigma"] = sigma

  # update parameters related to V
  if V is not None:
    forma = V.shape
    if len(forma) > 1:
         v = forma[1]
    else:
         v = 1
    lam = []
    for c in range(C):
      lam_c = []
      if v == 1:
        lam_c.append(mymult4(z[:, c], V) / sum_z[c])
      else:
        for j in range(v):
            lam_c.append(mymult4(z[:, c], V.iloc[:,j]) / sum_z[c])
      lam.append(lam_c)
    new_params["lam"] = lam


  # update parameters related to Y
  fitted_values = []
  fix_param = []
  groups = []
  interc = []
  knots_save = []
  hessiana = []

  fitted_cluster = np.zeros(len(data['y']))
  for i in range(len(data['y'])):
     fitted_cluster[i] = np.argmax(z[i])

  for c in range(C):
    # raggruppare le osservazioni rispetto ai gruppi
    data_c = data[fitted_cluster == c]
    y_c = list(data_c.groupby(group_name)['y'].apply(np.array).values)
    lengths_c = np.array(data_c.groupby(group_name).count().reset_index().iloc[:,1])
    num_group_c = len(data_c.groupby(group_name).count().reset_index()[group_name])
    data_fix = defaultdict(list)
    for i in range(num_fix):
      data_fix[i] = data_c.groupby(group_name)[name_fix[i]].apply(np.array).values.tolist()

    knots, par, W, hess_ran, hess_fix, others = algorithm_alpha(ran_var=False , ran_int=True,
                                                       n_fix=num_fix, sim=False,
                                                       tol=alpha, model=mod,
                                                       fix=data_fix, lengths=lengths_c,
                                                       y=y_c, N=num_group_c, t=None, data=data_c, 
                                                       name_fix=name_fix, name_output=['y'], name_group=group_name)

    fix_param.append(par)
    knots_save.append(knots)
    hessiana.append(hess_fix)

    #creo i gruppi
    group = np.zeros((num_group_c,1))
    for i in range(num_group_c):
      group[i] = int(np.argmax(W[i, :]))
    groups.append(group)

   #fitted values
    X = pd.DataFrame({'cluster': range(len(knots)), 'knots': knots})
    Y = pd.DataFrame({'Group': data_c.groupby(group_name).count().reset_index()[group_name], 'cluster': group[:,0]})
    Z = Y.merge(X, on=['cluster'])
    data_copy_c = data_c.copy()
    data_copy_c.loc[:, 'Group'] = data_copy_c.loc[:, group_name]
    data_copy_c = data_copy_c.merge(data_copy_c.merge(Z, how='left', on='Group', sort=False))
    interc.append(data_copy_c['knots'])

    if mod == 'B':
      value = data_copy_c['knots'] + np.dot(data_copy_c[name_fix], par)
      fitted_values.append(1 / (1 + np.exp(-value)))
    elif mod == 'P':
      value = data_copy_c['knots'] + np.dot(data_copy_c[name_fix], par)
      fitted_values.append(np.round(np.exp(value)))

  new_params["rand_inter"] = interc
  new_params["fix_param"] = fix_param
  new_params["groups"] = groups
  new_params["fitted_values"] = fitted_values
  new_params["z"] = z
  new_params["knots"] = knots_save
  new_params["hessian_fix"] = hessiana

  return new_params

def loglikelihood(knots, param_fixed, group, model, n_fix, fix, y, num_group):
        s = []  # s <- rep(0,N)
        # param_fixed = par
        # param_random = knots = c

        for i in range(num_group):

            if group[i]==group[i]:
              a = y[i]

              b = knots[int(group[i])]
              for k in range(n_fix):
                b = b + param_fixed[k] * fix[k][i]

              if model=='B':
                s.append(np.sum(a * b - np.log(1 + np.exp(b.astype(float) ) ) )) # HO CAMBIATO QUI: ho messo .astype(float)
              elif model=='P':
                s.append(np.sum(a * b - np.exp(b.astype(float)) - np.log(np.nan_to_num(factorial(a))) ))

        return np.sum(np.array(s))

def log_like(data, y, U, C, z, params, mod, group_name, name_fix, num_fix, y_name, V=None):
  # Carica i parametri dal dizionario 'params'
  w_old = params["w"]
  mu_old = params["mu"]
  sigma_old = params["sigma"]
  rand_inter_old = params["rand_inter"]
  fix_param_old = params["fix_param"]
  groups_old = params["groups"]
  fitted_values_old = params["fitted_values"]
  knots_old = params["knots"]

  if V is not None:
    lam_old = params["lam"]

  # likelihood for V
  multinom_Lik = np.zeros((len(y), C))
  if V is not None:
    forma = V.shape
    if len(forma) > 1:
         v = forma[1]
    else:
         v = 1
    for i in range(C):
         multinom_Lik[z[:,i]==1, i] = all_mydmultinom_log(V[z[:,i]==1], lam_old[i], v)

  # likelihood for U, V, D
  tot = 0
  for c in range(C):
    tot = tot + z[:, c] * (np.log(w_old[c]) +
                          multivariate_normal.logpdf(U, mean=mu_old[c], cov=sigma_old[:, :, c], allow_singular=True) +
                          multinom_Lik[:,c])

  # likelihood for SPGLMM
  lik_SPGLMM = 0
  fitted_cluster = np.zeros(len(data['y']))
  for i in range(len(data['y'])):
     fitted_cluster[i] = np.argmax(z[i])
  for c in range(C):
    data_c = data[fitted_cluster == c]
    y_c = list(data_c.groupby(group_name)['y'].apply(np.array).values)
    num_group_c = len(data_c.groupby(group_name).count().reset_index()[group_name])
    data_fix = defaultdict(list)
    for i in range(num_fix):
      data_fix[i] = data_c.groupby(group_name)[name_fix[i]].apply(np.array).values.tolist()

    lik_SPGLMM += loglikelihood(knots_old[c], fix_param_old[c], groups_old[c], mod, num_fix, data_fix, y_c, num_group_c)

  return np.sum(tot) + lik_SPGLMM

def Algo_full(data, y, C, U, num_fix, num_group, alpha, mod, num_obs_groups, group_name, name_fix, y_name, max_iter, perc_collasso, V=None):
    iter = 0
    params = initialize_params(data, y, U, C, num_fix, num_group, alpha, mod, num_obs_groups, group_name, name_fix,y_name, V)
    log_l = [0, log_like(data, y, U, C, params['z'], params, mod, group_name, name_fix, num_fix, y_name, V)]
    tol = 1
    loop = False
    z = params['z']

    while abs(log_l[-1] - log_l[-2]) > tol and iter<max_iter and loop == False:
        params_old = params
        z_old = z

        # E-step
        z = E_step(y, U, C, mod, params, V)

        # M-step
        params = M_step(data, y, U, C, z, params, num_fix, num_group, alpha, mod, num_obs_groups, group_name, name_fix,y_name, V)

        # Saving log-likelihood
        new_log_l = log_like(data, y, U, C, z, params, mod, group_name, name_fix, num_fix, y_name, V)
        log_l.append(new_log_l)

        iter += 1

        if (iter > 3 and abs(log_l[-1] - log_l[-3]) < tol and abs(log_l[-2] - log_l[-4]) < tol) :
          loop = True
        print("FINE ITERAZIONE", iter)

        fitted_cluster = np.zeros(len(y))
        for i in range(len(y)):
            fitted_cluster[i] = np.argmax(params['z'][i])
        for c in range(C):
            if len(fitted_cluster[fitted_cluster==c]) < perc_collasso*len(y):
                print("UN CLUSTER E' FORMATO DA MENO DI ", perc_collasso)
                return params, log_l, z, iter

    if loop == True:
        print("ALGORITMO ENTRATO NEL LOOP")
        if log_l[-1]>log_l[-2] :
          return params, log_l, z, iter
        else :
          return params_old, log_l, z_old, iter

    elif iter>=max_iter:
      print("RAGGIUNTO IL MASSIMO DI ITERAZIONI")
    else :
       print("ALGORITMO ARRIVATO A CONVERGENZA")


    return params, log_l, z, iter