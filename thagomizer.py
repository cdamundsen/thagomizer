#! /usr/bin/env python

import os
import sys
import textwrap

import click
import cv2
import numpy as np


class MessageTooLongException(Exception):
    def __init__(self, msg):
        self.message = msg

class FileToSmallException(Exception):
    def __init__(self, msg):
        self.message = msg

class InputFileException(Exception):
    def __init__(self, msg):
        self.message = msg

class Picture:
    def __init__(self, filename: str):
        self.filename = filename # The name of the input image file
        self.original = cv2.imread(filename)
        self.height, self.width, self.bytes_per_pixel = np.shape(self.original)
        self.flattened = self.original.flatten()
        self.size_bits = 16 # The maximum number of numbers in the input file that can be saved is 2^^16 - 1
        self.num_size_bits = 24 # The maximum number in the input set that can be saved in the file is 2^^24 - 1

    def encode(self, msg: list[int]) -> None:
        if len(msg) > pow(2, self.size_bits) - 1:
            raise MessageTooLongException(f"Max message length exceded. Message is {len(msg)}, max allowed is {pow(2, self.size_bits)-1}")

        index = 0

        # Store the number of numbers in the message
        length = len(msg)
        length_b = format(length, f"{self.size_bits:03}b")
        for b in length_b:
            self.flattened[index] = self.set_lsb(self.flattened[index], int(b))
            index += 1

        # Store the number of bits used for each number
        max_number = max(msg)
        max_number_bits = len(format(max_number, "b")) # the number of bits required to represent the largest number in the message

        # Figure out if there is enough space to store all the bits of the message
        if (max_number_bits * len(msg)) > len(self.flattened):
            raise FileToSmallException("The file is too small to hold the entire message")

        max_bits_string = format(max_number_bits, f"{self.num_size_bits:03}b")

        for b in max_bits_string:
            self.flattened[index] = self.set_lsb(self.flattened[index], int(b))
            index += 1

        # Now actually store the data
        for number in msg:
            number_b = format(number, f"{max_number_bits:03}b")
            for bit in number_b:
                self.flattened[index] = self.set_lsb(self.flattened[index], int(bit))
                index += 1

    def decode(self):
        numbers = []
        index = 0
        length_str = ''
        size_str = ''
        # Figure out how many numbers we need to pull out of the image
        for i in range(self.size_bits):
            lsb = str(self.flattened[index] & 1)
            length_str += lsb
            index += 1
        msg_length = int(length_str, 2)

        # Figure out how many bits are used to reprsent each number in the message
        for i in range(self.num_size_bits):
            lsb = str(self.flattened[index] & 1)
            size_str += lsb
            index += 1
        number_size = int(size_str, 2)

        # Now go get the numbers
        for i in range(msg_length):
            number_str = ''
            for j in range(number_size):
                lsb = str(self.flattened[index] & 1)
                number_str += lsb
                index += 1
            number = int(number_str, 2)
            numbers.append(number)
        
        return numbers

    def save_image(self, filename: str) -> None:
        reshaped = self.flattened.reshape(self.height, self.width, self.bytes_per_pixel)
        cv2.imwrite(filename, reshaped)

    def set_lsb(self, number: int, bit: int) -> int:
        new_number = number >> 1 # Clear the least significant bit
        new_number = new_number << 1
    
        if bit == 1:
            # if we want the lsb to be one, set it to one
            new_number = new_number | 1
        return new_number


def get_input(infile: str) -> list[int]:
    with open(infile) as inf:
        data = inf.read().split()
    try:
        data = [int(x) for x in data]
    except ValueError as e:
        msg = f"The input file must contain integers separated by whitespace.\n{e.args[0]}"
        raise InputFileException(f"The input file must contain integers separated by whitespace.\n{e.args[0]}")
    else:
        return data


def check_inputs(p: click.Path, of: click.Path, inf: click.Path|None, ins: bool, ext: bool) -> None:
    """
    Validates the arguments that were passed in on the command line. If an
    incorrect selection of input arguments were passed in, it prints a helpful
    error message is printed and then exits

    Arguments:
        p: a click.Path instance pointing to the input graphic, or None
        of: a click.Path pointing to the output file
        inf: a click.Path pointing to the encrypted message being inserted into the graphic
        ins: a boolean that indicates if the encrypted message should be inserted into the graphic
        ext: a boolean that indicates if the encyrpted message should pulled out of the graphic

    Returns: N/A
    """
    problems = []
    if not p:
        problems.append("  * You must include an image file using the picture option")
    if not of:
        problems.append("  * You must include the path to an output file")
    if os.path.isfile(of):
        problems.append(f"  * {of} already exists. This program won't overwrite it")
    if ins and ext:
        problems.append("  * You can only select insert or extract")
    elif not (ins or ext):
        problems.append("  * You must select insert or extract")
    elif ins and not inf:
        problems.append("  * You have to inlude an input file to insert into the picture")
    if problems:
        problems.append("thagomizer.py --help for help")
        problem_str = "\n".join(problems)
        print(f"The following issues were found:\n{problem_str}")
        sys.exit(1)


@click.command()
@click.option('--picture', '-p', type=click.Path(exists=True), default=None, help="The image file to be worked on. Required")
@click.option('--output_file', '-o', type=click.Path(), default=None, help='The destination of the output file. Required')
@click.option('--input_file', '-i', type=click.Path(), default=None, help="The input file to be inserted into the image. Optional")
@click.option('--insert', is_flag=True, help="Set this flag to insert the input file into the image.")
@click.option('--extract', is_flag=True, help="Set this flag to extract the info from the the image.")
def thagomizer(picture: click.File, output_file: click.Path, input_file: click.Path, insert: bool, extract: bool):
    """
    Thagomizer takes an image file uses steganograpy to embed a list integers
    into the image file which can then be saved as a new, visually identical,
    image. Said image can then be sent to someone else who can use thagomizer
    to extract that list of integers from the image file. If that list of
    integers was generated by the companion program cryptobook, the list of
    integers can be decrypted back into the message that Alice sent to Bob
    """
    problems = []
    if not picture:
        problems.append("  * You must include an image file using the picture option")
    if not output_file:
        problems.append("  * You must include the path to an output file")
    if os.path.isfile(output_file):
        problems.append(f"  * {output_file} already exists. This program won't overwrite it")
    if insert and extract:
        problems.append("  * You can only select insert or extract")
    elif not (insert or extract):
        problems.append("  * You must select insert or extract")
    elif insert and not input_file:
        problems.append("  * You have to inlude an input file to insert into the picture")
    if problems:
        problems.append("thagomizer.py --help for help")
        problem_str = "\n".join(problems)
        print(f"The following issues were found:\n{problem_str}")
        sys.exit(1)

    p = Picture(picture)

    if insert:
        numbers = get_input(input_file)
        p.encode(numbers)
        p.save_image(output_file)
    elif extract:
        numbers = p.decode()
        numbers = ' '.join([f"{n}" for n in numbers])
        with open(output_file, 'w') as outf:
            outf.write(textwrap.fill(numbers, width=80))


if __name__ == '__main__':
    thagomizer()
