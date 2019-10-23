import socket 
from threading import Thread 
from SocketServer import ThreadingMixIn 
import random
import time
import sys

TIME_BETWEEN_ANSWERS = 5
SOCKET_TIMEOUT = 10
MAX_CONNECTIONS = 256
MAX_CONNECTIONS_PER_IP = 10
NUMBER_OF_DIGITS = 5
MAX_AMOUNT_OF_VALID_ATTEMPTS = 4
MAX_AMOUNT_OF_ATTEMPTS = 100
FLAG = "ONA{861c4f67e887dec85292d36ab05cd7a1a7275228}"

connections = {}
total_connections = 0

class MaxAmountOfAttemptsException(Exception):
    pass

class MaxAmountOfValidAttemptsException(Exception):
    pass


def valid_attempt(attempted_number):
    return len(attempted_number) == NUMBER_OF_DIGITS

def remove_numbers_with_repetitions(all_numbers):
    return filter(lambda x: len(set(x)) == len(x), all_numbers)

def good_one(my_number, attempted_number,i):
    return  1 if my_number[i] == attempted_number[i] else 0

def regular_one(my_number, attempted_number,i):
    return  1 if my_number[i] != attempted_number[i] and attempted_number[i] in my_number else 0

def to_int(number):
    return int("".join(number))

def remove_ctrl_keys(attempted_number):
    """
        remove 0a 0d 
    """
    return attempted_number.strip()


def play_game(conn):
    all_numbers = range(10**(NUMBER_OF_DIGITS-1), 10**NUMBER_OF_DIGITS)
    all_numbers = map(lambda x: str(x), all_numbers)
    all_numbers = map(lambda x: [y for y in x], all_numbers)

    valid_numbers = remove_numbers_with_repetitions(all_numbers)
    leftover_numbers = valid_numbers

    #Presentation
    conn.send("Welcome to DA game. I'll choose a number of {} digits. It cannot not neither start with 0 nor repeat digits. You'll have to guess it. The answer shows first the amount of goods, then the amount of regulars. Remember, a digit is good if it was placed in the correct place. On the other hand a digit is regular if it is inside the number, but it wasn't placed in the correct place. Whenever you're ready just start guessing\nYou have only {} attempts. Good luck!\n".format(NUMBER_OF_DIGITS, MAX_AMOUNT_OF_VALID_ATTEMPTS))

    #Choose the number 
    my_number = random.choice(leftover_numbers)
    print "[d] Number is: {}".format(my_number)
    sys.stdout.flush()


    amount_of_attempts = 0
    attempted_number = remove_ctrl_keys(conn.recv(1024))
    amount_of_attempts += 1
    while not valid_attempt(attempted_number):
        conn.send("[W] Invalid format of the attempted number (this attempt doesn't count!). Remember it should be a number of {} digits\n".format(NUMBER_OF_DIGITS))
        attempted_number = remove_ctrl_keys(conn.recv(1024))
        amount_of_attempts += 1


    amount_of_valid_attempts = 0
    while amount_of_valid_attempts < MAX_AMOUNT_OF_VALID_ATTEMPTS and amount_of_attempts < MAX_AMOUNT_OF_ATTEMPTS:
        amount_of_goods = sum([good_one(my_number, attempted_number, digit_index) for digit_index in xrange(NUMBER_OF_DIGITS)])
        amount_of_regulars = sum([regular_one(my_number, attempted_number, digit_index) for digit_index in xrange(NUMBER_OF_DIGITS)])
        conn.send("mm let me check...\n")
        time.sleep(TIME_BETWEEN_ANSWERS)

        if amount_of_goods == NUMBER_OF_DIGITS:
            conn.send("YEAHH! You won in the flag is {}\n".format(FLAG))
            return
        else:
            conn.send("{} {}\n".format(amount_of_goods, amount_of_regulars))
            attempted_number = remove_ctrl_keys(conn.recv(1024))
            amount_of_attempts += 1
            while not valid_attempt(attempted_number) and amount_of_attempts < MAX_AMOUNT_OF_ATTEMPTS:
                conn.send("[W] Invalid format of the attempted number (this attempt doesn't count!). Remember it should be a number of {} digits\n".format(NUMBER_OF_DIGITS))
                attempted_number = remove_ctrl_keys(conn.recv(1024))
                amount_of_attempts += 1
            amount_of_valid_attempts += 1
    if amount_of_attempts == MAX_AMOUNT_OF_ATTEMPTS:
        conn.send("Oops! Sorry. {} attempts reached!\n".format(MAX_AMOUNT_OF_ATTEMPTS))
        raise MaxAmountOfAttemptsException
    elif amount_of_valid_attempts == MAX_AMOUNT_OF_VALID_ATTEMPTS:
        conn.send("Oops! Sorry. {} valid attempts reached!\n".format(MAX_AMOUNT_OF_VALID_ATTEMPTS))
        raise MaxAmountOfValidAttemptsException

    

