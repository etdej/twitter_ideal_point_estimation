import os
import json
import argparse
import utils

def parse_args():
    parser = argparse.ArgumentParser(description='Get elites and users data.')
    parser.add_argument('twitter_accnt_num', type=int,
                        help='The 0-based index in config.py of the twitter API account to use')
    parser.add_argument('country_code', type=str,
                        help='ISO alpha-2 country code for country of interest')
    parser.add_argument('f_elites', type=str,
                        help="JSON file that contains list of screen names of elites' accounts")
    parser.add_argument('f_out_elites', type=str,
                        help="CSV file to write final elites data")
    parser.add_argument('f_out_users', type=str,
                        help="JSON file to write final users data")
    parser.add_argument('--max_months_last_tweet_elite', '-mte', type=int,
                        default=3, dest='max_tweet_elite', required=False,
                        help="Maximum number of months since last tweet for elites, else account considered inactive")
    parser.add_argument('--max_months_last_tweet_user', '-mtu', type=int,
                        default=6, dest='max_tweet_user', required=False,
                        help="Maximum number of months since last tweet for users, else account considered inactive")
    parser.add_argument('--min_followers_elite', '-mfe', type=int, required=False,
                        default=5000, dest='min_followers_elite',
                        help="Minimum number of followers for a elite")
    parser.add_argument('--min_followers_user', '-mfu', type=int,
                        default=25, dest='min_followers_user', required=False,
                        help="Minimum number of followers for a user")
    parser.add_argument('--user_min_tweets', '-umt', type=int,
                        default=100, dest='user_min_tweets', required=False,
                        help="Minimum number of tweets a user must have made")
    return parser.parse_args()
    
