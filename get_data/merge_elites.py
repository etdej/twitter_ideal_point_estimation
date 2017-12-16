'''
Merge all the users that different twitter API accounts fetched into one single file.
Applies an additional filter on the users based on the number of elites they follow.
'''
import os
import json
import argparse
import tweepy

import config
import utils

def parse_args():
    parser = argparse.ArgumentParser(description='Get elites and users data.')
    parser.add_argument('in_files', type=str, nargs='+',
                        help='list of files that containt the fetched users')
    parser.add_argument('f_out', type=str,
                        help="CSV file to write final users data")
    return parser.parse_args()

def main(**kwargs):
    in_files = kwargs['in_files']
    f_out = kwargs['f_out']

    elites_dicts = {elite_dict['id_str']: elite_dict
                    for fin in in_files
                    for elite_dict in utils.read_csv(fin)}

    print("Total number of elites: ", len(elites_dicts))

    if len(elites_dicts) > 0:
        fields = list(list(elites_dicts.values())[0].keys())
        utils.write_csv(elites_dicts, f_out, fields)
    else:
        print("!!!! No users matched !!!!")
        
if __name__ == "__main__":
    args = parse_args()
    main(**vars(args))
    

