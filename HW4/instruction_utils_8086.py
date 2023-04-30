"""
Supported:
Decoding complete flavors of : MOV, conditional Jumps, ADD, ADC, SUB, SBB, CMP
Simming of non-memory MOVs.

In this module we added Simming of non-memory MOV operations. We refactored the code to 
pass along data structs. We maintain the instruction class for easy access this way. 

Author: Soumitra Goswami

"""
from __future__ import annotations
import struct
import typing as t
from dataclasses import dataclass


@dataclass(frozen=True)
class Address():
    val: t.Any
    is_register: t.Optional[bool] = False
    is_memory: t.Optional[bool] = False 
    is_wide: t.Optional[bool] = True

    def __str__(self):
        if self.is_memory:
            return f"[{self.val}]"
        return f"{self.val}"
    
    @property
    def flags(self):
        f_val = 0
        f_val |= int(self.is_register) # encode register flag
        f_val |= (int(self.is_memory) << 1) # encode memory flag
        return f_val

    @property
    def is_immediate(self):
        return self.flags == 0
    
        
@dataclass (frozen=True)
class Instruction():
    memonic: str
    src: t.Optional[Address] = None
    dest: t.Optional[Address] = None

    def __str__(self):
        if self.src is None and self.dest is None:
            return f"{self.memonic}"
        
        elif self.src is None:
            return f"{self.memonic} {self.dest}"

        if self.src.is_immediate and self.dest.is_memory:
            src_dtype = "word" if self.src.is_wide else "byte"
            return f"{self.memonic} {src_dtype} {self.dest}, {self.src}"
        return f"{self.memonic} {self.dest}, {self.src}"


# simulation
register_lables = dict()
register_lables['AX'] = {"pos": 0, "bytes": 2, "is_high" : 0 }
register_lables['AL'] = {"pos": 0, "bytes": 1, "is_high" : 0 }
register_lables['AH'] = {"pos": 0, "bytes": 1, "is_high" : 1 }
register_lables['BX'] = {"pos": 1, "bytes": 2, "is_high" : 0 }
register_lables['BL'] = {"pos": 1, "bytes": 1, "is_high" : 0 }
register_lables['BH'] = {"pos": 1, "bytes": 1, "is_high" : 1 }
register_lables['CX'] = {"pos": 2, "bytes": 2, "is_high" : 0 }
register_lables['CL'] = {"pos": 2, "bytes": 1, "is_high" : 0 }
register_lables['CH'] = {"pos": 2, "bytes": 1, "is_high" : 1 }
register_lables['DX'] = {"pos": 3, "bytes": 2, "is_high" : 0 }
register_lables['DL'] = {"pos": 3, "bytes": 1, "is_high" : 0 }
register_lables['DH'] = {"pos": 3, "bytes": 1, "is_high" : 1 }
register_lables['SP'] = {"pos": 4, "bytes": 2, "is_high" : 0 }
register_lables['BP'] = {"pos": 5, "bytes": 2, "is_high" : 0 }
register_lables['SI'] = {"pos": 6, "bytes": 2, "is_high" : 0 }
register_lables['DI'] = {"pos": 7, "bytes": 2, "is_high" : 0 }
# segment registers
register_lables["ES"] = {"pos": 8, "bytes": 2, "is_high" : 0}
register_lables["CS"] = {"pos": 9, "bytes": 2, "is_high" : 0}
register_lables["SS"] = {"pos": 10, "bytes": 2, "is_high" : 0}
register_lables["DS"] = {"pos": 11, "bytes": 2, "is_high" : 0}

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

seg_reg_field = dict()
seg_reg_field[0b00] = 'ES'
seg_reg_field[0b01] = 'CS'
seg_reg_field[0b10] = 'SS'
seg_reg_field[0b11] = 'DS'


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


def decode_mod(buf:bytes, buff_off:int, mod_code:int, rm_field:int, is_wide:int)->t.Tuple(Address, Address, int):
    """Decoding MOD field of the instruction set. 
       Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-20
    """
    new_offset=buff_off
    if mod_code > 3:
            raise KeyError(f"{mod_code} incorrect. Mod code needs to be 2 bits")
    
    if mod_code == 0b11:
        decode_str = Address(reg_field[rm_field][is_wide], is_register=True, is_wide=(is_wide==1))
    elif (mod_code==0b00 and rm_field!=0b110):
        decode_str = Address(encode_address[rm_field], is_memory=True, is_wide=(is_wide==1)) 
        
    elif mod_code == 0b00 and rm_field == 0b110:
        byte_code = 'h' if is_wide else 'b'
        byte_offset = 2 if is_wide else 1
        buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
        new_offset += byte_offset
        decode_str = Address(buffer[0], is_memory=True, is_wide=(is_wide==1))
    else:
        byte_code = 'h' if mod_code==2 else 'b'
        byte_offset = 2 if mod_code==2 else 1
        buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
        new_offset += byte_offset
        val = buffer[0]
        val_str = f'+ {val}' if val>0 else f'- {abs(val)}'
        if val !=0:
            decode_str = Address(f"{encode_address[rm_field]} {val_str}", is_memory=True, is_wide=(is_wide==1)) # This needs to change when simulating memory 
        else:
            decode_str = Address(encode_address[rm_field], is_memory=True, is_wide=(is_wide==1))

    return decode_str, new_offset

