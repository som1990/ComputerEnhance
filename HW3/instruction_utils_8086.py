"""
In this module we add support for Arithmetic operators: ADD, SUB and CMP as well as Jump instructions along with most
flavors of the MOV operator.

Author: Soumitra Goswami

"""
from __future__ import annotations
import struct
import typing as t


# Registry Tables
reg_field = [None]*8
reg_field[0b000] = ['AL', 'AX']
reg_field[0b001] = ['CL', 'CX']
reg_field[0b010] = ['DL', 'DX']
reg_field[0b011] = ['BL', 'BX']
reg_field[0b100] = ['AH', 'SP']
reg_field[0b101] = ['CH', 'BP']
reg_field[0b110] = ['DH', 'SI']
reg_field[0b111] = ['BH', 'DI']

# Address Encoding
encode_address = [None]*8
encode_address[0b000] = 'BX + SI'
encode_address[0b001] = 'BX + DI'
encode_address[0b010] = 'BP + SI'
encode_address[0b011] = 'BP + DI'
encode_address[0b100] = 'SI'
encode_address[0b101] = 'DI'
encode_address[0b110] = 'BP'
encode_address[0b111] = 'BX'

# mod table
mod_table = [None]*4
mod_table[0b11] = reg_field
mod_table[0b00] = encode_address
mod_table[0b01] = encode_address
mod_table[0b10] = encode_address

def decode_mod(buf:bytes, buff_off:int, mod_code:int, rm_field:int, is_wide:int)->t.Tuple(str, str, int):
    """Decoding MOD field of the instruction set. 
       Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-20
    """
    new_offset=buff_off
    if mod_code > 3:
            raise KeyError(f"{mod_code} not implemented in mod_table")
    
    reg_table = mod_table[mod_code]
    if mod_code == 0b11:
        decode_str = reg_field[rm_field][is_wide]
    elif (mod_code==0b00 and rm_field!=0b110):
        decode_str = f"[{reg_table[rm_field]}]"
        
    elif mod_code == 0b00 and rm_field == 0b110:
        byte_code = 'h' if is_wide else 'b'
        byte_offset = 2 if is_wide else 1
        buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
        new_offset += byte_offset
        decode_str = f"[{buffer[0]}]"
    else:
        byte_code = 'h' if mod_code==2 else 'b'
        byte_offset = 2 if mod_code==2 else 1
        buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
        new_offset += byte_offset
        val = buffer[0]
        val_str = f'+ {val}' if val>0 else f'- {abs(val)}'
        if val !=0:
            decode_str = f"[{reg_table[rm_field]} {val_str}]"
        else:
            decode_str = f"[{reg_table[rm_field]}]"

    return decode_str, new_offset

def mem_reg_ops(buf:bytes, buf_off:int)->t.Tuple(str, str, int):
    '''
    Byte 1
    OPCode                                              - 6 bits
    Direction of register (D)                           - 1 bit
    is wide format (W)                                  - 1 bit

    Byte 2
    Register/Memory Mode (MOD)                          - 2 bits
    Register Operand extension of OPCode (REG)          - 3 bits
    Register Operand Register to use in EA calcs (R/M)  - 3 bits

    BYTE 3
    DISP-LO ( eg: [bx + si + 4]) or 8 bit direct address (eg: [5]) or Low bits of 16 bit direct address

    BYTE 4 (if wide)
    DISP-HI (eg: [bx + si + 4999]) or High bits 16 bit direct address ( eg: [3458])
    '''
    new_offset = buf_off 
    buffer = struct.unpack_from('2B', buf, offset=new_offset)
    new_offset += 2

    # Byte 1
    reg_dir = (buffer[0] >> 1) & 1
    is_wide = buffer[0] & 1
    
    
    #Byte 2 
    
    src_reg_code = (buffer[1] >> 3) & 0b111
    src_decode = reg_field[src_reg_code][is_wide]
    dest_reg_code =(buffer[1]) & 0b111

    mod_code = (buffer[1] >> 6)
    print(f"D= {reg_dir} , W= {is_wide} MOD= {bin(mod_code)}")
    dest_decode, new_offset = decode_mod(buf, new_offset, mod_code, dest_reg_code, is_wide)

    if reg_dir == 1:
        temp = dest_decode
        dest_decode = src_decode
        src_decode = temp

    return dest_decode, src_decode, new_offset

