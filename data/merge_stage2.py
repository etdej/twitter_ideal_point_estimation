import pandas as pd
import sys

def main():
    if len(sys.argv) < 2:
        print('Error: missing arguments in call')
        print("Usage: merge_stage2.py [us|fr] [data_dir")
        return
    
    f_beta = "samples_beta_stage2.csv"
    f_theta = "samples_theta_stage2.csv"

    if sys.argv[1] == 'fr':
        f_beta = 'fr_' + f_beta
        f_theta = 'fr_' + f_theta

    n = 2
    n_warmup = 10
    data_dir = sys.argv[2] if len(sys.argv) == 3 else ""
    d = data_dir + "run-0/"
    thetas = pd.read_csv(d+f_theta, index_col=0).iloc[:, n_warmup:].mean(axis=1)
    betas = pd.read_csv(d+f_beta, index_col=0).iloc[:, n_warmup:].mean(axis=1)
    for i in range(1,n):
        d = data_dir + "run-{}/".format(i)
        theta_i = pd.read_csv(d+f_theta, index_col=0).iloc[:, n_warmup:].mean(axis=1)
        beta_i = pd.read_csv(d+f_beta, index_col=0).iloc[:, n_warmup:].mean(axis=1)
        thetas = pd.concat([thetas, theta_i])
        betas = pd.concat([betas, beta_i])

    f_beta = "betas_final.csv"
    f_theta = "thetas_final.csv"
    thetas.to_csv(f_theta, header=['theta'])
    betas.to_csv(f_beta, header=['beta'])


if __name__ == '__main__':
    main()