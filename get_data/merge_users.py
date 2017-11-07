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
    parser.add_argument('--user_min_following_elites', '-umfe', type=int,
                        default=3, dest='user_min_following_elites', required=False,
                        help="Minimum number of elite accounts a user must follow")
    return parser.parse_args()

def main(**kwargs):
    in_files = kwargs['in_files']
    f_out = kwargs['f_out']
    user_min_following_elites = kwargs['user_min_following_elites']

    users_dicts = [utils.json_load(fin) for fin in in_files]

    tmp_users_dict = users_dicts[0]
    for user_dict in users_dicts[1:]:
        for user_id, user in user_dict.items():
            if user_id in tmp_users_dict:
                tmp_users_dict[user_id]['elites'] += user['elites']
            else:
                tmp_users_dict[user_id] = user

    final_users_dict = {}
    for user_id, user in tmp_users_dict.items():
        if len(user['elites']) >= user_min_following_elites:
            final_users_dict[user_id] = user
            # store elites list as string separated by '|'
            final_users_dict[user_id]['elites'] = '|'.join(user['elites'])

    fields = list(list(final_users_dict.values())[0].keys())
    if len(final_users_dict) > 0:
        utils.write_csv(final_users_dict, f_out, fields)
    else:
        print("!!!! No users matched !!!!")
        
if __name__ == "__main__":
    args = parse_args()
    main(**vars(args))
    