def trans_between_immediate_and_accumulator(buf:bytes, buf_off:int, is_memory:bool=False)->t.Tuple(str, str, int):
    '''
    BYTE 1
    OP_CODE(1010000)                                7 bits
    is wide (W)                                     1 bit

    BYTE 2/3
    address                                         8 or 16 bits

    '''
    new_offset = buf_off
    buffer = struct.unpack_from('B', buf, offset=new_offset)
    new_offset += 1

    is_wide = (buffer[0]) & 1
    is_accum_to_mem = (buffer[0]>>1) & 1
    print(f"is_wide={is_wide}")

    dest_decode = reg_field[0b000][is_wide]

    byte_code = 'h' if is_wide else 'b'
    byte_offset = 2 if is_wide else 1
    buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
    new_offset += byte_offset
    src_decode = f"[{buffer[0]}]" if is_memory else f"{buffer[0]}"

    if is_accum_to_mem == 1:
        temp_decode = dest_decode
        dest_decode = src_decode
        src_decode = temp_decode
    print(f"Dest={dest_decode}, Source={src_decode}")
    return dest_decode, src_decode, new_offset


# INSTRUCTION SETS 
def mov_between_mem_and_reg(buf:bytes, buf_off:int)->t.Tuple(str, int):
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    print("I'm doing mov between memory and register")
    print(f"Byte1: OpCode= {bin(0b100010)} , operation= 'MOV'")
    new_offset = buf_off
    dest_decode,src_decode, new_offset = mem_reg_ops(buf, new_offset)
    
    print(f"Dest={dest_decode}, Source={src_decode}")
    output = f"MOV {dest_decode}, {src_decode}\n"
    return output, new_offset

def mov_immediate_to_reg_or_memory(buf:bytes, buf_off:int)->t.Tuple(str, int):
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    '''
    BYTE 1
    OP_CODE (1100011)                                   - 7 bits
    is_wide (w)                                         - 1 bit

    BYTE 2
    MOD                                                 - 2 bits
    000                                                 - 3 bits
    Register Operand Register to use in EA calcs (R/M)  - 3 bits

    BYTE 3
    DISP-LO
    
    BYTE 4 
    DISP-HI

    BYTE 5/6
    Data(8 or 16 if wide)

    '''
    print("I'm doing mov from immediate to memory or register")
    new_offset = buf_off 
    buffer = struct.unpack_from('2B', buf, offset=new_offset)
    new_offset += 2

    is_wide = buffer[0] & 1
    print(f"Byte1: Opcode={bin(0b1011)}, is_wide={is_wide}")
    
    mod_code = buffer[1] >> 6
    rm_code = buffer[1] & 0b111
    dest_decode, new_offset = decode_mod(buf, new_offset, mod_code, rm_code, is_wide)
    
    src_type = "word" if is_wide else "byte"
    byte_code = "h" if is_wide else "b"
    byte_offset = 2 if is_wide else 1

    buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
    new_offset += byte_offset
    src_decode = f"{src_type} {buffer[0]}"
    print(f"MOD={bin(mod_code)}, Dest={dest_decode}, Source={src_decode}")
    output = f"MOV {dest_decode}, {src_decode}\n"
    return output, new_offset

def mov_immediate_to_reg(buf:bytes, buf_off:int)->t.Tuple(str, int):
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    '''
    BYTE 1
    OP_CODE (1011)                                  - 4 bits
    is wide format (w)                              - 1 bit
    Register Operand extension of OPCode (REG)      - 3 bits

    BYTE 2
    Data                                            - 8 bits

    BYTE 3
    Data (if wide)                                  - 8 bits
    '''
    print("I'm doing mov from immediate to register")
    new_offset = buf_off 
    buffer = struct.unpack_from('B', buf, offset=new_offset)
    new_offset += 1
    
    is_wide = (buffer[0] >> 3) & 1
    dest_reg_code = (buffer[0]) & 0b111
    dest_decode = reg_field[dest_reg_code][is_wide]
    print(f"Byte1: Opcode={bin(0b1011)}, is_wide={is_wide}, reg={bin(dest_reg_code)}")

    byte_code = 'h' if is_wide else 'b'
    byte_offset = 2 if is_wide else 1
    src_decode = struct.unpack_from(byte_code, buf, offset=new_offset)
    new_offset += byte_offset

    print(f"Byte2/3: Dest={dest_decode}, Source={bin(src_decode[0])}({src_decode[0]})")
    output = f"MOV {dest_decode}, {src_decode[0]}\n"
    return output, new_offset

