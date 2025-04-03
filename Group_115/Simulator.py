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

# Initialize 32 registers and sets register x2(sp) to 380

def init_registers():
    registers = {'values': [0] * 32, 'pc': 0}
    registers['values'][2] = 380  # Set the third register(index [2]) to 380
    return registers

# Reads value from register

def read_register(registers, reg_num):
    if 0 <= reg_num < 32:
        return registers['values'][reg_num]
    return 0

# Writes value to register(except x0)

def write_register(registers, reg_num, value):
    if 1 <= reg_num < 32:
        value = value & 0xFFFFFFFF
        if value & 0x80000000:
            value |= ~0xFFFFFFFF
        registers['values'][reg_num] = value

# Reads current program counter(PC)

def pc_read(registers):
    return registers['pc']

# Updates program counter(PC)

def pc_write(registers, value):
    registers['pc'] = value

# Decodes RISC-V instruction and returns its components

def decode_instruction(binary_instruction):
    instr_int = int(binary_instruction, 2)
    opcode = instr_int & 0x7F
    
    rd = (instr_int >> 7) & 0x1F
    funct3 = (instr_int >> 12) & 0x7
    rs1 = (instr_int >> 15) & 0x1F
    rs2 = (instr_int >> 20) & 0x1F
    
    if opcode == 0b0110011:
        funct7 = (instr_int >> 25) & 0x7F
        if funct3 == 0x0 and funct7 == 0x00:  #add
            return {'type': 'R', 'op': 'add', 'rd': rd, 'rs1': rs1, 'rs2': rs2}
        elif funct3 == 0x0 and funct7 == 0x20:  #sub
            return {'type': 'R', 'op': 'sub', 'rd': rd, 'rs1': rs1, 'rs2': rs2}
        elif funct3 == 0x5 and funct7 == 0x00:  #srl
            return {'type': 'R', 'op': 'srl', 'rd': rd, 'rs1': rs1, 'rs2': rs2}
        elif funct3 == 0x7 and funct7 == 0x00:  #and
            return {'type': 'R', 'op': 'and', 'rd': rd, 'rs1': rs1, 'rs2': rs2}
        elif funct3 == 0x6 and funct7 == 0x00:  #or
            return {'type': 'R', 'op': 'or', 'rd': rd, 'rs1': rs1, 'rs2': rs2}
        elif funct3 == 0x2 and funct7 == 0x00:  #slt
            return {'type': 'R', 'op': 'slt', 'rd': rd, 'rs1': rs1, 'rs2': rs2}
    elif opcode == 0b0010011:  # I-type (immediate)
        imm = (instr_int >> 20) & 0xFFF
        if imm & 0x800:
            imm |= 0xFFFFF000
        else:
            imm &= 0xFFF
        if funct3 == 0x0:  #addi
            return {'type': 'I', 'op': 'addi', 'rd': rd, 'rs1': rs1, 'imm': imm}
    elif opcode == 0b0000011:  # I-type (load)
        imm = (instr_int >> 20) & 0xFFF
        if imm & 0x800:
            imm |= 0xFFFFF000
        else:
            imm &= 0xFFF
        if funct3 == 0x2:  #lw
            return {'type': 'I', 'op': 'lw', 'rd': rd, 'rs1': rs1, 'imm': imm}
    elif opcode == 0b0100011:  # S-type
        imm_lo = (instr_int >> 7) & 0x1F
        imm_hi = (instr_int >> 25) & 0x7F
        imm = (imm_hi << 5) | imm_lo
        if imm & 0x800:
            imm |= 0xFFFFF000
        else:
            imm &= 0xFFF
        if funct3 == 0x2:  #sw
            return {'type': 'S', 'op': 'sw', 'rs1': rs1, 'rs2': rs2, 'imm': imm}
    elif opcode == 0b1100011:  # B-type
        imm_11 = (instr_int >> 7) & 0x1
        imm_4_1 = (instr_int >> 8) & 0xF
        imm_10_5 = (instr_int >> 25) & 0x3F
        imm_12 = (instr_int >> 31) & 0x1
        imm = (imm_12 << 12) | (imm_11 << 11) | (imm_10_5 << 5) | (imm_4_1 << 1)
        if imm & 0x1000:
            imm |= 0xFFFFE000
        else:
            imm &= 0x1FFF
        if funct3 == 0x0:  #beq
            return {'type': 'B', 'op': 'beq', 'rs1': rs1, 'rs2': rs2, 'imm': imm}
        elif funct3 == 0x1:  #bne
            return {'type': 'B', 'op': 'bne', 'rs1': rs1, 'rs2': rs2, 'imm': imm}
        elif funct3 == 0x4:  #blt
            return {'type': 'B', 'op': 'blt', 'rs1': rs1, 'rs2': rs2, 'imm': imm}
    elif opcode == 0b1101111:  # J-type (jal)
        imm_20 = (instr_int >> 31) & 0x1
        imm_10_1 = (instr_int >> 21) & 0x3FF
        imm_11 = (instr_int >> 20) & 0x1
        imm_19_12 = (instr_int >> 12) & 0xFF
        imm = (imm_20 << 20) | (imm_19_12 << 12) | (imm_11 << 11) | (imm_10_1 << 1)
        if imm & 0x100000:
            imm |= 0xFFF00000
        else:
            imm &= 0xFFFFF
        return {'type': 'J', 'op': 'jal', 'rd': rd, 'imm': imm}
    elif opcode == 0b1100111 and funct3 == 0x0:  # I-type (jalr)
        imm = (instr_int >> 20) & 0xFFF
        if imm & 0x800:
            imm |= 0xFFFFF000
        else:
            imm &= 0xFFF
        return {'type': 'I', 'op': 'jalr', 'rd': rd, 'rs1': rs1, 'imm': imm}
    return {'type': 'unknown', 'op': 'unknown', 'binary': binary_instruction}

