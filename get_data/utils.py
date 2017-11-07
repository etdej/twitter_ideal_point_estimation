import re
import time
import csv
import json
import datetime
import copy
import geopy
import geotext
import pycountry
import tweepy
import config

def is_same_country(country_iso_2_code, country_str):
    country = pycountry.countries.get(alpha_2=country_iso_2_code)
    country_dict = copy.deepcopy(vars(country)['_fields'])
    if 'numeric' in country_dict:
        del country_dict['numeric']
    possible_country_names = list(country_dict.values())

    patt = r'({}|{}|{}|{})'.format(*possible_country_names)
    return True if re.search(patt, country_str, flags=re.IGNORECASE) else False

def get_geography_data(location_in):
    '''
    location_in: str, name of place
    returns list of city, country and coordinates
    For example:
        ['New York', 'United States', (40.74, -73.98)]
    '''
    got_location = False
    geolocators = [
        geopy.geocoders.Nominatim(timeout=3),
        geopy.geocoders.ArcGIS(timeout=3),
        geopy.geocoders.GoogleV3(api_key=config.google_geolocation_api_key, timeout=3),
        geopy.geocoders.Bing(api_key=config.bing_geolocation_api_key)
    ]
    while not got_location:
        for i, geolocator in enumerate(geolocators):
            try:
                location = geolocator.geocode(location_in)
                got_location = True
                break
            except geopy.exc.GeocoderTimedOut as err:
                print("Geolocator {} timed out: {}".format(i, err))
            except (geopy.exc.GeocoderServiceError, geopy.exc.GeocoderQuotaExceeded) as err: 
                print("Geolocator {} exceeded API rate limit: {}".format(i, err))
            except geopy.exc.GeopyError as err:
                print("Geopy.geocoders error in geolocator {}: ".format(i,err))
                raise
        if not got_location:
            time.sleep(10)

    if not location:
        return ['', '', ('', '')]
        
    coords = (location.latitude, location.longitude)
    places = geotext.GeoText(location.address)
    city = places.cities[0] if len(places.cities) > 0 else ''
    country = places.countries[0] if len(places.countries) > 0 else ''
    if not country:
        split = location.address.split(', ')
        country = split[-1] if split else ''
    return [city, country, coords]

def remove_undesired_elite_fields(elite):
    '''
    elite: Tweepy User object
    returns python dictionary
    '''
    elite_dict = elite._json
    to_remove = set([
        'status',
        'description',
        'contributors_enabled',
        'entities',
        'follow_request_sent',
        'following',
        'geo_enabled',
        'is_translation_enabled',
        'is_translator',
        'notifications',
        'translator_type'
    ])
    x = copy.deepcopy(elite_dict)
    for k in elite_dict.keys():
        if k.find('profile') >= 0 or k in to_remove:
            del x[k]
    return x

def cursor_iterator(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.TweepError as err:
            print("Rate limit error iterating: {}".format(err))
            time.sleep(15 * 60 + 0.5)
        except Exception as err:
            print("Error iterating: {}".format(err))
            raise

def catch_exception_decorator(f):
    def wrapper(*args, **kwargs):
        while True:
            try:
                return f(*args, **kwargs)
            except tweepy.TweepError as err:
                print("Rate limit error in {}: {}".format(f.__name__, err))
                time.sleep(15 * 60 + 0.5)
            except Exception as err:
                print("Error in {}: {}".format(f.__name__, err))
                raise
    return wrapper

@catch_exception_decorator
def call_twitter_api(f, *args, **kwargs):
    return f(*args, **kwargs)

def is_active(user, twitter_api, months_ago_last_tweet):

    last_tweets = call_twitter_api(
        twitter_api.user_timeline,
        user_id=user.id,
        count=1,
    )

    if len(last_tweets) < 1:
        return False

    last_date_allowed = datetime.datetime.now() - datetime.timedelta(weeks=4*months_ago_last_tweet)

    last_tweet = last_tweets[0]
    return last_tweet.created_at > last_date_allowed

def write_csv(X, fname, fieldnames, mode='w'):
    '''
    X: iterable type where its elements are dicts
    '''
    if mode not in ['w', 'a']:
        raise ValueError("Incorrect mode: must be 'w' or 'a'.")

    with open(fname, mode, newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if mode == 'w':
            writer.writeheader()
        for k, val in X.items():
            writer.writerow(val)

def read_csv(fname, fieldnames=None):
    '''
    If fieldnames==None it assumes the first row of the file contains the header.
    Returns list of dicts. Each dict corresponds to one row of the file
    '''
    with open(fname, newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames)
        X = [row for row in reader]
    return X

def json_load(fname):
    with open(fname, 'r') as f_in:
        d = json.load(f_in)
    return d

def json_dump(X, fname, mode='w'):
    with open(fname, mode) as f_out:
        json.dump(X, f_out, indent=2)
