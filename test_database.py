import sqlite3
import timeit

##
#Initializing a SQL database for storage
##

def check_current_n():
    conn = sqlite3.connect('selfsquares.db')
    #conn.row_factory = lambda cursor, row: row[0]
    c = conn.cursor()

    good = 0

    while not good:
        try:
            print("Trying...")
            print(c.execute("SELECT MAX(modulo) FROM selfsquares").fetchall())
            good = 1
        except Exception as e:
            print(e)
            pass
    return

def get_sums():
    conn = sqlite3.connect('selfsquares.db')
    #conn.row_factory = lambda cursor, row: row[0]
    c = conn.cursor()

    good = 0

    while not good:
        try:
            print("Trying...")
            print(c.execute("SELECT * FROM sums").fetchall())
            good = 1
        except Exception as e:
            print(e)
            pass
    return

    
def view_database():
    conn = sqlite3.connect('selfsquares.db')
    #conn.row_factory = lambda cursor, row: row[0]
    c = conn.cursor()

    good = 0

    while not good:
        try:
            print("Trying...")
            print(c.execute("SELECT * FROM selfsquares").fetchall())
            good = 1
        except Exception as e:
            print(e)
            pass
    return

#view_database()
check_current_n()
get_sums()
#print(timeit.timeit(stmt = 'check_current_n()', setup = 'from __main__ import check_current_n', number = 1))
#conn.commit()
