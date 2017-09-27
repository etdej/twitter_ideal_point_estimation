import tweepy
import config

class twitter():
    def __init__(self):
        print(config.consumer_key)
        auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
        auth.set_access_token(config.access_token, config.access_token_secret)
        self.api = tweepy.API(auth)

    def get_followers(self):
        return

    def get_tweets(self):
        public_tweets = self.api.home_timeline()
        for tweet in public_tweets:
          print(tweet.text)

if __name__ == "__main__":
    tweet = twitter()
    tweet.get_tweets()