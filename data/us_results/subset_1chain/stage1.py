import pandas as pd
import numpy as np
import pystan
import time

def normalize(x):
    center = x - x.mean()
    return center/center.std()

def main():
    #data_dir = "./"
    data_dir = "/scratch/dam740/1013/data/stage1/"
    #fin = data_dir + "adj-matrix-US.csv"
    #fin = data_dir + "adj-matrix-subset-us.csv"
    fin = data_dir + "adj-matrix-US-stage1-small.csv"
    adj_matrix = pd.read_csv(fin, index_col=0)
    #removing elites for which we don't know the party
    to_remove = ['pedropierluisi', 'EleanorNorton']
    for elite in to_remove:
      adj_matrix = adj_matrix.drop(elite, axis=1) if elite in adj_matrix else adj_matrix

    us_elites = pd.read_csv(data_dir + "elitesUS.csv", usecols=["US.screen_name", "US.party"])
    names = list(us_elites['US.screen_name'])
    party = list(us_elites['US.party'])
    us_party = pd.DataFrame(np.array(party).reshape(1, len(party)), columns=names)

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

    us_party = us_party[y.columns]
    us_party = us_party.transpose()

    phi = np.zeros(us_party.shape[0])
    phi[us_party[0] == 'D'] = -1
    phi[us_party[0] == 'R'] = 1

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
      real mu_beta;
      real<lower=0.1> sigma_beta;
      real mu_phi;
      real<lower=0.1> sigma_phi;
      real gamma;
    }
    model {
      alpha ~ normal(0, 1);
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
                       iter=150,
                       thin=2,
                       warmup=75,
                       chains=n_chains)
    print("Duration: ", time.time() - start)

    la = samp.extract()  # return a dictionary of arrays

    for par in la:
      print(par)
      print(la[par].shape)
      fname = "samples_{}.csv".format(par)
      columns = None
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
