import sqlite3

##
#Initializing a SQL database for storage
##
conn = sqlite3.connect('selfsquares.db')
#conn.row_factory = lambda cursor, row: row[0]
c = conn.cursor()

try:
    c.execute('''DROP TABLE selfsquares''')
except:
    pass
try:
    c.execute('''CREATE TABLE selfsquares
    (modulo int, selfsquare int)''')
except:
    pass


c.execute('''INSERT INTO selfsquares VALUES (2,1)''')
c.execute('''INSERT INTO selfsquares VALUES (3,1),(3,2)''')

conn.commit()
