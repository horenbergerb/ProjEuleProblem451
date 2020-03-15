from sympy import sieve
import sympy as sp
import sys
import multiprocessing
from multiprocessing import Lock
from math import sqrt
import sqlite3
import time
from functools import lru_cache
import cProfile

#used for convenient querying later on
get_squares = '''SELECT selfsquare FROM selfsquares WHERE modulo IN ({})'''
check_exists = '''SELECT modulo FROM selfsquares WHERE modulo IN ({}) LIMIT 1'''

####
#Overview
####
#The goal here is to leverage previous solutions when finding the next solution
#It uses the theory of finite abelian groups
#Which is basically just fancy chinese remainder theorem

#Note: this function is made for multiprocessing
#It assumes it is being passed shared variables and only searches a subset of n values up to max_n
#The subset is determined by interval and offset


###
#Initializing a SQL database for storage of self squares and run history
###
conn = sqlite3.connect('selfsquares.db')
c = conn.cursor()
try:
    #this table contains all the self-squares for each n-value
    c.execute('''CREATE TABLE selfsquares
    (modulo int, selfsquare int)''')
    c.execute('''INSERT INTO selfsquares VALUES (2,1)''')
    c.execute('''INSERT INTO selfsquares VALUES (3,1),(3,2)''')

    #creating an index to speed up recall
    c.execute('''CREATE INDEX modulos ON selfsquares(modulo)''')
    
    #this table contains the summation information of historical runs
    #historical runs are distinguished by rowid
    #not sure i also need the primary key here; i don't use it
    c.execute('''CREATE TABLE sums (cursum BIGINT, maxn int, id INT PRIMARY KEY)''')

    conn.commit()

    
except:
    pass


###
#Helper functions for accessing database information
#lots of weird hacks here
###


#grabs self-square data from our database
#lru_cache saves the most common requests to reduce sql searching
@lru_cache(maxsize=50000)
def pull_data(value):
    global conn
    global c
    good = False
    data = []
    while not good:
        try:
            data = c.execute(get_squares.format(value)).fetchall()
            good = True
        except Exception as e:
            print(e)
            pass
    return data

#updates the database with new self-squares
#takes a list of many [modulus, self-square] lists
def push_commits(commits, existence):
    global conn
    global c
    good = False
    while not good:
        try:
            #parsing all of our data into a sql string
            new_commits = ""
            for cur_commit in commits:
                new_commits += '('+str(cur_commit[0])+','+ str(cur_commit[1]) +'),'
            new_commits = new_commits[:-1]
            c.execute('''INSERT INTO selfsquares VALUES {}'''.format(new_commits))
            conn.commit()
            for cur_commit in commits:
                existence[cur_commit[0]] = 1
            commits = []
            good = True
        except Exception as e:
            print(e)
            pass

    return commits


#####
#the actual solver
#this guy finds our results and
#uses the helper functions above to save and retrieve data
#this block is equal parts math theory and data shenanigans
#####

