#!/usr/bin/env python3
import logging
import argparse
import util
from parties import Alice, Bob

logging.basicConfig(format="[%(levelname)s] %(message)s",
                    level=logging.WARNING)

def main(
    party,
    circuit_path="./circuit.json",
    alice_input_path="./alice_input.txt",
    bob_input_path="./bob_input.txt",
    output_path='./output.txt',
    number_of_bits='8',
    oblivious_transfer=True,
    loglevel=logging.WARNING,
):
    logging.getLogger().setLevel(loglevel)
    
    if party == "alice":
        util.generate_and_save_circuit(path=circuit_path, number_of_bits=int(number_of_bits))
        alice = Alice(circuit_path,
                      input_data_path=alice_input_path,
                      output_path=output_path,
                      number_of_bits=int(number_of_bits),
                      oblivious_transfer=oblivious_transfer)
        alice.start()
        result = util.verify(alice_data=alice_input_path, bob_data=bob_input_path, output_data=output_path)
        if result :
            print("Protocol successfully executed!")
        else :
            print("Unsuccessful Execution. Check input and output files to better understand what happened")
    elif party == "bob":
        bob = Bob(input_data_path=bob_input_path,
                  number_of_bits=int(number_of_bits),
                  oblivious_transfer=oblivious_transfer)
        bob.listen()
    else:
        logging.error(f"Unknown party '{party}'")

if __name__ == '__main__':
    loglevels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    parser = argparse.ArgumentParser(description="Run Yao protocol.")
    parser.add_argument("party",
                        choices=["alice", "bob",],
                        help="the yao party to run")
    parser.add_argument("--circuit",
                        default="./circuit.json",
                        help="the JSON circuit file for alice and local tests")
    parser.add_argument("--no-oblivious-transfer",
                        action="store_true",
                        help="disable oblivious transfer")
    parser.add_argument("--alice",
                        default="./alice_input.txt",
                        help="the input path to Alice's set of numbers")
    parser.add_argument("--bob",
                        default="./bob_input.txt",
                        help="the input path to Bob's set of numbers")
    parser.add_argument("--output",
                        default="./output.txt",
                        help="the path for the file to write the result of the execution to")
    parser.add_argument("--bits",
                        default="8",
                        help="the size of the circuit and the representation of its inputs")
    parser.add_argument("--loglevel",
                        metavar="level",
                        choices=loglevels.keys(),
                        default="warning",
                        help="the log level (default 'warning')")
    main(
        party=parser.parse_args().party,
        circuit_path=parser.parse_args().circuit,
        alice_input_path=parser.parse_args().alice,
        bob_input_path=parser.parse_args().bob,
        output_path=parser.parse_args().output,
        oblivious_transfer=not parser.parse_args().no_oblivious_transfer,
        number_of_bits=parser.parse_args().bits,
        loglevel=loglevels[parser.parse_args().loglevel],
    )