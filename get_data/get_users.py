import os
import json
import argparse
import tweepy

import config
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

    print("Starting...")

    auth = tweepy.OAuthHandler(
        config.twitter_api_accnts[twitter_accnt_num]['twitter_consumer_key'],
        config.twitter_api_accnts[twitter_accnt_num]['twitter_consumer_secret']
    )
    auth.set_access_token(
        config.twitter_api_accnts[twitter_accnt_num]['twitter_access_token'],
        config.twitter_api_accnts[twitter_accnt_num]['twitter_access_token_secret']
    )
    twitter_api = tweepy.API(auth)

    elites_handles_lst = utils.json_load(f_elites)
    users_dict = {}
    rejected_users = set()
    elites_dict = {}
    print("Starting loop over users...")
    for elite_name in elites_handles_lst:
        elite = utils.call_twitter_api(twitter_api.get_user, screen_name=elite_name)

        print("#### Elite: {} ####".format(elite_name))

        e_is_active = utils.is_active(elite, twitter_api, max_tweet_elite)

        if not e_is_active:
            print("\tSkipping " + elite_name + ": twitter account not active")
            continue
        elif elite.followers_count < min_followers_elite:
            print("\tSkipping " + elite_name + ": not enough followers on twitter")
            continue
        
        print("\tSaving " + elite_name + " ...")
        elite_dict = utils.remove_undesired_elite_fields(elite)
        elite_id = elite.id_str
        elites_dict[elite_id] = elite_dict

        cnt = 0
        for user in utils.cursor_iterator(tweepy.Cursor(twitter_api.followers, user_id=elite.id).items()):
            cnt += 1
            print("\t{} follower no {}: {}".format(elite.screen_name, cnt, user.id))
            
            if user.id_str in rejected_users:
                print("\t\tFollower " + user.id_str + " already rejected. Simply skipping...")
                continue
            elif user.id_str in users_dict:
                print("\t\tFollower " + user.id_str + " already saved. Simply adding this elite...")
                users_dict[user.id_str]['elites'].append(elite_name)
                continue
            elif user.followers_count < min_followers_user:
                print("\t\tSkipping follower " + user.id_str + ": not enough followers")
                rejected_users.add(user.id_str)
                continue
            elif not user.location:
                print("\t\tSkipping follower " + user.id_str + ": no location data")
                rejected_users.add(user.id_str)
                continue

            u_is_active = utils.is_active(user, twitter_api, max_tweet_user)
            if not u_is_active:
                print("\t\tSkipping follower " + user.id_str + ": twitter account not active")
                rejected_users.add(user.id_str)
                continue
            elif user.statuses_count < user_min_tweets:
                print("\t\tSkipping follower " + user.id_str + ": not enough tweets")
                rejected_users.add(user.id_str)
                continue

            location_data = utils.get_geography_data(user.location)
            belongs_to_country = utils.is_same_country(country_code, location_data[1])

            if not belongs_to_country:
                print("\t\tSkipping follower " + user.id_str + ": doesn't belong to target country")
                rejected_users.add(user.id_str)
                continue

            print("\t\tSaving follower " + user.id_str + " ...")
            users_dict[user.id_str] = {
                'id': user.id_str,
                'city': location_data[0],
                'country': location_data[1],
                'latitude': location_data[2][0],
                'longitude': location_data[2][1],
                'elites': [elite_name]
            }
        print("\tAnalyzed {} followers for elite {}".format(cnt, elite_name))

    if len(users_dict) > 0:
        utils.json_dump(users_dict, f_out_users)
    else:
        print("!!!! No users matched !!!!")

    if len(elites_dict) > 0:
        fields = list(list(elites_dict.values())[0].keys())
        utils.write_csv(elites_dict, f_out_elites, fields)
    else:
        print("!!!! No elites matched !!!!")
        
if __name__ == "__main__":
    args = parse_args()
    main(**vars(args))
    

