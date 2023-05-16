"""HW2 for the Performance aware programming course (https://www.computerenhance.com/)

A simple testbed for disassembling 8086 set of instructions. 
Takes in a binary file from the 8086 format and decodes it to relavant x86 assembly code
Referenced from 8086 Family User Manual 

Supported
Decoding complete flavors of : MOV, conditional Jumps, ADD, ADC, SUB, SBB, CMP
Simming of non-memory MOVs. 
 
Author: Soumitra Goswami 
"""

from __future__ import annotations
import struct
import typing as t


from pathlib import Path
from dataclasses import dataclass
import instruction_utils_8086 as utils_8086



# Function tables
op_funcs = dict()
# MOV instruction flavors
op_funcs["0b1011"] = utils_8086.mov_immediate_to_reg
op_funcs["0b100010"] = utils_8086.mov_between_mem_and_reg
op_funcs["0b1100011"] = utils_8086.mov_immediate_to_reg_or_memory
op_funcs["0b1010000"] = utils_8086.mov_mem_to_accum
op_funcs["0b1010001"] = utils_8086.mov_accum_to_mem
op_funcs["0b10001110"] = utils_8086.mov_between_segs_regs_and_memory
op_funcs["0b10001100"] = utils_8086.mov_between_segs_regs_and_memory

# ADD instruction flavors
op_funcs["0b000000"] = utils_8086.add_between_register_memory
op_funcs["0b0000010"] = utils_8086.add_immediate_to_accumulator

# SUB instruction flavors
op_funcs["0b001010"] = utils_8086.sub_between_register_memory
op_funcs["0b0010110"] = utils_8086.sub_immediate_from_accumulator

#CMP instruction flavors
op_funcs["0b001110"] = utils_8086.cmp_between_register_memory
op_funcs["0b0011110"] = utils_8086.cmp_immediate_from_accumulator

# common Arithmetic functions
op_funcs["0b100000"] = utils_8086.arith_immediate_to_register_memory

# JUMP instructions
op_funcs["0b01110100"] = utils_8086.jmp_unconditional
op_funcs["0b01111100"] = utils_8086.jmp_unconditional
op_funcs["0b01111110"] = utils_8086.jmp_unconditional
op_funcs["0b01110010"] = utils_8086.jmp_unconditional
op_funcs["0b01110110"] = utils_8086.jmp_unconditional
op_funcs["0b01111010"] = utils_8086.jmp_unconditional
op_funcs["0b01110000"] = utils_8086.jmp_unconditional
op_funcs["0b01111000"] = utils_8086.jmp_unconditional
op_funcs["0b01110101"] = utils_8086.jmp_unconditional
op_funcs["0b01111101"] = utils_8086.jmp_unconditional
op_funcs["0b01111111"] = utils_8086.jmp_unconditional
op_funcs["0b01110011"] = utils_8086.jmp_unconditional
op_funcs["0b01110111"] = utils_8086.jmp_unconditional
op_funcs["0b01111011"] = utils_8086.jmp_unconditional
op_funcs["0b01110001"] = utils_8086.jmp_unconditional
op_funcs["0b01111001"] = utils_8086.jmp_unconditional
op_funcs["0b11100010"] = utils_8086.jmp_unconditional
op_funcs["0b11100001"] = utils_8086.jmp_unconditional
op_funcs["0b11100000"] = utils_8086.jmp_unconditional
op_funcs["0b11100011"] = utils_8086.jmp_unconditional



def decode_opcode(buf:bytes):
    """Since opcodes vary from 3 bit to 8 bits. A simple way to decode the opcode to it's relevant instructions
    """
    decoded_func = None
    for i in range(6):
        num_bits = 3 + i
        bin_format = f"#0{num_bits+2}b"
        temp_code = format(buf>>(5-i),bin_format)
        if temp_code in op_funcs:
            decoded_func = op_funcs[temp_code]

    if decoded_func == None:
        raise NotImplementedError(f"opcode not recognized or implemented for byte {bin(buf)}")

    return decoded_func

def print_registers(registers:t.List[int])->str:
    lables = ["AX", "BX", "CX", "DX", "SP", "BP", "SI", "DI", "ES", "CS", "SS", "DS"]
    output = "Final Registers: \n"
    for i, reg in enumerate(registers):
        output += f"\t\t{lables[i]}: {reg:#06x} ({reg}) \n"

    return output


 
def disassemble_CPU8086(bin_path: str)->str:
    ''' A simple disassembler of limited 8086 set of instruction
    
    '''
    bin_data = b''
    with open(bin_path, "rb") as f:
        bin_data = f.read()
    filename = Path(bin_path).stem
    out_file = f"; {filename}\n"
    out_file += "bits 16\n"
    buff_off = 0
    count = 1
    out_op_text = f"; {filename}\n"

    myLayout = utils_8086.MemoryLayout8086(registers=12*[0], flags=0b0)

    while (count > -1):
        # unpacking as Unsigned char array for easier calculation.
        buffer = struct.unpack_from('2B', bin_data, offset=buff_off)
        
        # 1st Byte 
        
        # Looking for 4 bit opdata
        m_byte_1 = buffer[0]
        
        try:
            opcode_func = decode_opcode(m_byte_1)
            output, buff_off, sim_out = opcode_func(bin_data, buff_off, myLayout)
            out_file += str(output) + '\n'
            out_op_text += sim_out
            print(sim_out)
        except NotImplementedError as e:
            print(f"NotImplementedError: {e}")
            break
        except TypeError as e:
            print(f"'{opcode_func.__name__}' function is not fleshed out yet or has an error")
            print(f"TypeError: {e}")
            break
        
        #count += 1

        if buff_off >= len(bin_data):
            break
    print(f"End of Instructions at byte offset: {hex(buff_off)}")

    #Print the final registers
    out_op_text += "\n"
    out_op_text += print_registers(myLayout.registers)
    out_op_text += "Flags: \n" + utils_8086.serialize_flags(myLayout.flags) + '\n'
    return out_file, out_op_text
    
def write_file(out_path: str, output: str):
    with open(out_path, 'w') as ofh:
        ofh.write(output)


import os

dirname = os.path.dirname(__file__)
parent = Path(dirname).parent
path = os.path.join(dirname, 'listing_0046_add_sub_cmp')
#path = os.path.join(dirname, "listing_0047_challenge_flags")
#path =os.path.join(parent,'HW3', 'HW_Lst_42_completionist')
out_path = str(path) + '_out.asm'
output, out_sim = disassemble_CPU8086(path)
out_sim_path = str(path) + '_instructions.txt'
write_file(out_path, output)
write_file(out_sim_path, out_sim)