def execute_r_type(instr, registers):
    op = instr['op']
    rd = instr['rd']
    rs1_val = registers['values'][instr['rs1']]
    rs2_val = registers['values'][instr['rs2']]
    result = 0
    if op == 'add':
        result = rs1_val + rs2_val
    elif op == 'sub':
        result = rs1_val - rs2_val
    elif op == 'slt':
        result = 1 if (rs1_val < rs2_val) else 0
    elif op == 'srl':
        result = (rs1_val & 0xFFFFFFFF) >> (rs2_val & 0x1F)
    elif op == 'or':
        result = rs1_val | rs2_val
    elif op == 'and':
        result = rs1_val & rs2_val
    write_register(registers, rd, result)

def execute_i_type(instr, registers, memory, pc):
    """Execute I-type instructions"""
    op = instr['op']
    rd = instr['rd']
    rs1_val = registers['values'][instr['rs1']]
    if op == 'addi':
        result = rs1_val + instr['imm']
        write_register(registers, rd, result)
    elif op == 'lw':
        addr = rs1_val + instr['imm']
        result = read_word_memory(memory, addr)
        write_register(registers, rd, result)
    elif op == 'jalr':
        target = (rs1_val + instr['imm']) & ~1
        if target == pc:
            print(f"Warning: jalr target {target} is the same as current PC {pc}, halting execution")
            return pc + 4
        write_register(registers, rd, pc + 4)
        return target
    return None

def execute_s_type(instr, registers, memory):
    op = instr['op']
    rs1_val = registers['values'][instr['rs1']]
    rs2_val = registers['values'][instr['rs2']]
    addr = rs1_val + instr['imm']
    if op == 'sw':
        write_word_memory(memory, addr, rs2_val)

def execute_b_type(instr, registers, pc):
    op = instr['op']
    rs1_val = registers['values'][instr['rs1']]
    rs2_val = registers['values'][instr['rs2']]
    next_pc = pc + 4
    if op == 'beq':
        if rs1_val == rs2_val:
            next_pc = pc + instr['imm']
    elif op == 'bne':
        if rs1_val != rs2_val:
            next_pc = pc + instr['imm']
    elif op == 'blt':
        if rs1_val < rs2_val:
            next_pc = pc + instr['imm']
    return next_pc

def execute_j_type(instr, registers, pc):
    op = instr['op']
    rd = instr['rd']
    if op == 'jal':
        write_register(registers, rd, pc + 4)
        return pc + instr['imm']
    return pc + 4
