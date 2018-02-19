import re
import json
from bs4 import BeautifulSoup
import urllib2
import spacy
from difflib import SequenceMatcher
import operator
import sys
import time
start_time = time.time()

print 'loading spacy... '
nlp = spacy.load('en')
print 'finished loading spacy... '

presenters_regex = ['.* [Pp]resent.*']
awards_regex = ['.*[Aa]wards.*']



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

def find_name(text):
    doc = nlp(text)
    names = []
    for ent in doc.ents:
        term = None
        if ent.label_ == 'PERSON':
            term = ent.text
            names.append(ent.text)
    return names

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

def convert_json_to_readable(json_file):
	readable_tweets = []
	for tweet in json_file:
		text = tweet.items()[0][1]
		readable_tweets.append(text)
	readable_tweets = list(set(readable_tweets))
	return readable_tweets

def strip_puncutation(tweets):
    readable_tweets = []
    for tweet in tweets:
        text = tweet
        text = re.sub(r'[^\w\s]', '', text)
        readable_tweets.append(text)
    return readable_tweets

def get_similarity(a, b):
	return SequenceMatcher(None, a, b).ratio()

def check_for_similar(keys_list, val):
	for key in keys_list:
		if get_similarity(key.lower(), val.lower()) >= 0.6 or (val.lower() in key.lower() or key.lower() in val.lower()):
			if len(key) > 1 and len(val) > 1:
				return key
	return None

def check_for_similar2(keys_list, val):
	for key in keys_list:
		if get_similarity(key, val) >= 0.85:
			return key
	return None

def load(filepath):
	return json.loads(open(filepath).read())

def scrapeawards(year):
	url = 'https://www.goldenglobes.com/winners-nominees/' + year
	soup = BeautifulSoup(urllib2.urlopen(url).read(), "html.parser")
	links = soup.findAll("li")
	awards = []
	for link in links:
		if '/winners-nominees/' + year + '/all#category-' in link.a.get('href'):
			awards.append(link.a.string)
	return awards

def match(rex, data):
	matched = []
	for tweet in data:
		if re.match(rex, tweet['text']) != None and 'RT' != tweet['text'][:2]:
			matched.append(tweet)
	return matched

def issupper(a):
	if a.isupper():
		return True
	return False

def gethost(data):
	ideas = ['Host']
	search_term = reify(ideas[0])
	tweets = match(search_term, data)
	host_predictions = findname(tweets)
	if host_predictions[1][1]/float(host_predictions[0][1]) > .5:
		return host_predictions[0][0] + ' and ' + host_predictions[1][0]
	else:
		return host_predictions[0][0]

def findname2(ideas,data):
	hosts = {}
	for idea in ideas:
		rex = idea
		tweets = match(rex, data)
		for tweet in tweets:
			doc = nlp(tweet['text'])
			for ent in doc.ents:
				term = None
				if ent.label_ == 'PERSON':
					term = ent.text
				elif '@' == ent.text[0] or '#' == ent.text[0]:
					term = fix_hastag_at(ent.text)
				if term is not None:
					term = term.replace('.', '').replace('-', ' ')
				if term is not None and 'best' not in term.lower() and len(term) > 1 and 'gold' not in term.lower():
					if term in hosts.keys():
						hosts[term] += 1
					else:
						similar_key = check_for_similar(hosts.keys(), term)
						if similar_key is None:
							hosts[term] = 1
						else:
							hosts[similar_key] += 1
	sorted_hosts = sorted(hosts.items(), key=operator.itemgetter(1))
	sorted_hosts.reverse()
	try:
		return sorted_hosts
	except:
		return ''

def findname(tweets):
	candidates = {}
	for tweet in tweets:
		doc = nlp(tweet['text'])
		for ent in doc.ents:
			term = None
			if ent.label_ == 'PERSON':
				term = ent.text
			elif '@' == ent.text[0] or '#' == ent.text[0]:
				term = fix_hastag_at(ent.text)
			if term is not None:
				term = term.replace('.', '').replace('-', ' ')
			if term is not None and 'best' not in term.lower() and len(term) > 1 and 'gold' not in term.lower():
				if term in candidates.keys():
					candidates[term] += 1
				else:
					similar_key = check_for_similar(candidates.keys(), term)
					if similar_key is None:
						candidates[term] = 1
					else:
						candidates[similar_key] += 1
	candidates.pop('RT', None)
	sorted_candidates = sorted(candidates.items(), key=operator.itemgetter(1))
	sorted_candidates.reverse()
	try:
		if len(sorted_candidates) > 0:
			return sorted_candidates
		else:
			return 'No guesses found in find winner'
	except:
		return ''