# Multithreaded Python server : TCP Server Socket Thread Pool
class ClientThread(Thread): 
 
    def __init__(self,ip,port): 
        Thread.__init__(self) 
        self.ip = ip 
        self.port = port 
        print "[+] New server socket thread started for " + ip + ":" + str(port) 
        sys.stdout.flush()
 
    def run(self): 
        try:
            conn.settimeout(SOCKET_TIMEOUT)
            play_game(conn)
        except socket.timeout:
            print("[-] Socket timeout reached!")
            conn.send(("[-] Socket timeout reached!"))
        except MaxAmountOfAttemptsException:
            print("[-] MaxAmount of attempts reached from {}:{}".format(self.ip, self.port))
            conn.send(("[-] MaxAmount of attempts reached from {}:{}".format(self.ip, self.port)))
        except MaxAmountOfValidAttemptsException:
            print("[-] MaxAmount of valid attempts reached from {}:{}".format(self.ip, self.port))
            conn.send(("[-] MaxAmount of valid attempts reached from {}:{}".format(self.ip, self.port)))
        except Exception as e: 
            pass
        finally:
            print '[-] Connection from {}:{} closed!'.format(self.ip, self.port)
            sys.stdout.flush()
            conn.close()
            amount_of_connections = connections[self.ip]
            connections.update({self.ip:amount_of_connections-1})
            print '[+] Connections: {}'.format(connections)
            sys.stdout.flush()

# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '0.0.0.0' 
TCP_PORT = 1337 
BUFFER_SIZE = 20  # Usually 1024, but we need quick response 

tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
print "[+] Server up!" 
sys.stdout.flush()
tcpServer.bind((TCP_IP, TCP_PORT)) 
threads = [] 
 
while True: 
    tcpServer.listen(4) 
    (conn, (ip,port)) = tcpServer.accept() 
    print "[+] New connection received from {}:{}".format(ip,port)
    sys.stdout.flush()

    if sum(connections.values()) >= MAX_CONNECTIONS:
        conn.send("Sorry. Max number of connections achieved.")
        conn.close()
        print "[-] Connection from {}:{} dropped because of Max connections achieved".format(ip, port) 
        sys.stdout.flush()
        continue

    if ip in connections.keys():
        amount_of_connections = connections.get(ip)
        if amount_of_connections < MAX_CONNECTIONS_PER_IP:
            connections.update({ip:amount_of_connections+1})
        else:
            conn.send("Sorry. Max number of connections from your IP reached.")
            conn.close()
            print "[-] Connection from {}:{} dropped because of Max connections achieved for that ip".format(ip,port) 
            sys.stdout.flush()
            continue
    else:
        connections.update({ip:1})

    print "Connections: {}".format(connections)
    sys.stdout.flush()
    newthread = ClientThread(ip,port) 
    newthread.start() 
    threads.append(newthread) 
 
for t in threads: 
    t.join() 