def mem_reg_ops(buf:bytes, buf_off:int)->t.Tuple(Address, Address, int):
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
    src_decode = Address(reg_field[src_reg_code][is_wide], is_register=True, is_wide=(is_wide==1))
    
    dest_reg_code =(buffer[1]) & 0b111
    mod_code = (buffer[1] >> 6)
    print(f"D= {reg_dir} , W= {is_wide} MOD= {bin(mod_code)}")
    dest_decode, new_offset = decode_mod(buf, new_offset, mod_code, dest_reg_code, is_wide)

    if reg_dir == 1:
        temp = dest_decode
        dest_decode = src_decode
        src_decode = temp
    
    return dest_decode, src_decode, new_offset

def trans_between_immediate_and_accumulator(buf:bytes, buf_off:int, is_memory:bool=False)->t.Tuple(Address, Address, int):
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

    dest_decode = Address(reg_field[0b000][is_wide], is_register=True)

    byte_code = 'h' if is_wide else 'b'
    byte_offset = 2 if is_wide else 1
    buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
    new_offset += byte_offset
    src_decode = Address(buffer[0], is_memory=is_memory, is_wide=(is_wide==1))

    if is_accum_to_mem == 1:
        temp_decode = dest_decode
        dest_decode = src_decode
        src_decode = temp_decode
    
    print(f"Dest={dest_decode}, Source={src_decode}")
    return dest_decode, src_decode, new_offset

def mov_between_segs_regs_and_memory(buf:bytes, buf_off:int, regs:t.List[int]=None)->t.Tuple(Address, Address, int):
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    new_offset = buf_off
    buffer = struct.unpack_from('2B', buf, offset=new_offset)
    new_offset += 2
    is_wide = 1

    is_to_segment_regs = (buffer[0] >> 1) & 1
    if is_to_segment_regs:
        print("I'm doing a mov from memory/register to segment register")
    else:
        print("I'm doing a mov from segment register to memory/register") 

    seg_reg_code = (buffer[1] >> 3) & 0b11
    src_decode = Address(seg_reg_field[seg_reg_code], is_register=True, is_wide=True) 
    
    reg_code =(buffer[1]) & 0b111
    mod_code = (buffer[1] >> 6)
    print(f"MOD= {bin(mod_code)}")
    dest_decode, new_offset = decode_mod(buf, new_offset, mod_code, reg_code, is_wide)

    if is_to_segment_regs:
        temp = dest_decode
        dest_decode = src_decode
        src_decode = temp
    
    output = Instruction("MOV", src_decode, dest_decode)

    #Simming
    if src_decode.is_memory or dest_decode.is_memory:
        return output, new_offset, str(output)
    
    src_reg = register_lables[src_decode.val] 
    src_val = regs[src_reg['pos']] 
    dest_reg = register_lables[dest_decode.val]
    
    old_reg_val = regs[dest_reg['pos']]
    regs[dest_reg['pos']] = src_val
    sim_out = f"{output} ; {dest_decode}:{old_reg_val:#06x}->{regs[dest_reg['pos']]:#06x} \n"
    print(sim_out)
    return output, new_offset, sim_out

    

