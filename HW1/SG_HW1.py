from __future__ import annotations
import struct
import typing as t
from pathlib import Path

"""
Typical 8086/8088 Machine Instruction Format

Byte 1
OPCode                                              - 6 bits
Direction of register (D)                           - 1 bit
is wide format (W)                                  - 1 bit

Byte 2
Register/Memory Mode (MOD)                          - 2 bits
Register Operand extension of OPCode (REG)          - 3 bits
Register Operand Register to use in EA calcs (R/M)  - 3 bits

"""

# OP Tables
op_datas = [0b100010]

op_table = dict()
op_table[0b100010] = "MOV"

# Registry Tables
reg_field = dict()
reg_field[0b000] = ['AL', 'AX']
reg_field[0b001] = ['CL', 'CX']
reg_field[0b010] = ['DL', 'DX']
reg_field[0b011] = ['BL', 'BX']
reg_field[0b100] = ['AH', 'SP']
reg_field[0b101] = ['CH', 'BP']
reg_field[0b110] = ['DH', 'SI']
reg_field[0b111] = ['BH', 'DI']

# mod table
mod_table = dict()
mod_table[0b11] = reg_field 

def disassemble_CPU8086(bin_path: str, out_path : t.Optional[str] = None) -> str:
    
    out_path = out_path or bin_path + '_out.asm'
    bin_data = b''
    with open(bin_path, "rb") as f:
        bin_data = f.read()
    filename = Path(bin_path).stem
    out_file = f"; {filename}\n"
    out_file += "bits 16\n"
    buff_off = 0
    while (1):
        # unpacking as Unsigned char array for easier calculation.
        buffer = struct.unpack_from('2B', bin_data, offset=buff_off)
        
        # 1st Byte 
        op_data = buffer[0] >> 2
        
        if op_data not in op_datas:
            print(f"{bin(op_data)[2:]} code not recognized")
            return
        
        

        reg_dir = (buffer[0] >> 1) & 1
        is_wide = buffer[0] & 1
        print(f"Byte1: OpCode= {bin(op_data)} , operation={op_table[op_data]}, D= {reg_dir} , W= {is_wide}")
        # Byte 2
        reg_mode = (buffer[1] >> 6) 
        if reg_mode not in mod_table:
            print('Register mode not implemented')
            return
        
        reg_table = mod_table[reg_mode]
        src_reg = (buffer[1] >> 3) & 0b111
        src_decode = reg_table[src_reg][is_wide]
        dest_reg =(buffer[1]) & 0b111
        dest_decode = reg_table[dest_reg][is_wide]

        print(f"Byte2: MOD={bin(reg_mode)} , Source={src_decode}, Dest={dest_decode}")
        out_file += op_table[op_data] + ' ' + dest_decode + ', ' + src_decode + '\n'

        # TODO: find a way to calc bin size for each operation to calc correct offset 
        buff_off += 2 # HARDCODED 2 Byte offset each loop

        if buff_off >= len(bin_data):
            break

    with open(out_path, 'w') as ofh:
        ofh.write(out_file)



path = r"D:\Work\Courses\ComputerEnhance\HW_Lst_37_ComputerEnhance"
#path = r"D:\Work\Courses\ComputerEnhance\HW_Lst_38_MultipleInstructions"
out_path = path + '_out.asm'
disassemble_CPU8086(path, out_path)