def getawards():
	term = '.* [Nn]ominated [Ff]or a #?[Gg]olden ?[Gg]lobe [Ff]or .*'
	matched = match(term)
	rex = term
	for tweet in matched:
		tup = (tweet, re.split(rex[2:-2], tweet['text']))
		terms = tup[1][1].split()
		if len(terms) > 2:
			term = terms[0] + ' ' + terms[1] + ' ' + terms[2]
		elif len(terms) > 1:
			term = terms[0] + ' ' + terms[1]
		else:
			term = tup[1][1]
		terms = tup[1][0].split()
		if len(terms) > 2:
			winner = terms[-3] + ' ' + terms[-2] + ' ' + terms[-1]
		elif len(terms) > 1:
			winner = terms[-2] + ' ' + terms[-1]
		else:
			winner = tup[1][0]
		print winner, '         ', term

def stats(redata):
	print "Term, Quantity"
	for key in redata:
		print key, len(redata[key])

def splitdata(ideas, data):
	matchdic = {}
	for idea in ideas:
		if type(ideas) != type([]):
			prestring = ideas.get(idea)
		else:
			prestring = idea
		rex = reify(prestring)
		matchdic[idea] = match(rex, data)
	return matchdic

def fixawards(awards):
	newawards = {}
	for award in awards:
		newawards[award] = fixaward(award)
	return newawards

def fixaward(award):
	extrawords = [' Performance ', ' by ', ' an ', ' or ', ' for ', ' in ', ' a ', ' the ', ' made ', ' any ', ' By ', ' An ', ' Or ', ' For ', ' In ',
				  ' A ', ' The ', ' Made ', ' Any ', ' - ', ' Limited Series ']
	newaward = award.split(',')[0]
	# if ('Actor' in newaward or 'Actress' in newaward) and 'Television' not in newaward:
	# 	newaward = newaward.replace(' Motion Picture ', ' ').replace(' Motion Picture',' ')
	for extraword in extrawords:
		newaward = newaward.replace(extraword, ' ')
	while ' ' == newaward[-1]:
		newaward = newaward[:-1]
	while ' ' == newaward[0]:
		newaward = newaward[1:]
	return newaward

def reify(st):
	toreturn = ''
	if st[:2] != '.*':
		toreturn += '.*'
	thisspace = False
	lastspace = False
	for i, char in enumerate(st):
		if char == ' ':
			thisspace = True
		else:
			thisspace = False
		if lastspace or char.isupper():
			toreturn += '[' + char.upper() + char.lower() + ']'
		else:
			toreturn += char
		lastspace = thisspace
	if toreturn[-2:] != '.*':
		toreturn += '.*'
	toreturn = toreturn.replace(' ','.*')
	toreturn = toreturn.replace('[Mm]otion.*[Pp]icture', '(([Mm]otion.*[Pp]icture)|([Mm]ovie))')
	toreturn = toreturn.replace('[Tt]elevision', '(([Tt][Vv])|([Tt]elevision))')
	return toreturn

def find_winner2(tweets, award_name):
	stop_words = ['winner', 'winning', 'won', 'wins', '#goldenglobes',
				  '#goldenglobes2018', 'tv', 't.v', 'rt']
	temp_dict = {}
	# Put tweets into dictionary with count
	for t in tweets:
		if t['text'] in temp_dict.keys():
			temp_dict[t['text']] = temp_dict[t['text']] + 1
		else:
			similar_key = check_for_similar2(temp_dict.keys(), t['text'])
			if similar_key is None:
				temp_dict[t['text']] = 1
			else:
				temp_dict[similar_key] = temp_dict[similar_key] + 1

	# remove stop words
	award_words = award_name.lower().split()
	tweets_l = []
	tweets_count = []
	for k in temp_dict.keys():
		tweet_text = k
		tweet_text = tweet_text.split()
		tweet_text = [word for word in tweet_text if word.lower() not in stop_words
					  and 'https' not in word.lower() and word.lower() not in award_words
					  and 'golden' not in word.lower()]
		tweet_text = ' '.join(tweet_text)
		tweets_l.insert(len(tweets_l), tweet_text)
		tweets_count.insert(len(tweets_count), temp_dict[k])
	candidates = {}
	for i in range(0, len(tweets_l)):
		tweet_words = tweets_l[i].split()
		for j in range(0, len(tweet_words)):
			proposed_candidate = ''
			if tweet_words[j].isupper():
				while j < len(tweet_words) and tweet_words[j].isupper():
					proposed_candidate = proposed_candidate + ' ' + tweet_words[j]
					j += 1
			elif '@' == tweet_words[j][0] or '#' == tweet_words[j][0]:
				proposed_candidate = fix_hastag_at(tweet_words[j])
			proposed_candidate = proposed_candidate.strip()
			if proposed_candidate:
				proposed_candidate = proposed_candidate.replace('.','').replace('-', ' ')
				if proposed_candidate in candidates.keys():
					candidates[proposed_candidate] = candidates[proposed_candidate] + tweets_count[i]
				else:
					similar_key = check_for_similar(candidates.keys(), proposed_candidate)
					if similar_key is None:
						if len(proposed_candidate) > 1:
							candidates[proposed_candidate] = tweets_count[i]
					else:
						candidates[similar_key] = candidates[similar_key] + tweets_count[i]
	candidates.pop('RT', None)
	sorted_candidates = sorted(candidates.items(), key=operator.itemgetter(1))
	sorted_candidates.reverse()
	if len(sorted_candidates) > 0:
		return sorted_candidates
	else:
		return 'No guesses found! in find winner 2'

