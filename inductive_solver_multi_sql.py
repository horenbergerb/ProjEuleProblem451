from sympy import sieve
import sympy as sp
import sys
import multiprocessing
from multiprocessing import Lock
from math import sqrt
import numpy as np
import sqlite3
import time

lock = Lock()
get_squares = '''SELECT selfsquare FROM selfsquares WHERE modulo = {}'''

####
#Overview
####
#The goal here is to leverage previous solutions when finding the next solution
#It uses the theory of finite abelian groups
#Which is basically just fancy chinese remainder theorem

#Note: this function is made for multiprocessing
#It assumes it is being passed shared variables and only searches a subset of n values up to max_n
#The subset is determined by interval and offset
def inductive_solver(max_n, primes, sum_sol, interval, offset):

    #preparing our database
    conn = sqlite3.connect('selfsquares.db')
    conn.row_factory = lambda cursor, row: row[0]
    c = conn.cursor()
    
    #tracking the sum which will be added to the total at the end
    local_sum = 0

    #x is our n value
    x = 0
    #finding our last completed solution
    good = 0
    while not good:
        try:
            start_x = c.execute('''SELECT MAX(modulo) from selfsquares WHERE modulo%{} = {}'''.format(interval, offset)).fetchall()
            if start_x[0] != None:
                x = start_x[0]+interval
            good = 1
        except:
            pass

    print("x was set to {}".format(x))

    #handling base cases, n < 4
    #this is also where we set up offset counting for each process
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
        while (x/smallest_prime_power)%smallest_prime == 0:
            smallest_prime_power *= smallest_prime

        #handling edge cases where our n is a prime power or a power of 2
        #if n is prime power, solns are x-1 or 1
        if smallest_prime_power == x:
            if smallest_prime != 2:
                good = False
                while not good:
                    try:
                        c.execute('''INSERT INTO selfsquares VALUES ({},1),({},{})'''.format(x,x,x-1))
                        conn.commit()
                        good = True
                    except e:
                        pass
                #solutions[x] = [1,x-1]
                local_sum += 1
                x += interval
                continue
            #if it's a power of two, we just brute force it by checking every possible number for self-squareness
            #powers of two are weird
            #we probably don't have to do this, but whatever
            else:
                max_val = 1
                cur_solutions = [1,x-1]
                for cur_val in range(int(sqrt(x)),int((x/2))+1):
                    if (cur_val**2)%x == 1:
                        if (-cur_val)%x > max_val:
                            max_val = (-cur_val)%x
                        cur_solutions.append(cur_val)
                        cur_solutions.append((-cur_val)%x)
                local_sum += max_val
                good = False
                while not good:
                    try:
                        c.execute('''INSERT INTO selfsquares VALUES {}'''.format('('+str(x)+','+ ('),('+str(x)+',').join(map(str,cur_solutions)) + ')'))
                        conn.commit()
                        good = True
                    except e:
                        pass
                #solutions[x] = cur_solutions
                x += interval
                continue

        #so now we have some p^s and this is k. we should technically already have solutions for these
        k = x/smallest_prime_power
        #we have to wait until k, p^n are in our dict. other processes might not have done them yet
        good = False
        while not good:
            try:
                good = (len(c.execute(get_squares.format(k)).fetchall()) > 0 and len(c.execute(get_squares.format(smallest_prime_power)).fetchall()) > 0)
            except:
                pass
        #recall our desired number must satisfy a^2 = 1 mod kp^s
        #where kp^s = n
        #thus it satisfies a^2=1 mod p^s
        #and it satifies a^2=1 mod k
        #so our solution must be modularly equivalent to previous solutions for mod p^s and mod k

        #now we're just leveraging chinese remainder theorem
        #we do crt on every pair of solutions from p^s and k
        
        cur_sols = []
        max_val = 1
        gcd = sp.gcdex(smallest_prime_power,k)
        good = 0
        while not good:
            try:
                for a in c.execute(get_squares.format(smallest_prime_power)).fetchall():
                    for b in c.execute(get_squares.format(k)).fetchall():
                        #this is the crt part. note the use of extended euclidean algorithm
                        next_sol = ((gcd[0]*smallest_prime_power*(b)) + (gcd[1]*k*(a)))%x
                        cur_sols.append(next_sol)
                        if next_sol > max_val and next_sol < x-1:
                            max_val = next_sol
                good = 1
            except:
                pass
        local_sum += max_val
        #saving our solutions in the shared variable
        good = 0
        while not good:
            try:
                c.execute('''INSERT INTO selfsquares VALUES {}'''.format('('+str(x)+','+ ('),('+str(x)+',').join(map(str,cur_sols)) + ')'))
                conn.commit()
                good = 1
            except:
                pass

        #continuing on this process's share of the n values
        x += interval

    #Safely updating the sum
    #For some reason this didn't seem necessary with the dictionary
    lock.acquire()
    sum_sol.value += local_sum
    lock.release()
        
    return


##
#Initialization and Interface for user commands
##

max_n = 5

#We expect a two arguments: max_n and #processes 
if len(sys.argv) == 3:
    max_n = int(sys.argv[1])
    processes = int(sys.argv[2])

    ##
    #Initializing a SQL database for storage
    ##
    conn = sqlite3.connect('selfsquares.db')
    c = conn.cursor()

    try:
        c.execute('''CREATE TABLE selfsquares
    (modulo int, selfsquare int)''')
        c.execute('''INSERT INTO selfsquares VALUES (2,1)''')
        c.execute('''INSERT INTO selfsquares VALUES (3,1),(3,2)''')
        conn.commit()
    except:
        pass
    
    ##
    #Beginning the multiprocessing
    ##

    #this guy is in charge of all our processes
    #he also holds shared variables
    #we share primes and solutions through this
    manager = multiprocessing.Manager()

    #sum of max involutions
    sum_sol = manager.Value('i', 1)
    #all the primes we will need
    primes = manager.list()
    jobs = []


    #prime sieve for finding the smallest prime divisor of each n
    print("Calculating all necessary primes...")
    primes = manager.Array('i', [i for i in sieve.primerange(2,int(sqrt(max_n))+1)])
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
        cur_process = multiprocessing.Process(target=inductive_solver, args=[max_n, primes, sum_sol, processes, cur])
        cur_process.start()
        jobs.append(cur_process)

    #wait for our processes to terminate
    for cur_process in jobs:
        cur_process.join(timeout=None)
        
    #and finally, we have our solution!
    print("sum: {}".format(sum_sol.value))