# INSTRUCTION SETS 
def mov_between_mem_and_reg(buf:bytes, buf_off:int, regs:t.List[int]=None)->t.Tuple(Instruction, int, str):
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    m_regs = regs or []
    print("I'm doing mov between memory and register")
    print(f"Byte1: OpCode= {bin(0b100010)} , operation= 'MOV'")
    new_offset = buf_off
    dest_decode,src_decode, new_offset = mem_reg_ops(buf, new_offset)
    
    print(f"Dest={dest_decode}, Source={src_decode}")
    output = Instruction("MOV", src_decode, dest_decode)

    # Siming
    # TODO: Simulation of memory needs to be implemented
    if src_decode.is_memory or dest_decode.is_memory:
        return output, new_offset, str(output)
    

    src_reg = register_lables[src_decode.val] 
    src_val = regs[src_reg['pos']]
    src_nbytes = src_reg['bytes']
    src_is_high = src_reg['is_high']
    if src_nbytes == 1:
        src_val = (src_val)>> 8 if src_is_high else (src_val & 0x00ff)
        
    dest_reg = register_lables[dest_decode.val]
    old_reg_val = regs[dest_reg['pos']]
    dest_nbytes = dest_reg["bytes"]
    dest_is_high = dest_reg["is_high"]
    if dest_nbytes == 2: 
        regs[dest_reg['pos']] = src_val
    else:
        bit_mask = 0xff00 if dest_is_high else 0x00ff
        src_val = src_val << 8 if dest_is_high else src_val
        regs[dest_reg['pos']] = (old_reg_val & ~(bit_mask))  + (src_val & bit_mask)
    
    sim_out = f"{output} ; {dest_decode}:{old_reg_val:#06x}->{regs[dest_reg['pos']]:#06x} \n"
    print(sim_out)
    return output, new_offset, sim_out

def mov_immediate_to_reg_or_memory(buf:bytes, buf_off:int, regs:t.List[int]=None)->t.Tuple(Instruction, int, str):
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
    m_regs = regs or []
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
    src_decode = Address(buffer[0], is_wide=(is_wide==1))
    print(f"MOD={bin(mod_code)}, Dest={dest_decode}, Source={src_decode}")
    output = Instruction("MOV", src_decode, dest_decode)
    sim_out = ""
    return output, new_offset, sim_out

def mov_immediate_to_reg(buf:bytes, buf_off:int, regs:t.List[int]=None)->t.Tuple(Instruction, int, str):
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
    m_regs = regs or []
    print("I'm doing mov from immediate to register")
    # Decoding
    new_offset = buf_off 
    buffer = struct.unpack_from('B', buf, offset=new_offset)
    new_offset += 1
    
    is_wide = (buffer[0] >> 3) & 1
    dest_reg_code = (buffer[0]) & 0b111
    dest_decode = Address(reg_field[dest_reg_code][is_wide], is_register=True, is_wide=(is_wide==1))
    print(f"Byte1: Opcode={bin(0b1011)}, is_wide={is_wide}, reg={bin(dest_reg_code)}")

    byte_code = 'h' if is_wide else 'b'
    byte_offset = 2 if is_wide else 1
    buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
    new_offset += byte_offset
    src_decode = Address(buffer[0], is_wide=(is_wide==1))
    print(f"Byte2/3: Dest={dest_decode}, Source={bin(src_decode.val)}({src_decode.val})")
    output = Instruction("MOV", src_decode, dest_decode)
    
    # Simming
    dest_reg = register_lables[dest_decode.val]
    old_reg_value = regs[dest_reg['pos']]
    dest_nbytes = dest_reg["bytes"]
    dest_is_high = dest_reg["is_high"]
    sim_out=""
    src_val = src_decode.val
    if dest_nbytes == 2:
        regs[dest_reg['pos']] = src_val
        
    else:    
        bit_mask = 0xff00 if dest_is_high else 0x00ff
        src_val = src_val << 8 if dest_is_high else src_val
        regs[dest_reg['pos']] = (old_reg_value & ~(bit_mask))  + (src_val & bit_mask)
        
    sim_out = f"{output} ; {dest_decode}:{old_reg_value:#06x}->{regs[dest_reg['pos']]:#06x} \n"
    print(sim_out) 
    return output, new_offset, sim_out


def mov_mem_to_accum(buf:bytes, buf_off:int, regs:t.List[int]=None)->t.Tuple(Instruction, int, str):
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    m_regs = regs or []
    print(f"I'm doing mov from memory to accumilator : OPCODE= {1010000}")
    new_offset = buf_off
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, buf_off, is_memory=True)

    output = Instruction("MOV", src_decode, dest_decode)
    sim_out = ""
    return output, new_offset, sim_out


def mov_accum_to_mem(buf:bytes, buf_off:int, regs:t.List[int]=None)->t.Tuple(Instruction, int, str):
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    m_regs = regs or []
    print(f"I'm doing mov from accumilator to memory. OPCODE: {1010001}")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, buf_off,is_memory=True)

    output = Instruction("MOV", src_decode, dest_decode)
    sim_out = ""
    return output, new_offset, sim_out


