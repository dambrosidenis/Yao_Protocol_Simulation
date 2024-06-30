import json
import operator
import random
import secrets
import sympy
import zmq
from itertools import chain
import json

# SOCKET
LOCAL_PORT = 987654
SERVER_HOST = "localhost"
SERVER_PORT = 987654


class Socket:
    def __init__(self, socket_type):
        self.socket = zmq.Context().socket(socket_type)
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def send(self, msg):
        self.socket.send_pyobj(msg)

    def receive(self):
        return self.socket.recv_pyobj()

    def send_wait(self, msg):
        self.send(msg)
        return self.receive()

    """
    From https://stackoverflow.com/questions/17174001/stop-pyzmq-receiver-by-keyboardinterrupt
    """

    def poll_socket(self, timetick=100):
        try:
            while True:
                obj = dict(self.poller.poll(timetick))
                if self.socket in obj and obj[self.socket] == zmq.POLLIN:
                    yield self.socket.recv_pyobj()
        except KeyboardInterrupt:
            pass


class EvaluatorSocket(Socket):
    def __init__(self, endpoint=f"tcp://*:{LOCAL_PORT}"):
        super().__init__(zmq.REP)
        self.socket.bind(endpoint)


class GarblerSocket(Socket):
    def __init__(self, endpoint=f"tcp://{SERVER_HOST}:{SERVER_PORT}"):
        super().__init__(zmq.REQ)
        self.socket.connect(endpoint)


# PRIME GROUP
PRIME_BITS = 64  # order of magnitude of prime in base 2


def next_prime(num):
    """Return next prime after 'num' (skip 2)."""
    return 3 if num < 3 else sympy.nextprime(num)


def gen_prime(num_bits):
    """Return random prime of bit size 'num_bits'"""
    r = secrets.randbits(num_bits)
    return next_prime(r)


def xor_bytes(seq1, seq2):
    """XOR two byte sequence."""
    return bytes(map(operator.xor, seq1, seq2))


def bits(num, width):
    """Convert number into a list of bits."""
    return [int(k) for k in f'{num:0{width}b}']


