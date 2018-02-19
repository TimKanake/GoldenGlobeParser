import re
import json
from bs4 import BeautifulSoup
from award import Award
import urllib2
import spacy
import time

start_time = time.time()
nlp = spacy.load('en')

presenters_regex = ['.* [Pp]resent.*']
awards_regex = ['.*[Aa]wards.*']



def get_superlative_winner_ec(tweets, re_list):
    matched_tweets = get_regex_matches(re_list, tweets)
    nominees =  getNomWin(matched_tweets, 'Actor')
    winner = nominees[0]
    nominees = nominees[1]

    return winner, nominees

def strip_puncutation(tweets):
    readable_tweets = []
    for tweet in tweets:
        text = tweet
        text = re.sub(r'[^\w\s]', '', text)
        readable_tweets.append(text)
    return readable_tweets

def load_json(filepath):
    return json.loads(open(filepath).read())

#Gives us unique tweets.
def convert_json_to_readable(json_file):
    readable_tweets = []
    for tweet in json_file:
        text = tweet.items()[0][1]
        readable_tweets.append(text)
    readable_tweets = list(set(readable_tweets))
    return readable_tweets

def regex_match(regex_list, string):
    for regex in regex_list:
        match = re.search(regex, string)
        if match:
            return True
    return False

def find_name(text):
    doc = nlp(text)
    names = []
    for ent in doc.ents:
        term = None
        if ent.label_ == 'PERSON':
            term = ent.text
            names.append(ent.text)
    return names

def scrape_award_names():
    url = 'https://www.goldenglobes.com/winners-nominees/2018'
    response = urllib2.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html,"html.parser")
    links = soup.findAll("li")
    award_names = []
    for link in links:
        if '/winners-nominees/2018/all#category-' in link.a.get('href'):
            award = Award(award_name = link.a.string)
            award_names.append(award)
    return award_names


def get_regex_matches(regex_list, tweets):
    matches = []
    for tweet in tweets:
        if not tweet in matches and regex_match(regex_list, tweet):
            matches.append(tweet)
    return matches

def find_most_likely_name(selected_tweets, stopwords):
    dict = {}
    for tweet in selected_tweets:
        if len(find_name(tweet)) > 2:
            names = find_name(tweet)
            for name in names:
                for name_word in name.split():
                    if name_word in stopwords:
                        break
                if not name in stopwords:
                    if dict.has_key(name):
                        dict[name] += 1
                    else:
                        dict[name] = 1
    for key in dict.keys():
        if '@' in key:
            dict[key] = 0
    if dict:
        return max(dict, key=dict.get)
    return None

def find_most_likely_names(selected_tweets, stopwords, number):
    dict = {}
    for tweet in selected_tweets:
        if len(find_name(tweet)) > 2:
            names = find_name(tweet)
            for name in names:
                for name_word in name.split():
                    if name_word in stopwords:
                        break
                if not name in stopwords:
                    if dict.has_key(name):
                        dict[name] += 1
                    else:
                        dict[name] = 1

    names = []
    while number > 0:
        if dict:
            name = max(dict, key=dict.get)
            names.append(name)
            dict.pop(name, None)
        number -= 1
    return names



def find_names(selected_tweets, stopwords):
    dict = {}
    for tweet in selected_tweets:
        if len(find_name(tweet)) > 0:
            names = find_name(tweet)
            for name in names:
                for name_word in name.split():
                    if name_word in stopwords:
                        break
                if not name in stopwords:
                    if dict.has_key(name):
                        dict[name] += 1
                    else:
                        dict[name] = 1
    unique_names = []
    for key in dict.keys():
        if not '@' in key:
            unique_names.append(key)
    return unique_names


def match_tweet_to_award(award_name, tweet, match_number):
    stopwords = ['Best', 'by', 'Award', 'an', 'in', 'a', 'or', 'any', ]
    count = 0

    if '-' in award_name:
        split_tweet = award_name.split('-')
        first_half = split_tweet[0].split()
        first_half = [word for word in first_half if word.lower() not in stopwords]
        second_half = split_tweet[1].split()
        second_half = [word for word in second_half if word.lower() not in stopwords]
        for word in first_half:
            if word in tweet.split():
                count += 1
                break
        for word in second_half:
            if word in tweet.split():
                count += 1
                break

        if count >= 2:
            return True


    else:
        first_half = tweet.split()
        first_half = [word for word in first_half if word.lower() not in stopwords]
        for word in first_half:
            if word in tweet.split():
                count += 1

        if count == 1:
            return True
    return False


def parse_gg(tweets, award_names):
    parsed_awards = award_names

    #The host is the same for every award in a given year.
    tweets = convert_json_to_readable(tweets)
    punctuation_stripped_tweets = strip_puncutation(tweets)

    stopwords = []

    for award in parsed_awards:
        award_tweets = []
        for tweet in punctuation_stripped_tweets:
            if match_tweet_to_award(award, tweet, 1):
                award_tweets.append(tweet)

        #Find Presenter for this award
        presenter_tweets = get_regex_matches(presenters_regex, award_tweets)

        presenters = find_most_likely_names(presenter_tweets, stopwords, 2)
        award.presenters = presenters
        print award
        print award.presenters

def print_parsed_info(parsed_info):
    for award in parsed_info:
        award.print_award()

def print_usage_statement():
    print "Run: Python gg_parser.py /path/to/file.json percent_of_tweets_analyzed_as_decimal_float"



