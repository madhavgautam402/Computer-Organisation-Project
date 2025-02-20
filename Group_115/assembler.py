# RISC-V Assembler: Encodes assembly instructions into machine code

REGISTERS = {
    'zero': 0, 'ra': 1, 'sp': 2, 'gp': 3, 'tp': 4, 't0': 5, 't1': 6, 't2': 7, 
    's0': 8, 'fp': 8, 's1': 9, 'a0': 10, 'a1': 11, 'a2': 12, 'a3': 13, 'a4': 14, 
    'a5': 15, 'a6': 16, 'a7': 17, 's2': 18, 's3': 19, 's4': 20, 's5': 21, 
    's6': 22, 's7': 23, 's8': 24, 's9': 25, 's10': 26, 's11': 27, 't3': 28, 
    't4': 29, 't5': 30, 't6': 31
}

# Ensuring that both named registers and numeric registres are implemented correctly

def get_register_number(reg):
    reg = reg.lower()
    if reg in REGISTERS:
        return REGISTERS[reg]
    if reg.startswith('x') and reg[1:].isdigit():
        reg_num = int(reg[1:])
        if 0 <= reg_num <= 31:
            return reg_num
    raise ValueError(f"Invalid register: {reg}")

# Ensures that immediate values fit within the specified bit-length

def check_immediate_bounds(imm, bits):
    try:
        value = int(imm, 16) if isinstance(imm, str) and imm.startswith('0x') else int(imm)
        min_val, max_val = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
        if not (min_val <= value <= max_val):
            raise ValueError(f"Immediate {value} out of range for {bits}-bit")
        return value
    except ValueError:
        raise ValueError(f"Invalid immediate value {imm}")

FUNCT3 = {
    'add': '000', 'sub': '000', 'sll': '001', 'slt': '010', 'sltu': '011', 
    'xor': '100', 'srl': '101', 'sra': '101', 'or': '110', 'and': '111',
    'addi': '000', 'slti': '010', 'sltiu': '011', 'xori': '100', 'ori': '110', 
    'andi': '111', 'slli': '001', 'srli': '101', 'srai': '101', 'lb': '000', 
    'lh': '001', 'lw': '010', 'lbu': '100', 'lhu': '101', 'jalr': '000', 
    'sb': '000', 'sh': '001', 'sw': '010', 'beq': '000', 'bne': '001', 
    'blt': '100', 'bge': '101', 'bltu': '110', 'bgeu': '111'
}

FUNCT7 = {'add': '0000000', 'sub': '0100000', 'sll': '0000000', 'slt': '0000000',
          'sltu': '0000000', 'xor': '0000000', 'srl': '0000000', 'sra': '0100000',
          'or': '0000000', 'and': '0000000', 'slli': '0000000', 'srli': '0000000',
          'srai': '0100000'}

# Mapping instructions

OPCODES = {
    'r-type': '0110011', 'i-type': '0010011', 'load': '0000011', 'jalr': '1100111',
    's-type': '0100011', 'b-type': '1100011', 'lui': '0110111', 'auipc': '0010111',
    'jal': '1101111'
}

# Used for arithmetic and logical operations

def encode_r_type(opcode, rd, rs1, rs2):
    return f"{FUNCT7[opcode]}{rs2:05b}{rs1:05b}{FUNCT3[opcode]}{rd:05b}{OPCODES['r-type']}"

# Used for arithmetic, bitwise, memory loads, and jumps

def encode_i_type(opcode, rd, rs1, imm):
    imm_str = f"{FUNCT7[opcode]}{imm & 0x1F:05b}" if opcode in ['slli', 'srli', 'srai'] else f"{imm & 0xFFF:012b}"
    op = 'load' if opcode in ['lb', 'lh', 'lw', 'lbu', 'lhu'] else 'jalr' if opcode == 'jalr' else 'i-type'
    return f"{imm_str}{rs1:05b}{FUNCT3[opcode]}{rd:05b}{OPCODES[op]}"

# Used for memory storage

def encode_s_type(opcode, rs2, rs1, imm):
    imm = imm & 0xFFF
    return f"{imm >> 5:07b}{rs2:05b}{rs1:05b}{FUNCT3[opcode]}{imm & 0x1F:05b}{OPCODES['s-type']}"

# Used for conditional branching

