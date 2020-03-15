Problem Statement:

Consider the number 15.
There are eight positive numbers less than 15 which are coprime to 15: 1, 2, 4, 7, 8, 11, 13, 14.
The modular inverses of these numbers modulo 15 are: 1, 8, 4, 13, 2, 11, 7, 14
because
1 · 1 mod 15=1
2 · 8=16 mod 15=1
4 · 4=16 mod 15=1
7 · 13=91 mod 15=1
11 · 11=121 mod 15=1
14 · 14=196 mod 15=1

Let I(n) be the largest positive number m smaller than n-1 such that the modular inverse of m modulo n equals m itself.
So I(15)=11.
Also I(100)=51 and I(7)=1.

Find ∑ I(n) for 3≤n≤2×10^7

OVERVIEW OF FILES:
There are a couple different versions of solution in this project. All of them work, but some are more practical than others.

BEST SOLUTION:
The most successful solution was
"inductive_solver_multi_sql.py"
It is designed for Python3
This solution used multiple processes to concurrently solve self-square of each modulus.
The squares are stored in a local sql database.
Then, each process dumps its sum of max squares into a sum in the database.

This solution needs to be altered to use existing database data, but the necessary modifications are small

SECOND BEST SOLUTION:
"inductive_solver_multi.py"
This solution is functional, but I didn't quite have enough RAM for it. You could probably optimize this to make it sufficient. I suspect it is the fastest solution.

OTHER SOLUTIONS:
Other solutions use factorizations or brute force checks to get the desired values. They use a variety of mathy hacks, but they slow down far too quickly.

teengy weengy