class PrimeGroup:
    """Cyclic abelian group of prime order 'prime'."""
    def __init__(self, prime=None):
        self.prime = prime or gen_prime(num_bits=PRIME_BITS)
        self.prime_m1 = self.prime - 1
        self.prime_m2 = self.prime - 2
        self.generator = self.find_generator()

    def mul(self, num1, num2):
        "Multiply two elements." ""
        return (num1 * num2) % self.prime

    def pow(self, base, exponent):
        "Compute nth power of an element." ""
        return pow(base, exponent, self.prime)

    def gen_pow(self, exponent):  # generator exponentiation
        "Compute nth power of a generator." ""
        return pow(self.generator, exponent, self.prime)

    def inv(self, num):
        "Multiplicative inverse of an element." ""
        return pow(num, self.prime_m2, self.prime)

    def rand_int(self):  # random int in [1, prime-1]
        "Return an random int in [1, prime - 1]." ""
        return random.randint(1, self.prime_m1)

    def find_generator(self):  # find random generator for group
        """Find a random generator for the group."""
        factors = sympy.primefactors(self.prime_m1)

        while True:
            candidate = self.rand_int()
            for factor in factors:
                if 1 == self.pow(candidate, self.prime_m1 // factor):
                    break
            else:
                return candidate
            
def read_input_data(input_data_path, aggregator_func=sum, separator=' ') :
    """Read the input data file and convert into an aggregate value.

    Args:
        input_data_path: A string containing the path to the file to read to. The file must contain a sequence of integers separated by separator and written on a single line.
        aggregator_func: The function used to aggregate the values read from the data. It must be a function that takes as input an array of integers and returns an integer.
            (optional; sum by default)
        separator: A string containing the characters that separate the input numbers in the given file.
            (optional; ' ' by default)

    Returns:
        An integer containing the aggregated value of the input data file.
    """
    with open(input_data_path) as f:
        input_data = f.readlines()[0]
    return aggregator_func(map(int, input_data.split(separator)))
            
def convert_to_binary_list(number, number_of_bits=8) :
    """Convert an integer into a list containing the digits of its number_of_bits binary representation. Negative numbers are converted into 2's complement. Throws an error if the number is >= 2^(number_of_bits-1) or < -(2^(number_of_bits-1)) because of overflow (example: for number_of_bits = 8, available values would be all integers between -128 and 127)

    Args:
        number: The integer to convert.
        number_of_bits: An integer containing the padding size.
            (optional; 8 by default)

    Returns:
        A list containing the ordered digits of number's binary representation in two's-complement, as integers
    """
    if (number < -(2**(number_of_bits-1))) or (number >= 2**(number_of_bits-1)) :
        raise Exception("Overflow error! Please change the size of the circuit and reload program!")
    binary_representation = bin(abs(number))[2:].zfill(number_of_bits) # At first, convert the number as it was positive
    if number < 0 : # If it's negative ...
        binary_representation = list(map(lambda c : '0' if c == '1' else '1', list(binary_representation))) # ... first of all complement it ...
        for i in range(number_of_bits) : # ... then increase by 1 its representation to obtain a valid two's complement encoding
            if binary_representation[~i] == '1' :
                binary_representation[~i] = '0'
            else :
                binary_representation[~i] = '1'
                break
        binary_representation = "".join(binary_representation)
    binary_list = list(map(int, list(binary_representation)))
    return binary_list

def convert_to_decimal(result):
    """Convert the circuit's output into a decimal number.

    Args:
        result: An array containing the ordered binary digits of the computed result as two's complement.

    Returns:
        The corrisponding value converted into decimal number.
    """
    if result[0] == 1 : # In this case we are dealing with a negative number, thus we must firstly complement it and then offset if by -1
        complemented_result = int("".join(list(map(lambda c : '0' if c == 1 else '1', result))), 2)
        return -complemented_result - 1
    else : # In this case we are dealing with a negative number, thus we can convert it straight away
        return int("".join([str(digit) for digit in result]),2)

def save_results(result, output_path='./output.txt'):
    """Save the result of the protocol's execution into a file.

    Args:
        result: A printable parameter containing the value of the computed result.
        output_path: A string containing a path to the file we want to write to.
            (optional; './output.txt' by default)

    Returns:
        None.
    """
    with open(output_path, 'w') as f:
        f.writelines([str(result)])

def verify(alice_data='./alice_input.txt',
           bob_data='./bob_input.txt',
           output_data='./output.txt',
           aggregator_func=sum,
           separator=' ') :
    """Evaluate the result of the yao protocol's execution.

    Args:
        alice_data: A string containing the path to Alice's input data file.
            (optional; './alice_input.txt' by default)
        bob_data: A string containing the path to Bob's input data file.
            (optional; './bob_input.txt' by default)
        output_data: A string containig the path to the output data file.
            (optional; './output.txt' by default)
        aggregator_func: The function used to aggregate the values read from the data. It must be a function that takes as input an array of integers and returns an integer.
            (optional; sum by default)
        separator: A string containing the characters that separate the input numbers in the given file.
            (optional; ' ' by default) 

    Returns:
        True if the protocol was executed successfully and the result matches, False otherwise.
    """
    alice_aggregated_data = read_input_data(alice_data, aggregator_func=aggregator_func, separator=separator)
    bob_aggregated_data = read_input_data(bob_data, aggregator_func=aggregator_func, separator=separator)
    with open(output_data) as f :
        output = int(f.readlines()[0])
    return output == alice_aggregated_data + bob_aggregated_data

def generate_circuit(n, name, id) :
    """Generate a dictionary containing an adder circuit.

    Args:
        n: An integer indicating the number of input bits for each side.
        name: A string containing the name of the circuit.
        id: A string containing the id of the circuit.

    Returns:
        A dictionary encoding an n-bit adder according to the specification of the garbled-circuit library.
    """

    circuit = {
        'id' : f'{n}-bit {id}',
        'alice' : ([1] + [5+7*i for i in range(n-1)])[::-1],
        'bob' : ([2] + [6+7*i for i in range(n-1)])[::-1],
        'out' : ([3] + [8+7*i for i in range(n-1)] + [9+7*(n-1)])[::-1],
        'gates' : [
            { 'id' : 3, 'type' : 'XOR', 'in' : [1,2] },
            { 'id' : 4, 'type' : 'AND', 'in' : [1,2] }
        ] + list(chain.from_iterable([
            [{ 'id' : 7+7*i, 'type' : 'XOR', 'in' : [5+7*i, 6+7*i] },
            { 'id' : 8+7*i, 'type' : 'XOR', 'in' : [4+7*i, 7+7*i] },
            { 'id' : 9+7*i, 'type' : 'AND', 'in' : [4+7*i, 7+7*i] },
            { 'id' : 10+7*i, 'type' : 'AND', 'in' : [5+7*i, 6+7*i] },
            { 'id' : 11+7*i, 'type' : 'OR', 'in' : [9+7*i, 10+7*i] }]
        for i in range(n-1) ])) + [
            { 'id' : 5+7*(n-1), 'type' : 'XOR', 'in' : [7*(n-1)-2, 7*(n-1)-1] },
            { 'id' : 6+7*(n-1), 'type' : 'AND', 'in' : [5+7*(n-1), 1+7*(n-1)] },
            { 'id' : 7+7*(n-1), 'type' : 'NOT', 'in' : [5+7*(n-1)] },
            { 'id' : 8+7*(n-1), 'type' : 'AND', 'in' : [7+7*(n-1), 7*(n-1)-1] },
            { 'id' : 9+7*(n-1), 'type' : 'OR', 'in' : [6+7*(n-1), 8+7*(n-1)] }
        ]
    }
    return { 'name' : name, 'circuits' : [circuit] }

def generate_and_save_circuit(path='./circuit.json', number_of_bits=8, name='adder', id='adder'):
    """Generate an adder circuit and save it to file.

    Args:
        path: A string containing the path for the file to save the circuit to.
            (optional; './circuit.json' by default)
        number_of_bits: (optional) An integer indicating the size of the input for the circuit (for each party).
            (optional; 8 by default)
        name: (optional) A string containing the name of the circuit.
            (optional; 'adder' by default)
        id: A string containing the id of the circuit.
            (optional; 'adder by default)

    Returns:
        None.
    """
    circuit = generate_circuit(number_of_bits, name, id )
    with open(path, 'w') as f :
        json.dump(circuit, f, indent=1)

# HELPER FUNCTIONS
def parse_json(json_path):
    with open(json_path) as json_file:
        return json.load(json_file)