# ARITHMETIC INSTRUCTIONS
arith_opcodes = dict()
arith_opcodes[0b000] = {"decode" : "ADD", "desc": "I'm doing an add with carry. Flavor : Immediate to register/memory"}
arith_opcodes[0b010] = {"decode" : "ADC", "desc": "I'm doing an add with carry. Flavor : Immediate to register/memory"}
arith_opcodes[0b101] = {"decode" : "SUB", "desc": "I'm doing an sub. Flavor : Immediate from register/memory"}
arith_opcodes[0b011] = {"decode" : "SBB", "desc": "I'm doing an subtract with borrow. Flavor : Immediate from register/memory"}
arith_opcodes[0b111] = {"decode" : "CMP", "desc": "I'm doing a compare. Flavor : Immediate from register/memory"}


def arith_immediate_to_register_memory(buf:bytes, buf_off:int,regs:t.List[int]=None)->t.Tuple(str,int):
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
    memonic = arith_opcodes[arith_opcode]["decode"]

    print(arith_opcodes[arith_opcode]["desc"])
    print(f"Byte1: OpCode= {bin(0b100000)} , operation= {memonic}, S= {is_sign} , W= {is_wide}")
    dest_decode, new_offset = decode_mod(buf, new_offset, mod_code, rm_code, is_wide)

    byte_code = 'h' if (is_wide and is_sign == 0) else 'b'
    byte_offset = 2 if (is_wide and is_sign == 0) else 1
    buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
    new_offset += byte_offset
    src_decode = Address(buffer[0], is_wide=(is_wide==1))
 
    byte_type = "word" if is_wide else "byte"

    print(f"mod={bin(mod_code)}, Dest={dest_decode}, Source={src_decode}")
    output = Instruction(memonic, src_decode, dest_decode)
    sim_out = ""
    return output, new_offset, sim_out


def add_between_register_memory(buf:bytes, buf_off:int,regs:t.List[int]=None)->t.Tuple(str, int):
    print(f"I'm doing an add flavor : reg/memory with register to either. OPCODE:{000000}")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = mem_reg_ops(buf, new_offset)
    print(f" Dest={dest_decode}, Source={src_decode}")
    output = Instruction("ADD", src_decode, dest_decode)

    return output, new_offset, ""


def add_immediate_to_accumulator(buf:bytes, buf_off:int,regs:t.List[int]=None)->t.Tuple(str, int):
    print(f"I'm doing an add flavor : Immediate to accumilator. OPCODE:{bin(0b000010)}")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, new_offset)

    output = Instruction("ADD", src_decode, dest_decode)

    return output, new_offset, ""


def sub_between_register_memory(buf:bytes, buf_off:int,regs:t.List[int]=None)->t.Tuple(str, int):
    print("I'm doing an sub flavor : reg/memory with register to either")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = mem_reg_ops(buf, new_offset)

    print(f" Dest={dest_decode}, Source={src_decode}")
    output = Instruction("SUB", src_decode, dest_decode)

    return output, new_offset, ""


def sub_immediate_from_accumulator(buf:bytes, buf_off:int, regs:t.List[int]=None)->t.Tuple(str, int): 
    print(f"I'm doing an sub flavor : Immediate from accumilator.{bin(0b0010110)}")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, new_offset)
    
    print(f" Dest={dest_decode}, Source={src_decode}")
    output = Instruction("SUB", src_decode, dest_decode)

    return output, new_offset, ""


def cmp_between_register_memory(buf:bytes, buf_off:int, regs:t.List[int]=None)->t.Tuple(str, int):
    print(f"I'm doing an cmp flavor : reg/memory with register to either. {bin(0b001110)}")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = mem_reg_ops(buf, new_offset)

    print(f" Dest={dest_decode}, Source={src_decode}")
    output = Instruction("CMP", src_decode, dest_decode)

    return output, new_offset, ""


def cmp_immediate_from_accumulator(buf:bytes, buf_off:int, regs:t.List[int]=None)->t.Tuple(str, int):
    print(f"I'm doing an cmp flavor : Immediate from accumilator.{bin(0b0010110)}")
    new_offset= buf_off
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, new_offset)
    
    print(f"Dest={dest_decode}, Source={src_decode}")
    output = Instruction("CMP", src_decode, dest_decode)

    return output, new_offset, ""


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


def jmp_unconditional(buf:bytes, buf_off:int, regs:t.List[int]=None)->t.Tuple(str, int):
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
    dest_decode = Address(f"${disp_str}", is_wide=False)
    print(f"jump operation: {operation_decode}, displacement={disp_str}")
    output = Instruction(operation_decode, dest=dest_decode)
    return output, new_offset, ""