def encode_b_type(opcode, rs1, rs2, imm):
    imm = imm & 0x1FFE
    return f"{imm >> 12 & 0x1:01b}{imm >> 5 & 0x3F:06b}{rs2:05b}{rs1:05b}{FUNCT3[opcode]}{imm >> 1 & 0xF:04b}{imm >> 11 & 0x1:01b}{OPCODES['b-type']}"

# Used for lui & auipc

def encode_u_type(opcode, rd, imm):
    return f"{imm & 0xFFFFF000:032b}[:20]{rd:05b}{OPCODES[opcode]}"

# Encodes jal instructions

def encode_j_type(opcode, rd, imm):
    imm = imm & 0x1FFFFE
    return f"{imm >> 20 & 0x1:01b}{imm >> 1 & 0x3FF:010b}{imm >> 11 & 0x1:01b}{imm >> 12 & 0xFF:08b}{rd:05b}{OPCODES['jal']}"

# Considers an instruction, identifies its type, and calls the respective encoding function

def encode_instruction(parts, current_address, labels):
    opcode = parts[0].lower()

    try:
        if opcode in ['add', 'sub', 'sll', 'slt', 'sltu', 'xor', 'srl', 'sra', 'or', 'and']:  # R-type
            rd, rs1, rs2 = get_register_number(parts[1]), get_register_number(parts[2]), get_register_number(parts[3])
            return encode_r_type(opcode, rd, rs1, rs2)

        elif opcode in ['addi', 'slti', 'sltiu', 'xori', 'ori', 'andi', 'slli', 'srli', 'srai']:  # I-type
            rd = get_register_number(parts[1])
            rs1 = get_register_number(parts[2])
            imm = check_immediate_bounds(parts[3], 12)
            return encode_i_type(opcode, rd, rs1, imm)

        elif opcode in ['lb', 'lh', 'lw', 'lbu', 'lhu']:  # Load
            rd = get_register_number(parts[1])
            offset_str, base_reg = parts[2].split('(', 1)
            base_reg = base_reg.rstrip(')')
            imm = check_immediate_bounds(offset_str, 12)
            rs1 = get_register_number(base_reg)
            return encode_i_type(opcode, rd, rs1, imm)

        elif opcode in ['sb', 'sh', 'sw']:  # Store
            rs2 = get_register_number(parts[1])
            offset_str, base_reg = parts[2].split('(', 1)
            base_reg = base_reg.rstrip(')')
            imm = check_immediate_bounds(offset_str, 12)
            rs1 = get_register_number(base_reg)
            return encode_s_type(opcode, rs2, rs1, imm)

        elif opcode in ['beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu']:  # B-type (Branch)
            rs1 = get_register_number(parts[1])
            rs2 = get_register_number(parts[2])
            imm = labels[parts[3]] - current_address if parts[3] in labels else check_immediate_bounds(parts[3], 13)
            return encode_b_type(opcode, rs1, rs2, imm)

        elif opcode in ['lui', 'auipc']:  # U-type
            rd = get_register_number(parts[1])
            imm = check_immediate_bounds(parts[2], 20)
            return encode_u_type(opcode, rd, imm)

        elif opcode == 'jal':  # J-type
            rd = get_register_number(parts[1])
            imm = labels[parts[2]] - current_address if parts[2] in labels else check_immediate_bounds(parts[2], 21)
            return encode_j_type(opcode, rd, imm)

        elif opcode == 'jalr':  # JALR (special case of I-type)
            rd = get_register_number(parts[1])
            rs1 = get_register_number(parts[2])
            imm = check_immediate_bounds(parts[3], 12)
            return encode_i_type(opcode, rd, rs1, imm)

        else:
            raise ValueError(f"Unknown instruction {opcode}")

    except Exception as e:
        raise ValueError(f"Error encoding {opcode}: {str(e)}")

# Reads an assembly file, extracts labels & encodes each instruction

def assemble_file(input_file, output_file):
    labels, current_address = {}, 0
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    for line in lines:
        if ':' in line:
            labels[line.split(':')[0].strip()] = current_address
        current_address += 4
    binary_instructions, current_address = [], 0
    for i, line in enumerate(lines, 1):
        if ':' in line:
            line = line.split(':', 1)[1].strip()
            if not line:
                continue
        parts = line.replace(',', ' ').split()
        binary = encode_instruction(parts, current_address, labels)
        binary_instructions.append(binary)
        current_address += 4
    with open(output_file, 'w') as f:
        f.writelines(f"{instr}\n" for instr in binary_instructions)

def main():
    input_file, output_file = input("Input file: "), input("Output file: ")
    try:
        assemble_file(input_file, output_file)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
