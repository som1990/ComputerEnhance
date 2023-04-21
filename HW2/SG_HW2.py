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
# MOV instruction Codes
op_table["MOV"] = [0b1011, 0b100010, 0b1100011, 0b1010000, 0b1010001]



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

def decode_mod(buf:bytes, buff_off:int, mod_code:int, rm_field:int, is_wide:int)->t.Tuple(str, int):
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

def mov_between_mem_and_reg(buf:bytes, buf_off:int)->t.Tuple(str, int):
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
    print("I'm doing mov between memory and register")
    
    new_offset = buf_off 
    buffer = struct.unpack_from('2B', buf, offset=new_offset)
    new_offset += 2

    # Byte 1
    reg_dir = (buffer[0] >> 1) & 1
    is_wide = buffer[0] & 1
    print(f"Byte1: OpCode= {bin(0b100010)} , operation= 'MOV', D= {reg_dir} , W= {is_wide}")
    
    #Byte 2 
    
    src_reg_code = (buffer[1] >> 3) & 0b111
    src_decode = reg_field[src_reg_code][is_wide]
    dest_reg_code =(buffer[1]) & 0b111

    mod_code = (buffer[1] >> 6)
    dest_decode, new_offset = decode_mod(buf, new_offset, mod_code, dest_reg_code, is_wide)

    if reg_dir == 1:
        temp = dest_decode
        dest_decode = src_decode
        src_decode = temp
    
    print(f"Byte2: MOD={bin(mod_code)} , Source={src_decode}, Dest={dest_decode}")
    output = f"MOV {dest_decode}, {src_decode}\n"
    return output, new_offset

def mov_immediate_to_reg_or_memory(buf:bytes, buf_off:int)->t.Tuple(str, int):
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
    print(f"MOD={bin(mod_code)} , Source={src_decode}, Dest={dest_decode}")
    output = f"MOV {dest_decode}, {src_decode}\n"
    return output, new_offset

def mov_immediate_to_reg(buf:bytes, buf_off:int)->t.Tuple(str, int):
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

    print(f"Byte2/3: Source={bin(src_decode[0])}({src_decode[0]})")
    output = f"MOV {dest_decode}, {src_decode}\n"
    return output, new_offset

def mov_mem_to_accum(buf:bytes, buf_off:int)->t.Tuple(str, int):
    print("I'm doing mov from memory to accumilator")
    new_offset = buf_off
    buffer = struct.unpack_from('B', buf, offset=new_offset)
    new_offset += 1

    is_wide = (buffer[0]) & 1
    print(f"Byte1: Opcode={bin(0b1010000)}, is_wide={is_wide}")

    dest_decode = "ax"

    byte_code = 'h' if is_wide else 'b'
    byte_offset = 2 if is_wide else 1
    buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
    new_offset += byte_offset
    src_decode = f"[{buffer[0]}]"

    print(f"Source={src_decode}, Dest={dest_decode}")
    output = f"MOV {dest_decode}, {src_decode}\n"
    return output, new_offset

def mov_accum_to_mem(buf:bytes, buf_off:int)->t.Tuple(str, int):
    print("I'm doing mov from accumilator to memory")
    new_offset= buf_off
    buffer = struct.unpack_from('B', buf, offset=new_offset)
    new_offset += 1

    is_wide = (buffer[0]) & 1
    print(f"Byte1: Opcode={bin(0b1010000)}, is_wide={is_wide}")


    src_decode = "ax"

    byte_code = 'h' if is_wide else 'b'
    byte_offset = 2 if is_wide else 1
    buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
    new_offset += byte_offset
    dest_decode = f"[{buffer[0]}]"
    print(f"Source={src_decode}, Dest={dest_decode}")
    output = f"MOV {dest_decode}, {src_decode}\n"
    return output, new_offset
    

op_funcs = dict()
op_funcs[0b1011] = mov_immediate_to_reg
op_funcs[0b100010] = mov_between_mem_and_reg
op_funcs[0b1100011] = mov_immediate_to_reg_or_memory
op_funcs[0b1010000] = mov_mem_to_accum
op_funcs[0b1010001] = mov_accum_to_mem 

def decode_opcode(buf:bytes):
    decoded_func = None
    for i in range(6):
        temp_code = buf>>(5-i)
        if temp_code in op_funcs:
            decoded_func = op_funcs[temp_code]

    return decoded_func


def disassemble_CPU8086(bin_path: str, out_path : t.Optional[str] = None) -> str:
    
    out_path = out_path or bin_path + '_out.asm'
    bin_data = b''
    with open(bin_path, "rb") as f:
        bin_data = f.read()
    filename = Path(bin_path).stem
    out_file = f"; {filename}\n"
    out_file += "bits 16\n"
    buff_off = 0
    count = 1
    while (count < 10):
        # unpacking as Unsigned char array for easier calculation.
        buffer = struct.unpack_from('2B', bin_data, offset=buff_off)
        
        # 1st Byte 
        
        # Looking for 4 bit opdata
        m_byte_1 = buffer[0]
        
        opcode_func = decode_opcode(m_byte_1)

        if opcode_func == None:
            raise ReferenceError("opcode not recognized or implemented")
            
        
        output, buff_off = opcode_func(bin_data, buff_off)
        out_file += output
        #count += 1

        if buff_off >= len(bin_data):
            break

    with open(out_path, 'w') as ofh:
        ofh.write(out_file)



path = r"D:\Work\Courses\ComputerEnhance\HW2\HW_Lst_40"
#path = r"D:\Work\Courses\ComputerEnhance\HW1\HW_Lst_38_MultipleInstructions"
out_path = path + '_out.asm'
disassemble_CPU8086(path, out_path)

#opcode = 0b10001010

#print(decode_opcode(opcode))