def main(
    twitter_accnt_num,
    country_code, 
    f_elites,
    f_out_elites,
    f_out_users,
    max_tweet_elite,
    max_tweet_user,
    min_followers_elite,
    min_followers_user,
    user_min_tweets):
    

    def process_user(user_dict, users_dict, rejected_users, elite, tweepy_api):
        '''
        updates users_dict or rejected_users
        '''
        uid = user_dict['id_str']

        if uid in rejected_users:
            print("\t\tFollower " + uid + " already rejected. Simply skipping...")
            return
            
        elif uid in users_dict:
            print("\t\tFollower " + uid + " already saved. Simply adding this elite...")
            users_dict[uid]['elites'].append(elite)
            return
            
        elif user_dict['followers_count'] < min_followers_user:
            print("\t\tSkipping follower " + uid + ": not enough followers")
            rejected_users.add(uid)
            return
            
        elif not user_dict['location']:
            print("\t\tSkipping follower " + uid + ": no location data")
            rejected_users.add(uid)
            return
            
        elif user_dict['statuses_count'] < user_min_tweets:
            print("\t\tSkipping follower " + uid + ": not enough tweets")
            rejected_users.add(uid)
            return

        u_is_active = utils.is_active(user_dict, tweepy_api, max_tweet_user)
        if not u_is_active:
            print("\t\tSkipping follower " + uid + ": twitter account not active")
            rejected_users.add(uid)
            return
            
        location_data = utils.get_geography_data(user_dict['location'])
        belongs_to_country = utils.is_same_country(country_code, location_data[1])

        if not belongs_to_country:
            print("\t\tSkipping follower " + uid + ": doesn't belong to target country")
            rejected_users.add(uid)
            return
            
        print("\t\tSaving follower " + uid + " ...")
        users_dict[uid] = {
            'id': uid,
            'city': location_data[0],
            'country': location_data[1],
            'latitude': location_data[2][0],
            'longitude': location_data[2][1],
            'elites': [elite]
        }

    print("Starting...")

    tweepy_api = utils.get_tweepy_api(twitter_accnt_num)
    raw_auth = utils.get_raw_twitter_auth(twitter_accnt_num)

    elites_handles_lst = utils.json_load(f_elites)
    users_dict = {}
    rejected_users = set()
    elites_dict = {}

    for elite_name in elites_handles_lst:
        elite = utils.tweepy_api_call(tweepy_api.get_user, screen_name=elite_name)
        if not elite:
            print("\tSkipping " + elite_name + ": user name not found")
            continue
    
        print("#### Elite: {} ####".format(elite_name))

        if elite.followers_count < min_followers_elite:
            print("\tSkipping " + elite_name + ": not enough followers on twitter")
            continue

        e_is_active = utils.is_active(elite._json, tweepy_api, max_tweet_elite)
        if not e_is_active:
            print("\tSkipping " + elite_name + ": twitter account not active")
            continue
        
        print("\tSaving " + elite_name + " ...")
        elite_dict = utils.remove_undesired_elite_fields(elite)
        elite_id = elite.id_str
        elites_dict[elite_id] = elite_dict

        get_ids_params = {
            'user_id': elite.id_str,
            'stringify_ids': 'true',
        }

        cursor = -1
        not_done = True
        users_lst = []
        cnt=0
        while not_done:
            get_ids_params['cursor'] = cursor
            resp = utils.twitter_api_call(utils.FOLLOWERS_IDS_URL, raw_auth, get_ids_params)
            if 'errors' in resp:
                err_code = resp['errors'][0]['code'] 
                if err_code == utils.NO_MORE_RESULTS:
                    print('\tDone. No more follower ids.')
                    not_done = False

                elif err_code == utils.RATE_LIMIT_CODE:
                    print('\tRate limit reached for GET followers ids.')
                    
                    if len(users_lst) > 0:
                        print('\tProcessing users...')
                        for user in users_lst:
                            process_user(user, users_dict, rejected_users, elite_name, tweepy_api)
                        cnt+=len(users_lst)
                        users_lst = []
                    else:
                        print('\tSleeping...')
                        time.sleep(15*60+0.1)
                else:
                    print("\t(Exiting) Other error occurred: ", resp['errors'])
                    return
                continue
            cursor = resp['next_cursor']
            i = 0
            while i<5000:
                ids = resp['ids'][i:i+100]
                params = {
                    'user_id': ','.join(ids)
                }
                users = utils.twitter_api_call(utils.USERS_URL, raw_auth, params, method='post')
                if 'errors' in users:
                    err_code = users['errors'][0]['code'] 
                    if err_code == utils.NO_MORE_RESULTS:
                        print('\tDone. No more ids.')
                        not_done = False
                        break
                    elif err_code == utils.RATE_LIMIT_CODE:
                        print('\tRate limit reached for GET users')
                        
                        if len(users_lst) > 0:
                            print("\tProcessing users....")
                            for user in users_lst:
                                process_user(user, users_dict, rejected_users, elite_name, tweepy_api)
                            users_lst = []
                        else:
                            print('\tSleeping...')
                            time.sleep(15*60+0.1)
                    else:
                        print("\t(Exiting) Other error occurred: ", users['errors'])
                        return
                        
                else:
                    users_lst += users
                    i+=100

        if len(users_lst) > 0:
            cnt+=len(users_lst)
            print("\tProcessing users....")
            for user in users_lst:
                process_user(user, users_dict, rejected_users, elite_name, tweepy_api)
            users_lst = []

        print("\tAnalysed {} followers for {}".format(cnt, elite_name))

    if len(users_dict) > 0:
        print("Saving user data...")
        utils.json_dump(users_dict, f_out_users)
    else:
        print("!!!! No users matched !!!!")

    if len(elites_dict) > 0:
        print("Saving entity data...")
        fields = list(list(elites_dict.values())[0].keys())
        utils.write_csv(elites_dict, f_out_elites, fields)
    else:
        print("!!!! No elites matched !!!!")
    
    print("We are done here!")

if __name__ == "__main__":
    args = parse_args()
    main(**vars(args))
    

