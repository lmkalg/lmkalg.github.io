from pwn import *
from argparse import ArgumentParser
import itertools
import random


NUMBER_OF_DIGITS = 5
all_attempts = 1

def refresh_timeout(conn):
    """
        Ugly trick to keep the connection open.
    """
    global all_attempts
    print("[+] Refreshing timeout!. Attempts: {}".format(all_attempts))
    all_attempts += 1
    conn.send("SOMETHING WITH INVALID FORMAT")
    conn.recvline()
    return

def remove_numbers_with_repetitions(all_numbers):
    return list(filter(lambda x: len(set(x)) == len(x), all_numbers))

def prepare_send(number):
    return str("".join(number))

def good_filter(number, attempted_number, i):
    return attempted_number[i] == number[i]

def regular_filter(number, attempted_number, i):
    return attempted_number[i] != number[i] and attempted_number[i] in number 

def water_filter(number, attempted_number, i):
    return attempted_number[i] not in number

def do_magic(amount_of_good, amount_of_regular):
    functions = []
    functions.extend([good_filter for _ in range(amount_of_good)])
    functions.extend([regular_filter for _ in range (amount_of_regular)])
    functions.extend([water_filter for _ in range(NUMBER_OF_DIGITS - len(functions))])
    return functions


def filter_functions(functions, leftover_number, attempted_number, perm, conn):
    result = True
    for index in range(NUMBER_OF_DIGITS):
        result = result and functions[index](leftover_number, attempted_number, perm[index])
    return result


def solve(host, port):
    global all_attempts
    
    all_numbers = range(10**(NUMBER_OF_DIGITS-1), 10**NUMBER_OF_DIGITS) #Change not to be only for 3
    all_numbers = map(lambda x: str(x), all_numbers)
    all_numbers = map(lambda x: [y for y in x], all_numbers)
    valid_numbers = remove_numbers_with_repetitions(all_numbers)
    
    win = False
    while not win:
        all_attempts = 1
        
        try:
            leftover_numbers = valid_numbers
            conn = remote(host,port)

            #First attempt, random 
            attempted_number = random.choice(leftover_numbers)

            #Get answer
            response = conn.recvlines(2)

            #Make first attempt
            rounds = 0
            print("[+] Valid Attempt {}: {}. Total Attempts: {}".format(rounds+1, attempted_number, all_attempts))
            all_attempts += 1
            conn.send(prepare_send(attempted_number))
            print("[+] Waiting for server answer...")
            response = conn.recvlines(2)
            response = response[1].decode("UTF-8")
            print("[+] Reponse was: {}".format(response))
            rounds += 1
            while "ona" not in response.lower() and "oops" not in response.lower():
                amount_of_good, amount_of_regular = response.strip().split(' ') #Insert with space in the middle
                amount_of_good, amount_of_regular = int(amount_of_good), int(amount_of_regular)
                functions = do_magic(amount_of_good, amount_of_regular)        
                permutations = itertools.permutations(range(NUMBER_OF_DIGITS),NUMBER_OF_DIGITS)
                new_numbers = []

                i = 0 
                for perm in permutations:
                    if i %30 == 0: #ARBITRARY
                        refresh_timeout(conn)
                    new_numbers.extend(filter(lambda x: filter_functions(functions, x, attempted_number, perm, conn), leftover_numbers))
                    i += 1 
                
                leftover_numbers = new_numbers

                if leftover_numbers != []:
                    attempted_number = random.choice(leftover_numbers)
                    print("[+] Valid Attempt {}: {}. Total Attempts: {}".format(rounds+1, attempted_number, all_attempts))
                    conn.send(prepare_send(attempted_number))
                    print("[+] Waiting for server answer...")
                    conn.recvline() # thinking
                    response = conn.recvline().decode("UTF-8")
                    print("[+] Reponse was: {}".format(response))
                else:
                    raise Exception("Impossible")
                rounds +=1
                
            if "ona" in response.lower():
                print("[+] YEAHH! I won in {} rounds!!".format(rounds))
                win = True
            else:
                print("[-] NO! I lost again!!")
                conn.close()
                continue
        except EOFError:
            print("[-] Socket closed from server!\n\n")
            conn.close()
            continue



if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-d', dest='host', help="Host of the server")
    parser.add_argument('-p', dest='port', help="Port of the server")
    args = parser.parse_args()
    if not args.host or not args.port:
        parser.error("Missing Arguments")
    
    solve(args.host, args.port)
    