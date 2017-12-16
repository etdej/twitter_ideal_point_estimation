import argparse
from os import getpid
import numpy as np
from numpy.random import uniform
from scipy.stats import norm, describe
import pandas as pd
import time
import multiprocessing
from queue import Empty

def parse_args():
    parser = argparse.ArgumentParser(description='Stage 2.')
    parser.add_argument('n_iters', type=int,
                        help='The number of iterations to run each chain')
    parser.add_argument('n_warmup', type=int,
                        help='The number of warmup iterations (takes from n_iters)')
    parser.add_argument('inital_user_ix', type=int,
                        help='The index of the first user to estimate')
    parser.add_argument('n_users', type=int,
                        help='The number of users to estimate parameters for')
    return parser.parse_args()

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def log_posterior_density(alpha, beta, gamma, theta, phi, mu_beta, sigma_beta, y):
    value = alpha + beta - gamma *(theta - phi)**2
    out = np.log(sigmoid(value)**y *(1 - sigmoid(value))**(1-y))
    dnorm = norm.logpdf(theta, 0, 1) + norm.logpdf(beta, mu_beta, sigma_beta)
    return np.sum(out + dnorm)

def metropolis(y, alpha_i, gamma_i, phi_i, mu_beta_i, sigma_beta_i, beta_init, theta_init, 
               iters=2000, delta=0.05, chains=2, n_warmup=1000, thin=1, verbose=False):

    np.seterr(all='ignore')
    
    n_params = len(alpha_i)
    assert(n_params == len(gamma_i))
    assert(n_params == len(phi_i))
    assert(n_params == len(mu_beta_i))
    assert(n_params == len(sigma_beta_i))
    
    samples = []
    for ix, chain in enumerate(range(chains)):
        samples_chain = []
        
        curr = [beta_init, theta_init[chain]]
        i = 0
        start = time.time()
        print_freq = 10000
        for iter in range(iters):
            if iter > 0 and iter%print_freq == 0:
                print('pid: {} | iter: {}->{} | time: {}'.format(getpid(),
                                                                iter-print_freq,
                                                                iter,
                                                                time.time() - start))
                start = time.time()
            # getting samples from iterations
            alpha = alpha_i[iter%n_params]
            gamma = gamma_i[iter%n_params]
            phi = phi_i[iter%n_params]
            mu_beta = mu_beta_i[iter%n_params]
            sigma_beta = sigma_beta_i[iter%n_params]
            
            # sampling candidate values
            cand = uniform(low= [c-delta for c in curr], high=[c+delta for c in curr])
            accept_prob = np.exp(log_posterior_density(alpha, cand[0], gamma, cand[1], phi, mu_beta, sigma_beta, y) -
                                 log_posterior_density(alpha, curr[0], gamma, curr[1], phi, mu_beta, sigma_beta, y))
            accept_prob = np.clip(accept_prob, a_min=None, a_max=1)
            if uniform() <= accept_prob:
                curr = cand
            
            if iter%thin == 0:
                samples_chain.append(curr)
                
        samples.append(samples_chain)
    return samples

def metropolis_worker(process_id, return_dict, **kwargs):
    samples = metropolis(**kwargs)
    return_dict[process_id] = samples

def main(n_iters, n_warmup, inital_user_ix, n_users):
    def estimation(indexes):
        kwargs = { 
            'alpha_i': alpha_i,
            'gamma_i': gamma_i,
            'phi_i': phi_i,
            'mu_beta_i': mu_beta_i,
            'sigma_beta_i': sigma_beta_i, 
            'iters': n_iters,
            'n_warmup': n_warmup
        }
        manager = multiprocessing.Manager()
        ix_out = 0
        n_parallel_jobs = 18
        beta = []
        theta = []
        while ix_out < len(indexes):
            return_dict = manager.dict()
            user_ixs = indexes[ix_out:ix_out+n_parallel_jobs]
            print("\tComputing {} parallel - 1st uid: {} | last uid: {}".format(n_parallel_jobs, user_ixs[0], user_ixs[-1]))
            ix_out += n_parallel_jobs
            jobs = []
            for i in user_ixs:
                kwargs['y'] = y[i, :]
                kwargs['beta_init'] = np.log(np.sum(y[i,:]))
                kwargs['theta_init'] = np.random.normal(0, 1, size=(2))
                p = multiprocessing.Process(
                    target=metropolis_worker,
                    args=[i, return_dict],
                    kwargs=kwargs
                )
                jobs.append(p)
                p.start()
            
            for job in jobs:
                job.join()

            sorted_results = sorted(return_dict.items())
            print("\tNum results: {}\n\t##########".format(len(sorted_results)))
            beta.extend([np.array(samples)[:, :, 0] for i, samples in sorted_results])
            theta.extend([np.array(samples)[:, :, 1] for i, samples in sorted_results])

        return beta, theta

    print("N_iters: {} | n_warmup: {} | initial_user: {} | n_users: {}".format(n_iters, n_warmup, inital_user_ix, n_users))

    data_dir = "us_results/subset_sigalpha/"
    #data_dir = "/scratch/dam740/1013/data/stage2/"

    samples_alpha = pd.read_csv(data_dir + 'samples_alpha.csv')
    samples_phi = pd.read_csv(data_dir + 'samples_phi.csv')
    samples_gamma = pd.read_csv(data_dir + 'samples_gamma.csv')
    samples_mu_beta = pd.read_csv(data_dir + 'samples_mu_beta.csv')
    samples_sigma_beta = pd.read_csv(data_dir + 'samples_sigma_beta.csv')

    fin = data_dir + "adj-matrix-US.csv"
    adj_matrix = pd.read_csv(fin, index_col=0)

    to_remove = ['pedropierluisi', 'EleanorNorton']
    for elite in to_remove:
      adj_matrix = adj_matrix.drop(elite, axis=1) if elite in adj_matrix else adj_matrix

    y = adj_matrix.as_matrix()
    alpha_i = samples_alpha.as_matrix()
    gamma_i = samples_gamma.as_matrix()
    phi_i = samples_phi.as_matrix()
    mu_beta_i = samples_mu_beta.as_matrix()
    sigma_beta_i = samples_sigma_beta.as_matrix()

    #removing elites for which we don't know the party
    to_remove = ['pedropierluisi', 'EleanorNorton']
    for elite in to_remove:
        adj_matrix = adj_matrix.drop(elite, axis=1) if elite in adj_matrix else adj_matrix

    start = time.time()
    beta, theta = estimation(range(inital_user_ix,inital_user_ix+n_users))
    print('Duration: {}'.format(time.time() - start))

    # for each user take avg between chains to get only 1 value per iteration
    beta_avg = np.mean(beta, axis=1)
    theta_avg = np.mean(theta, axis=1)
    index = adj_matrix.index[inital_user_ix:inital_user_ix+n_users]
    pd.DataFrame(beta_avg, index=index).to_csv('samples_beta_stage2.csv')
    pd.DataFrame(theta_avg, index=index).to_csv('samples_theta_stage2.csv')

if __name__ == '__main__':
    args = parse_args()
    main(**vars(args))
