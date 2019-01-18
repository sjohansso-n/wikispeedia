"""
WIKISPEEDIA is a script for speedreading Wikipedia
articles. Takes a user provided keyword, downloads 
and parses the corresponding Wikipeedia article, 
and prints the words at a given speed.
"""

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
import socket
import time
import os
import re

timeout = 10
socket.setdefaulttimeout(timeout)
URL = 'https://en.wikipedia.org/wiki/'
ARTICLE_FILE = 'article.html'
DIRECTORY = 'titles/'

class Searcher():

	def __init__(self):
		self.directory = DIRECTORY

	def file_to_search_in(self, keyword):
		"""
		Returns the filename of the file to search in for 
		matches based on the keyword's first letter/symbol.
		"""
		if re.match('^[A-Za-z0-9_-]*$', keyword[0]):
			file = f'{ self.directory }{ keyword[0] }.txt'
		else: 
			file = f'{ self.directory }symbols.txt'
		return file

	def search_for_match(self, keyword):
		"""
		Searches for a keyword in a file of words, first with 
		unchanged casing, then all lower case. Returns True 
		when a match is found or False if there is no match.
		"""
		file = self.file_to_search_in(keyword)
		with open(file, 'r') as f:
			for word in f:
				if (keyword == word.strip() or 
					keyword.capitalize() == word.strip() or 
					keyword.title() == word.strip()):
					return True, word.strip()
		with open(file, 'r') as f:
			for word in f:
				if keyword.lower() == word.strip().lower():
					return True, word.strip()
		return False, keyword

	def search_for_startswith_matches(self, keyword):
		"""
		Searches in a file of words for words that starts with 
		a keyword. Returns a list of matches. If there is no 
		match it returns an empty list. Stops when 5 matches 
		has been found.
		"""
		file = self.file_to_search_in(keyword)
		with open(file, 'r') as f:
			startswith_matches = []
			for word in f:
				if word.strip().lower().startswith(keyword):
					startswith_matches.append(word.strip())
					if len(startswith_matches) == 5:
						break
		return startswith_matches

	def search_for_contains_matches(self, keyword):
		"""
		Searches in a file of words for words that contains 
		a keyword. Returns a list of matches. If there is no 
		match it returns an empty list. Stops when 5 matches 
		has been found.
		"""
		contains_matches = []
		for file in [f for f in os.listdir(self.directory) if f.endswith('.txt')]:
			with open(self.directory + file, 'r') as f:
				for word in f:
					if keyword in word.strip().lower():
						contains_matches.append(word.strip())
						if len(contains_matches) == 5:
							return contains_matches
		return contains_matches

class Downloader():

	def __init__(self, keyword):
		self.keyword = keyword.replace(' ', '_')
		self.article = ARTICLE_FILE
		self.searcher = Searcher()

	def keyword_match(self):
		"""
		Returns true if the keyword is in the dictionary, 
		else returns False.
		"""
		return self.searcher.search_for_match(self.keyword)

	def near_match(self):
		"""
		Prints a list of words that either startswith the keyword 
		or contains the keyword, if there are such matches.
		"""
		startswith_matches = self.searcher.search_for_startswith_matches(self.keyword)
		if len(startswith_matches) > 0:
			print(f"No matches found. Found similar matches: { startswith_matches }")
		else:
			contains_matches = self.searcher.search_for_contains_matches(self.keyword)
			if len(contains_matches) > 0:
				print(f"No matches found. Found similar matches: { contains_matches }")
			else:
				print("Didn't find any matches.")

	def get_url(self, url):
		"""
		Tries to open an url with a keyword. Saves html data to a 
		file if there is success and calls the function that prints 
		the text in the file.
		"""
		try:
			response = urlopen(Request(url))
			with open(self.article, 'wb') as f:
				f.write(response.read())
			return True
		except:
			print("Couldn't download data.")
			return False

class SpeedReader():

	def __init__(self, article):
		self.article = article

	def get_speed(self):
		"""
		Asks the user to provide a reading speed and how many 
		words there should be per line when reading.
		"""
		wpm, wpr = '', ''
		while wpm not in range(1, 2001) or wpr not in range(1,200):
			try:
				wpm = int(input('Enter words per minute:\n'))
				wpr = int(input('Enter words per row:\n'))
			except:
				pass
		return wpm, wpr

	def reading_info(self, wpm, wpr):
		"""
		Calculates the number of words in the document, how 
		many lines there will be when reading and how many 
		minutes the reading will take at the given speed.
		"""
		words = 0
		for line in self.gen_lines():
			words += sum(1 for word in line)
		return words, int(words/wpr), int(words/wpm)

	def gen_lines(self):
		"""
		Parses an html document and extracts the text. Each line in 
		the text is yeilded as a list of the words in the line.
		"""
		with open(self.article) as f:
			soup = BeautifulSoup(f, 'html.parser')
			unwanted = {'navbar': soup.find('table', {'class': 'vertical-navbox nowraplinks plainlist'}),
						'toc': soup.find(id='toc')}
			for line in soup.find_all(['p','ul']):
				if all(line not in value.descendants for key, value in unwanted.items() if value != None):
					try:
						if (line.next_sibling.next_element != soup.find(id="See_also") and
							line.next_sibling.next_element != soup.find(id="Notes") and
							line.next_sibling.next_element != soup.find(id="References") and
							line.next_sibling.next_element != soup.find(id="External_links") and
							line.next_sibling.next_element.next_element != soup.find(id="left-navigation")):
							yield line.text.split()
						else:
							break
					except:
						pass

	def read_text(self, line, wpm, wpr):
		"""
		Takes a list of words as input and and prints them 
		out in rows with the given length and speed.
		"""
		words_per_sec = float(wpm/60)
		sec_per_row = float(wpr/words_per_sec)

		while len(line) > 0:
			print(' '.join([word for word in line[:wpr]]))
			del(line[:wpr])
			time.sleep(sec_per_row)

def main():
	keyword = ''
	while len(keyword) == 0:
		keyword = input('What do you want to read about? ')
	
	data = Downloader(keyword)
	match, keyword = data.keyword_match()
	data.keyword = keyword
	if match and data.get_url(URL + keyword):
		print('Ready! Found match: {}'.format(keyword.replace('_',' ')))

		reader = SpeedReader(ARTICLE_FILE)
		wpm, wpr = reader.get_speed()
		print('Counting...')
		words, lines, minutes = reader.reading_info(wpm, wpr)

		print(f'Number of words in text: {words}')
		print(f'Number of lines: {lines}')
		print(f'Reading will take {minutes} minutes.')
		print('Starting in 5 seconds...')
		
		time.sleep(5)
		for line in reader.gen_lines():
			if len(line)>0:
				reader.read_text(line, wpm, wpr)
				print('\n')
	else:
		data.near_match()

if __name__ == '__main__':
	main()