def mov_mem_to_accum(buf:bytes, buf_off:int)->t.Tuple(str, int):
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    
    print(f"I'm doing mov from memory to accumilator : OPCODE= {1010000}")
    new_offset = buf_off
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, buf_off, is_memory=True)

    output = f"MOV {dest_decode}, {src_decode}\n"
    return output, new_offset

def mov_accum_to_mem(buf:bytes, buf_off:int)->t.Tuple(str, int):
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    print(f"I'm doing mov from accumilator to memory. OPCODE: {1010001}")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, buf_off,is_memory=True)

    output = f"MOV {dest_decode}, {src_decode}\n"
    return output, new_offset


# ARITHMETIC INSTRUCTIONS
arith_opcodes = dict()
arith_opcodes[0b000] = {"decode" : "ADD", "desc": "I'm doing an add with carry. Flavor : Immediate to register/memory"}
arith_opcodes[0b010] = {"decode" : "ADC", "desc": "I'm doing an add with carry. Flavor : Immediate to register/memory"}
arith_opcodes[0b101] = {"decode" : "SUB", "desc": "I'm doing an sub. Flavor : Immediate from register/memory"}
arith_opcodes[0b011] = {"decode" : "SBB", "desc": "I'm doing an subtract with borrow. Flavor : Immediate from register/memory"}
arith_opcodes[0b111] = {"decode" : "CMP", "desc": "I'm doing a compare. Flavor : Immediate from register/memory"}


def arith_immediate_to_register_memory(buf:bytes, buf_off:int)->t.Tuple(str,int):
    '''
    Byte 1
    OPCode(100000)                                          - 6 bits
    Sign extend 8bit immediate data to 16 bit (S) if W=1    - 1 bit
    is wide format (W)                                      - 1 bit

    Byte 2
    Register/Memory Mode (MOD)                              - 2 bits
    is with carry (ADC or ADD)                              - 3 bits
    Register Operand Register to use in EA calcs (R/M)      - 3 bits

    BYTE 3
    DISP-LO ( eg: [bx + si + 4]) or 8 bit direct address (eg: [5]) or Low bits of 16 bit direct address

    BYTE 4 (if wide)
    DISP-HI (eg: [bx + si + 4999]) or High bits 16 bit direct address ( eg: [3458])

    BYTE 5/6
    data                                                    - 8 or 16 bits

    '''
    new_offset= buf_off
    buffer = struct.unpack_from('2B', buf, offset=new_offset)
    new_offset += 2

    is_wide = buffer[0] & 1
    is_sign = (buffer[0] >> 1) & 1

    rm_code = buffer[1] & 0b111
    arith_opcode = ((buffer[1] >> 3) & 0b111) 
    mod_code = (buffer[1] >> 6) & 0b11
    if arith_opcode not in arith_opcodes:
        raise NotImplementedError("This arithmetic operation for immediate to register is not implemented yet.")
    instruction = arith_opcodes[arith_opcode]["decode"]

    print(arith_opcodes[arith_opcode]["desc"])
    print(f"Byte1: OpCode= {bin(0b100000)} , operation= {instruction}, S= {is_sign} , W= {is_wide}")
    dest_decode, new_offset = decode_mod(buf, new_offset, mod_code, rm_code, is_wide)

    byte_code = 'h' if (is_wide and is_sign == 0) else 'b'
    byte_offset = 2 if (is_wide and is_sign == 0) else 1
    buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
    new_offset += byte_offset
    src_decode = f"{buffer[0]}"

    byte_type = "word" if is_wide else "byte"
    if mod_code != 0b11 :
        dest_decode = f"{byte_type} {dest_decode}"

    print(f"mod={bin(mod_code)}, Dest={dest_decode}, Source={src_decode}")
    output = f"{instruction} {dest_decode}, {src_decode}\n"
    
    return output, new_offset


