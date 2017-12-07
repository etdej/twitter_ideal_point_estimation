import sys
sys.path.insert(0, '../get_data/')

import os.path
import pandas as pd
import numpy as np
import pystan
import time
import utils

party_ideology = {
        'FI': -1,
        'FN': 1,
        'LR': 1,
        'PE': -1,
        'PS': -1,
        'REM': 0,
}

def make_adj_matrix(f_adj_matrix, data_dir):
    f_elites = data_dir + "fr_elites_data.csv"
    f_users = data_dir + "fr_users_data.csv"
    elites = pd.read_csv(f_elites, index_col=0)
    # todo might have index col
    users = pd.read_csv(f_users, index_col=0)
    adj_matrix = pd.DataFrame(index=users.index, 
                              columns=[name.lower() for name in elites['screen_name']],
                              data=np.zeros([users.shape[0], elites.shape[0]]),
                              dtype=int)
    
    for ix, user in users.iterrows():
        for elite_name in user['elites'].split('|'):
            adj_matrix.loc[ix, elite_name.lstrip('@').lower()] = 1
    adj_matrix.to_csv(f_adj_matrix)

    # make stage1 adj_matrix (less than 25k users)
    adj_matrix_stage1 = adj_matrix[adj_matrix.sum(axis=1) >= 5]
    f_adj_matrix_stage1 = "adj-matrix-FR-stage1.csv"
    adj_matrix_stage1.to_csv(f_adj_matrix_stage1)

def add_party(elites, data_dir, fout):
    f_party = data_dir + 'elites_FR_parties.json'
    parties = utils.json_load(f_party)
    while len(parties) != elites.shape[0]:
        parties.append(['None', 'None'])
    elites.loc[:, 'party'] = [party for _, party in parties]
    elites.to_csv(fout)
    return elites

def normalize(x):
        center = x - x.mean()
        return center/center.std()

def main():
    data_dir = "./"
    #data_dir = "/scratch/dam740/1013/data/stage1/fr"
    f_adj_matrix = data_dir + "adj-matrix-FR.csv"
    f_adj_matrix_stage1 = data_dir + "adj-matrix-FR-stage1.csv"
    if not os.path.isfile(f_adj_matrix):
        make_adj_matrix(f_adj_matrix, data_dir)

    adj_matrix = pd.read_csv(f_adj_matrix_stage1, index_col=0)
    #removing elites for which we don't know the party
    to_remove = ['pedropierluisi', 'EleanorNorton']
    for elite in to_remove:
        adj_matrix = adj_matrix.drop(elite, axis=1) if elite in adj_matrix else adj_matrix

    f_elites = data_dir + "fr_elites_data.csv"
    elites = pd.read_csv(f_elites)
    if 'party' not in elites.columns:
        elites = add_party(elites, data_dir, f_elites)
    elites = elites.loc[:, ['screen_name', 'party']]
    names = list(elites['screen_name'])
    party = list(elites['party'])
    fr_party = pd.DataFrame(np.array(party).reshape(1, len(party)), columns=names)
    y = adj_matrix

    J = adj_matrix.shape[0]
    K = adj_matrix.shape[1]
    stan_data = dict(
        J = J,
        K = K,
        N = J*K,
        jj = list(range(1, J+1))*K,
        kk = np.repeat(list(range(1, K+1)), J),
        y= y.as_matrix().flatten().tolist())

    fr_party = fr_party[y.columns]
    fr_party = fr_party.transpose()

    phi = np.array([party_ideology[party] if party in party_ideology else 0 for party in elites['party']])
    stan_model ="""
    data {
        int<lower=1> J; // number of twitter users
        int<lower=1> K; // number of elite twitter accounts
        int<lower=1> N; // N = J x K
        int<lower=1,upper=J> jj[N]; // twitter user for observation n
        int<lower=1,upper=K> kk[N]; // elite account for observation n
        int<lower=0,upper=1> y[N]; // dummy if user i follows elite j
    }
    parameters {
        vector[K] alpha;
        vector[K] phi;
        vector[J] theta;
        vector[J] beta;
        real mu_alpha;
        real mu_beta;
        real<lower=0.1> sigma_beta;
        real mu_phi;
        real<lower=0.1> sigma_phi;
        real gamma;
    }
    model {
        alpha ~ normal(mu_alpha, 1);
        beta ~ normal(mu_beta, sigma_beta);
        phi ~ normal(mu_phi, sigma_phi);
        theta ~ normal(0, 1); 
        for (n in 1:N)
            y[n] ~ bernoulli_logit( alpha[kk[n]] + beta[jj[n]] - 
                gamma * square( theta[jj[n]] - phi[kk[n]] ) );
    }"""

    stan_init = []
    n_chains = 1
    for i in range(n_chains):
        stan_init.append(dict(
            alpha = normalize(np.log(y.sum(axis=0) + 0.0001)),
            beta = normalize(np.log(y.sum(axis=1) + 0.0001)),
            mu_beta = 0,
            mu_alpha = 0,
            sigma_beta = 1,
            theta = np.random.normal(size=(J)),
            phi = phi,
            mu_phi = 0,
            sigma_phi = 1,
            gamma = np.random.normal()
        ))
    
    print("Init model...")
    start = time.time()
    sm = pystan.StanModel(model_code=stan_model)
    print("Duration: ", time.time() - start)

    print("Sampling...")
    start = time.time()
    samp = sm.sampling(data=stan_data,
                       init=stan_init,
                       iter=3,
                       thin=2,
                       warmup=1,
                       chains=n_chains)
    print("Duration: ", time.time() - start)

    la = samp.extract()  # return a dictionary of arrays

    for par in la:
        print(par)
        print(la[par].shape)
        fname = "fr_samples_{}.csv".format(par)
        columns = None
        if len(la[par].shape) <= 0:
            print("Skipping: empty...")
            continue
        if len(la[par].shape) < 2:
            pass
        elif la[par].shape[1]==y.shape[1]:
                columns = np.array(y.columns)
        elif la[par].shape[1]==y.shape[0]:
                columns = np.array(y.index)
        par_df = pd.DataFrame(la[par], columns=columns)
        par_df.to_csv(fname, index=False)

if __name__ == '__main__':
    main()