def inductive_solver(max_n, primes, waiting, run_id, existence, interval, offset):

    #######
    #profiling to track efficiency
    #uncomment this and code at bottom of function
    #######
    #pr = cProfile.Profile()
    #pr.enable()
    
    global conn
    global c
    
    #holds self-square data to commit to sql
    commits = []
    
    #preparing our database
    global conn
    conn = sqlite3.connect('selfsquares.db')
    conn.row_factory = lambda cursor, row: row[0]
    global c
    c = conn.cursor()
    
    #tracking the sum which will be added to the total at the end
    local_sum = 0

    #x is our n value
    x = 0

    #finding our last completed solution in the database to avoid redundancy
    good = 0
    while not good:
        try:
            start_x = c.execute('''SELECT MAX(modulo) from selfsquares WHERE modulo%{} = {}'''.format(interval, offset)).fetchall()
            if start_x[0] != None:
                x = start_x[0]+interval
            good = 1
        except:
            pass

    #handling base case modulos, i.e. n < 4
    #4 is a somewhat arbitrary number
    #this is also where we set up offset counting for each of the multiprocesses
    if x == 0:
        start_val = 0
        while(start_val*interval + offset < 4):
            if start_val*interval + offset > 2:
                local_sum += 1
            start_val+=1
        
        x = start_val*interval + offset

    ##
    #Beginning the loop through n values
    ##
    
    #looping through all values of n
    while x < max_n + 1:
        
        #occasionally update sql database with our current solns
        #offset is also the process identifier in the set of waiting flags
        if len(commits) > 10000 or (waiting[offset] == 1 and len(commits) > 0):
            commits = push_commits(commits, existence)
        
        #finding the smallest prime divisor
        smallest_prime = x

        upper_bound = int(sqrt(x))+1
        for cur_prime in primes:
            if cur_prime > upper_bound:
                break
            if x%cur_prime == 0:
                smallest_prime = cur_prime
                break

        #getting the power of the smallest prime divisor
        smallest_prime_power = smallest_prime
        while (x//smallest_prime_power)%smallest_prime == 0:
            smallest_prime_power *= smallest_prime

        #handling edge cases where our n is a prime power or a power of 2
        #if n is prime power, solns are x-1 or 1
        if smallest_prime_power == x:
            if smallest_prime != 2:
                commits.append([x,x-1])
                commits.append([x,1])
                local_sum += 1
                x += interval
                continue
            #if it's a power of two, we just brute force it by checking every possible number for self-squareness
            #powers of two are weird
            #we probably don't have to do this, but whatever
            else:
                max_val = 1
                commits.append([x,x-1])
                commits.append([x,1])
                for cur_val in range(int(sqrt(x)),int((x/2))+1):
                    if (cur_val**2)%x == 1:
                        if (-cur_val)%x > max_val:
                            max_val = (-cur_val)%x
                        commits.append([x, cur_val])
                        commits.append([x, (-cur_val)%x])
                local_sum += max_val
                x += interval
                continue

        #so now we have some p^s and this is k. we should technically already have solutions for these
        k = x//smallest_prime_power

        #we have to wait until k, p^n are in our database. other processes might not have done them yet
        #this ugly chunk of code is making sure we have the k, p^n values we need
        good = False
        prime_power_self_squares = []
        k_self_squares = []
            
        while not existence[smallest_prime_power] == 1:
            #telling the responsible process to hurry up
            waiting[smallest_prime_power%interval] = 1
            #watching in case someone is telling us to hurry up
            if waiting[offset] == 1 and len(commits) > 0:
                commits = push_commits(commits, existence)
        while not existence[k] == 1:
            waiting[k%interval] = 1
            if waiting[offset] == 1 and len(commits) > 0:
                commits = push_commits(commits, existence)

        #we're no longer waiting, update flags
        waiting[smallest_prime_power%interval] = 0
        waiting[k%interval] = 0

        #grab the data we need
        k_self_squares = pull_data(k)
        prime_power_self_squares = pull_data(smallest_prime_power)
            
        #recall our desired number must satisfy a^2 = 1 mod kp^s
        #where kp^s = n
        #thus it satisfies a^2=1 mod p^s
        #and it satifies a^2=1 mod k
        #so our solution must be modularly equivalent to previous solutions for mod p^s and mod k

        #now we're just leveraging chinese remainder theorem
        #we do crt on every pair of solutions from p^s and k
        
        max_val = 1
        gcd = sp.gcdex(smallest_prime_power,k)
        for a in prime_power_self_squares:
            for b in k_self_squares:
                #this is the crt part. note the use of extended euclidean algorithm
                next_sol = ((gcd[0]*smallest_prime_power*(b)) + (gcd[1]*k*(a)))%x
                commits.append([x, next_sol])
                if next_sol > max_val and next_sol < x-1:
                    max_val = next_sol
                    
        local_sum += max_val
        
        #continuing on this process's share of the n values
        x += interval

    ######
    #cleanup code; submitting remaining data
    ######
    
    #push any remaining self-squares that have not been updated
    if len(commits) > 0:
        commits = push_commits(commits, existence)

    #update the total sum for this run with our local count
    good = False
    while not good:
        try:
            c.execute('''UPDATE sums SET cursum = cursum + {} WHERE rowid = {}'''.format(local_sum, run_id))
            conn.commit()
            good = True
        except:
            pass


    #######
    #profiling to track efficiency
    #uncomment this and code at bottom of function
    #######
    #pr.disable()
    #pr.print_stats(sort='time')
        
    return


##
#Initialization and Interface for user commands
##

#default search range is small
max_n = 5

#We expect a two arguments: max_n and number of processes 
if len(sys.argv) == 3:
    max_n = int(sys.argv[1])
    processes = int(sys.argv[2])

    #used to distinguish runs in the database
    run_id = -1

    #creating a new summation with our max_n and start at 0 sum
    try:
        c.execute('''INSERT INTO sums (cursum,maxn) VALUES (0, {})'''.format(max_n))
        run_id = c.lastrowid
        conn.commit()
    except Exception as e:
        print(e)
        exit()
        
    ##
    #Beginning the multiprocessing
    ##

    #used to tell processes when their values are needed; keeps them from waiting too long
    waiting = multiprocessing.Array('i', [0 for val in range(processes)])

    #used to check which values exist
    existence = multiprocessing.Array('i',[0 for val in range(max_n+1)])
    existence[1] = 1
    existence[2] = 1
    existence[3] = 1
    

    #holds our processes
    jobs = []


    #prime sieve to generate primes
    #we use these for finding the smallest prime divisor of each n
    print("Calculating all necessary primes...")
    primes = multiprocessing.Array('i', [i for i in sieve.primerange(2,int(sqrt(max_n))+1)])
    sieve._reset()
    
    print("Solving...")

    ##
    #Creating the processes
    ##
    
    #setting up each process with their own values of n
    #each of the k processes only looks at values of n where n+cur=0(mod k), 0<cur<k
    
    #initialize the processes in a loop
    #pass in the shared variables and start the processing
    for cur in range(0, processes):
        cur_process = multiprocessing.Process(target=inductive_solver, args=[max_n, primes, waiting, run_id, existence, processes, cur])
        cur_process.start()
        jobs.append(cur_process)

    #wait for our processes to terminate
    for cur_process in jobs:
        cur_process.join(timeout=None)
        
    #and finally, we have our solution!
    print("sum: {}".format(c.execute('''SELECT cursum FROM sums WHERE rowid = {}'''.format(run_id)).fetchall()[0]))
