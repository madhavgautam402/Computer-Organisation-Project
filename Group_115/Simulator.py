import sys
import os

# Convert integer to a 32 bit binary string

def binary_format(value):
    if isinstance(value, int):
        value = value & 0xFFFFFFFF
        return f"0b{value:032b}"
    return value

# Initializes empty dictionary for memory storage

def init_memory(base_addr=0x00010000):
    return {}

# Reads single byte from memory

def read_byte_memory(memory, addr):
    if addr not in memory:
        return 0
    return memory[addr] & 0xFF

# Reads 16 bit halfword by combining two bytes

def read_halfword_memory(memory, addr):
    value = 0
    for i in range(2):
        value |= read_byte_memory(memory, addr + i) << (i * 8)
    return value

# Reads 32 bit word by combining four bytes

def read_word_memory(memory, addr):
    value = 0
    for i in range(4):
        value |= read_byte_memory(memory, addr + i) << (i * 8)
    return value

# Writes single byte to memory

def write_byte_memory(memory, addr, value):
    memory[addr] = value & 0xFF  # Ensures only lowest byte is stored


# Writes a 16-bit halfword to memory

def write_halfword_memory(memory, addr, value):
    for i in range(2):
        write_byte_memory(memory, addr + i, (value >> (i * 8)) & 0xFF)

# Writes a 32-bit word to memory

def write_word_memory(memory, addr, value):
    for i in range(4):
        write_byte_memory(memory, addr + i, (value >> (i * 8)) & 0xFF)