def fix_hastag_at(st):
	st = st.replace('#','').replace('@','').replace('-',' ').replace('_',' ')
	index = 0
	while index < len(st):
		if st[index].isupper():
			st = st[:index] + ' ' + st[index:]
			index += 2
		else:
			index += 1
	try:
		while ' ' == st[0]:
			st = st[1:]
	except:
		pass
	try:
		while ' ' == st[-1]:
			st = st[:-1]
	except:
		pass
	return st

def get_most_similar_award(tweet, awards):
	max_similarity = -sys.maxint-1
	similar_award = None
	for a in awards:
		temp_ratio = SequenceMatcher(None, a, tweet).ratio()
		if temp_ratio > max_similarity:
			max_similarity = temp_ratio
			similar_award = a
	return similar_award

def tweet_matches_idea(ideas, tweet):
	for idea in ideas:
		if re.match(idea, tweet['text'].lower()) != None:
			return True

def get_nominees(predictions):
	nominees = []
	nominees.append(predictions[0][0])
	for i in range(1, len(predictions)):
		if 'best' not in predictions[i][0].lower() and not check_for_similar2(nominees, predictions[i][0])\
				and 'gold' not in predictions[i][0].lower():
			nominees.append(predictions[i][0])

	return nominees

def findControversy(data):
	res = [".*[bB]ad.*", ".*[gG]ood.*", ".*!!!.*", ".*[hH]ate.*"]
	return findname2(res,data)[0][0]

def findBestDressed(data):
	res = [".*[lL]ooks.*", ".*[sS]exy.*", ".*[hH]andsome.*", ".*[bB]est.*[dD]ressed.*", ".*[dD]ress.*"]
	return findname2(res,data)[0][0]

def findRedCarpet(data):
	res = ['.*red.*carpet.*', '.*press.*conference.*']
	candidates = []
	predictions =  findname2(res, data)
	for i in range(1, len(predictions)):
		if 'best' not in predictions[i][0].lower() and not check_for_similar2(candidates, predictions[i][0])\
				and 'gold' not in predictions[i][0].lower():
			candidates.append(predictions[i][0])

	return candidates

def find_nametemp(text):
    doc = nlp(text)
    names = []
    for ent in doc.ents:
        term = None
        if ent.label_ == 'PERSON':
            term = ent.text
            names.append(ent.text)
    return names

def findnamepresenter(selected_tweets, stopwords):
	stopwords = stopwords.split()
	dict = {}
	for tweet in selected_tweets:
		if len(find_nametemp(tweet)) > 0:
			names = find_nametemp(tweet)
			for name in names:
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

def get_presenters(award_tweets, award):
	presenter_tweets = get_regex_matches(['.* present.*'], award_tweets)
	presenters = findnamepresenter(presenter_tweets,award)
	print presenters

def get_regex_matches(regex_list, tweets):
    matches = []
    for tweet in tweets:
        if not tweet in matches and regex_match(regex_list, tweet):
            matches.append(tweet)
    return matches

def regex_match(regex_list, string):
    for regex in regex_list:
        match = re.search(regex, string)
        if match:
            return True
    return False

def main():
	year = '2018'
	filepath = "gg2018.json"
	data = load(filepath)
	print '\n', 'Welcome to Golgen Globes', ' ', year, ' Predictions: ', '\n'
	print 'Awards hosted by: ', gethost(data), '\n'
	awards = scrapeawards(year)
	for award in awards:
		awards_tweets = match(reify(fixaward(award)), data)
		print '\n', award
		if 'Actor' in award or 'Actress' in award or 'Director' in award or 'Performance' in award or 'Cecil'\
				in award or 'Screenplay' in award:
			predictions = findname(awards_tweets)
		else:
			predictions = find_winner2(awards_tweets, award)
		nominees = get_nominees(predictions)
		if 'Cecil' in award:
			winner = predictions[1][0]
			print 'Winner: ', winner, '\n'
		else:
			winner = predictions[0][0]
			print 'Winner: ', winner
			print 'Nominees: ', nominees[:5], '\n'

	print 'Elapsed time fulfilling base requirements: ', time.time() - start_time, ' seconds.'
	temp_time = time.time()
	print 'Most Controversial: ', findControversy(data), '\n'
	print 'Best Dressed: ', findBestDressed(data), '\n'
	print 'List of People on the Red Carpet', findRedCarpet(data), '\n'
	print 'Elapsed time fulfilling extra credit: ' , time.time()-temp_time , ' seconds.'
	temp_time = time.time()
	print 'getting presenters...', '\n'
	parse_gg(data, awards)

	print 'Elapsed time getting presenters: ', time.time() - temp_time, ' seconds.'
	print 'Total time taken is: ', time.time() - start_time

main()
