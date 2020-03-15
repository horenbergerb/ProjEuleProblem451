import sqlite3

##
#Initializing a SQL database for storage
##

# conn = sqlite3.connect('selfsquares.db')
# #conn.row_factory = lambda cursor, row: row[0]
# c = conn.cursor()


# try:
#     c.execute('''DROP TABLE selfsquares''')
#     c.execute('''DROP TABLE sums''')
# except:
#     pass
# try:
#     c.execute('''CREATE TABLE selfsquares
#     (modulo int, selfsquare int)''')
#     c.execute('''CREATE TABLE sums (cursum BIGINT, maxn int, id INT PRIMARY KEY)''')
#     c.execute('''CREATE INDEX modulos ON selfsquares(modulo)''')
# except Exception as e:
#     print(e)
#     pass


# #c.execute('''INSERT INTO selfsquares VALUES (2,1)''')
# #c.execute('''INSERT INTO selfsquares VALUES (3,1),(3,2)''')

# conn.commit()
