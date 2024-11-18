#! /usr/bin/env python

import click
import cv2
import numpy as np


class MessageTooLongException(Exception):
    def __init__(self, msg):
        self.message = msg

class FileToSmallException(Exception):
    def __init__(self, msg):
        self.message = msg


class Picture:
    def __init__(self, filename: str, max_msg_bits = 16):
        self.filename = filename
        self.original = cv2.imread(filename)
        self.height, self.width, self.bytes_per_pixel = np.shape(self.original)
        self.flattened = self.original.flatten()
        self.size_bits = max_msg_bits
        self.num_size_bits = 24

    def encode(self, msg: list[int]):
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
        print(max_number_bits)

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

        print(f"self.size_bits = {self.size_bits}")
        print(f"self.num_size_bits = {self.num_size_bits}")
        print(f"index = {index}")

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


def get_image(file_name: str) -> np.ndarray:
    """
    import numpy as np
    import cv2
    m = cv2.imread("/Users/amundsen/Downloads/OhLawd.png")
    h, w. bpp = np.shape(m)
    h,w,bpp = np.shape(m)
    print("width: " + str(w))
    print(f"height: {h}")
    print(f"bpp: {bpp}")
    m[1][1]
    import array
    m[10][10] = (0, 0, 255)
    cv2.imwrite('red_pixel.png', m)
    """
    img = cv2.imread(file_name)
    print(dir(img))
    return img