def add_between_register_memory(buf:bytes, buf_off:int)->t.Tuple(str, int):
    print(f"I'm doing an add flavor : reg/memory with register to either. OPCODE:{000000}")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = mem_reg_ops(buf, new_offset)
    print(f" Dest={dest_decode}, Source={src_decode}")
    output = f"ADD {dest_decode}, {src_decode}\n"

    return output, new_offset


def add_immediate_to_accumulator(buf:bytes, buf_off:int)->t.Tuple(str, int):
    print(f"I'm doing an add flavor : Immediate to accumilator. OPCODE:{bin(0b000010)}")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, new_offset)

    output = f"ADD {dest_decode}, {src_decode}\n"

    return output, new_offset


def sub_between_register_memory(buf:bytes, buf_off:int)->t.Tuple(str, int):
    print("I'm doing an sub flavor : reg/memory with register to either")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = mem_reg_ops(buf, new_offset)

    print(f" Dest={dest_decode}, Source={src_decode}")
    output = f"SUB {dest_decode}, {src_decode}\n"

    return output, new_offset


def sub_immediate_from_accumulator(buf:bytes, buf_off:int)->t.Tuple(str, int): 
    print(f"I'm doing an sub flavor : Immediate from accumilator.{bin(0b0010110)}")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, new_offset)
    
    print(f" Dest={dest_decode}, Source={src_decode}")
    output = f"SUB {dest_decode}, {src_decode}\n"

    return output, new_offset


def cmp_between_register_memory(buf:bytes, buf_off:int)->t.Tuple(str, int):
    print(f"I'm doing an cmp flavor : reg/memory with register to either. {bin(0b001110)}")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = mem_reg_ops(buf, new_offset)

    print(f" Dest={dest_decode}, Source={src_decode}")
    output = f"CMP {dest_decode}, {src_decode}\n"

    return output, new_offset


def cmp_immediate_from_accumulator(buf:bytes, buf_off:int)->t.Tuple(str, int):
    print(f"I'm doing an cmp flavor : Immediate from accumilator.{bin(0b0010110)}")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, new_offset)
    
    print(f"Dest={dest_decode}, Source={src_decode}")
    output = f"CMP {dest_decode}, {src_decode}\n"

    return output, new_offset


# JUMP instructions
jump_opcodes = dict()
jump_opcodes[0b01110100] = "JE"
jump_opcodes[0b01111100] = "JL"
jump_opcodes[0b01111110] = "JLE"
jump_opcodes[0b01110010] = "JB"
jump_opcodes[0b01110110] = "JBE"
jump_opcodes[0b01111010] = "JP"
jump_opcodes[0b01110000] = "JO"
jump_opcodes[0b01111000] = "JS"
jump_opcodes[0b01110101] = "JNE"
jump_opcodes[0b01111101] = "JNL"
jump_opcodes[0b01111111] = "JNLE"
jump_opcodes[0b01110011] = "JNB"
jump_opcodes[0b01110111] = "JNBE"
jump_opcodes[0b01111011] = "JNP"
jump_opcodes[0b01110001] = "JNO"
jump_opcodes[0b01111001] = "JNS"
jump_opcodes[0b11100010] = "LOOP"
jump_opcodes[0b11100001] = "LOOPZ"
jump_opcodes[0b11100000] = "LOOPNZ"
jump_opcodes[0b11100011] = "JCXZ"


def jmp_unconditional(buf:bytes, buf_off:int)->t.Tuple(str, int):
    '''
    Byte 1
    Jump OpCode                                             - 8 bits

    Byte 2
    DISP                                                    - 8 bits
    '''
    print("I'm doing a conditional jump")
    new_offset= buf_off
    buffer = struct.unpack_from('B', buf, offset=new_offset)
    new_offset += 1

    opcode = buffer[0]
    operation_decode = jump_opcodes[opcode]
    
    buffer = struct.unpack_from('b', buf, offset=new_offset)
    new_offset +=1

    disp = buffer[0] + 2
    disp_str = f"{disp}"
    if disp > 0:
        disp_str = f"+{disp}"
    elif disp == 0:
        disp_str = f"+0"
    print(f"jump operation: {operation_decode}, displacement={disp_str}")
    output = f"{operation_decode} ${disp_str} \n"

    return output, new_offset

