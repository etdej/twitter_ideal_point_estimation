import tweepy
import config

class twitter():
    def __init__(self):
        auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
        auth.set_access_token(config.access_token, config.access_token_secret)
        self.api = tweepy.API(auth)

    def get_user_id(self, user_name):
        user = self.api.get_user(user_name)
        return user.id

    def get_followers(self, id):
        followers = tweet.api.followers_ids(id)
        for follower in followers:
            print(follower)


    def get_tweets(self):
        public_tweets = self.api.home_timeline()
        for tweet in public_tweets:
          print(tweet.text)

    def save_edge(self, id, file):
        followers = tweet.api.followers_ids(id)
        for follower in followers:
            print(follower)
        return followers
            
if __name__ == "__main__":
    tweet = twitter()
    id = tweet.get_user_id("alannunnelee")
    print("id = "+str(id))
    print(len(tweet.api.followers_ids(id)))