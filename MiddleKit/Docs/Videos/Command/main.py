# Gain access to the Middle package
import os
import sys
sys.path.insert(1, os.path.abspath(os.pardir))

from datetime import date
from MiddleKit.Run.MySQLObjectStore import MySQLObjectStore
from Middle.Movie import Movie
from Middle.Person import Person
from Middle.Role import Role


def main():

    # Set up the store
    # store = MySQLObjectStore(user='user', passwd='password')
    store = MySQLObjectStore()
    store.readModelFileNamed('../Middle/Videos')

    movie = Movie()
    movie.setTitle('The Terminator')
    movie.setYear(1984)
    movie.setRating('r')
    store.addObject(movie)

    james = Person()
    james.setName('James Cameron')
    james.setBirthDate(date(1954, 8, 16))
    movie.addToDirectors(james)

    ahnuld = Person()
    ahnuld.setName('Arnold Schwarzenegger')
    ahnuld.setBirthDate(date(1947, 7, 30))
    store.addObject(ahnuld)

    terminator = Role()
    terminator.setKaracter('Terminator')
    terminator.setPerson(ahnuld)
    movie.addToCast(terminator)

    store.saveChanges()


if __name__ == '__main__':
    main()
