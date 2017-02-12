#!/usr/bin/python3

from configparser import SafeConfigParser
from datetime import datetime, timedelta
import feedparser
import re
from time import mktime
import webbrowser

from imdbpie import Imdb


def main():
    # vars
    daysCheckBack = 1

    # Run it
    movieFeed = get_feed_from_config('config.ini')
    listOfTorrents = parse_feed(movieFeed, daysCheckBack)
    # print (imdb_rating('Hitchcock/Truffaut', 2014))  # for testing
    find_movies_above_rating(listOfTorrents)


def find_movies_above_rating(listOfTorrents, minRating=7.5):
    interestingMovies = []
    checkList = {}
    for torrent in listOfTorrents:
        mov = MovieTorrent(torrent['torrName'], torrent['downLink'],
                           torrent['pageUrl'])
        if not mov.is_hi_def():
            continue
        title, year = mov.title_year_from_name()
        if not title:
            continue
        if title in checkList:  # don't check the same movie twice
            rating = checkList.get(title)
        else:
            rating = imdb_rating(title, year)
        checkList[title] = rating
        if rating >= minRating:
            print ('The movie %s in this torrent: %s' %
                   (title, torrent['torrName']))
            print ("Has a rating of %s" % rating)
            interestingMovies.append((torrent['torrName'], rating))
            # mov.open_url_in_browser()
    print (interestingMovies)


def get_feed_from_config(configFile):
    config = SafeConfigParser()
    config.read(configFile)
    feed = config.get('Feeds', 'mtvFeed')
    return feed


def imdb_rating(movieTitle, year=None):
    imdb = Imdb()
    try:
        results = imdb.search_for_title(movieTitle)
    except:
        print ('WARNING: Could not find the title %s' % movieTitle)
        return 0.00
    if year is None:
        bestHit = results[0]
    else:
        gotHit = False
        for result in results:
            movieYear = int(result.get('year'))
            if movieYear - 2 <= year and movieYear + 2 >= year:
                bestHit = result
                gotHit = True
                break
        if not gotHit:
            print ('WARNING: Could not get match for %s' % movieTitle)
            return 0.00
    print ('-=MATCH=- %s --from %s  --=--  %s' % (movieTitle, year, bestHit))
    idBestHit = bestHit.get('imdb_id')
    rating = imdb.get_title_by_id(idBestHit).rating
    movType = imdb.get_title_by_id(idBestHit).type
    if movType.lower() != 'feature' and movType.lower() != 'documentary':
        print ('WARNING: This is not a feature-film or docu: %s' % movieTitle)
        return 0.00
    elif rating is None:
        print ('WARNING: Could not get rating from title %s' %
               bestHit.get('title'))
        return 0.00
    return float(rating)


def between_years(year, minYear=1905, maxYear='current'):
    if maxYear == 'current':
        now = datetime.now()
        maxYear = now.year
    if year >= minYear and year <= maxYear:
        return True
    else:
        return False


def parse_feed(feedToParse, daysCheckBack=30):
    feed = feedparser.parse(feedToParse)
    output = []
    for item in feed["items"]:
        foundItems = {}
        try:
            item.title
        except:
            continue
        # print ('\n %s \n' % item)
        dtObj = datetime.fromtimestamp(mktime(item.published_parsed))
        if dtObj > datetime.now() - timedelta(days=daysCheckBack):
            foundItems['torrName'] = item.title
            foundItems['downLink'] = item.link
            foundItems['pageUrl'] = item.comments
            output.append(foundItems)
    return output


class MovieTorrent:

    def __init__(self, torrName, downLink, pageUrl):
        self.torrName = torrName
        self.downLink = downLink
        self.pageUrl = pageUrl

    def open_url_in_browser(self):
        webbrowser.open(self.downLink)

    def is_hi_def(self):
        hd = ['720', '1080']
        for hdTerm in hd:
            if hdTerm in self.torrName:
                return True
        return False

    def title_year_from_name(self):
        """Assumes that the torrent-name always contains the movie-year
        and title. Can deal with movies whose names is or starts with a year.
        But not if they have a year within the name ("A space oddyssey 2001"
        does not work, whereas "2001 A space oddyssey" does.)
        """
        splitByFourDigits = re.split(r'(\d\d\d\d)', self.torrName)
        # moviename presumably comes first
        if len(splitByFourDigits) <= 1:  # No year in torrName
            print ('WARNING: Unable to extract year from %s' % self.torrName)
            return None, None
        for index, elem in enumerate(splitByFourDigits):
            if elem != '':  # if title does not start with 4 digits
                title = elem
                positionTitle = index
                break
        for index, elem in enumerate(splitByFourDigits):
            if index <= positionTitle:
                continue
            if re.match(r'([1-2][0-9]{3})', elem):
                year = int(elem)
                if between_years(year):
                    break
            elif index == positionTitle + 1:
                finalTitle = title + elem
            # print (index, elem)
        if not between_years(year):
            print ('WARNING: Unable to extract year from %s' % self.torrName)
            return None, None
        finalTitle = finalTitle.replace('.', ' ').strip()
        # print (finalTitle, '---YEAR %s' % year)
        return finalTitle, year


if __name__ == '__main__':
    main()
