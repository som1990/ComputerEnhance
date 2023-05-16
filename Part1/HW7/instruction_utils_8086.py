"""
Supported:
Decoding complete flavors of : MOV, conditional Jumps, ADD, ADC, SUB, SBB, CMP
Simming of all varieties of MOVs, ADD, SUB, CMP minus the segment registers.
Implementation of flags for Carry(C), Auxilary Overflow(A), Overflow(O), Parity (P), Sign (S), Zero (Z). 
Implementation of JNE/NZ Jump and IP register.

Author: Soumitra Goswami

"""
from __future__ import annotations
import struct
import typing as t
from dataclasses import dataclass


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
register_lables["ES"] = {"pos": 8, "bytes": 2, "is_high" : 0 }
register_lables["CS"] = {"pos": 9, "bytes": 2, "is_high" : 0 }
register_lables["SS"] = {"pos": 10,"bytes": 2, "is_high" : 0 }
register_lables["DS"] = {"pos": 11,"bytes": 2, "is_high" : 0 }

# IP register
register_lables["IP"] = {"pos": 12,"bytes": 2, "is_high" : 0 }

flag_bit_positions = dict()
flag_bit_positions['C'] = 0
flag_bit_positions['P'] = 2
flag_bit_positions['A'] = 4
flag_bit_positions['Z'] = 6
flag_bit_positions['S'] = 7
flag_bit_positions['T'] = 8
flag_bit_positions['I'] = 9
flag_bit_positions['D'] = 10
flag_bit_positions['O'] = 11


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
encode_address[0b000] = ["BX", "SI"]
encode_address[0b001] = ["BX", "DI"]
encode_address[0b010] = ["BP", "SI"]
encode_address[0b011] = ["BP", "DI"]
encode_address[0b100] = ["SI"]
encode_address[0b101] = ["DI"]
encode_address[0b110] = ["BP"]
encode_address[0b111] = ["BX"]

@dataclass
class MemoryLayout8086():
    registers:t.List[int] = None
    flags: bytes = 0b0
    memory:t.List[int] = None

    def get_reg_value(self, address: Address):
        val = 0
        if not address.is_register:
            print(f"address : {address} is not a register. Returning 0")
            return val
        reg = register_lables[address.val] 
        val = self.registers[reg['pos']]
        src_nbytes = reg["bytes"]
        src_is_high = reg["is_high"]
        if src_nbytes == 1:
            val = (val)>> 8 if src_is_high else (val & 0x00ff)
            
        return val 
    
    def set_reg_value(self, address: Address, val:t.Any):
        reg = register_lables[address.val]
        old_reg_val = self.registers[reg['pos']]
        dest_nbytes = reg["bytes"]
        dest_is_high = reg["is_high"]
        if dest_nbytes == 2: 
            self.registers[reg['pos']] = val
        else:
            bit_mask = 0xff00 if dest_is_high else 0x00ff
            val = val << 8 if dest_is_high else val
            self.registers[reg['pos']] = (old_reg_val & ~(bit_mask))  + (val & bit_mask)

        return old_reg_val
    
    def get_mem_value(self, address:Address):
        val = 0 
        if not address.is_memory:
            print(f"Address: {address} is not a memory address. Returning 0")
            return val
        
        # Take into consideration any displacement provided
        mem_loc = address.mem_displacement
        # if memory needs to be derived from register values we first get the memory locations
        if address.mem_from_reg:
            for reg in address.val:
                reg_pos = register_lables[reg]["pos"]
                mem_loc += self.registers[reg_pos]
        else:    
            mem_loc += address.val[0] # memory address that's explicity stored

        if not address.is_wide:
            val = self.memory[mem_loc]
            return val
        
        val = (self.memory[mem_loc] << 8) | (self.memory[mem_loc+1] & 0xff)

        return val


    def set_mem_value(self, address:Address, val:t.Any):
        if not address.is_memory:
            print(f"Address: {address} is not a memory address. Returning None")
            return
        
        # Take into consideration any displacement provided
        mem_loc = address.mem_displacement
        # if memory needs to be derived from register values we first get the memory locations
        if address.mem_from_reg:
            for reg in address.val:
                reg_pos = register_lables[reg]["pos"]
                mem_loc += self.registers[reg_pos]
        else:    
            mem_loc += address.val[0] # memory address that's explicity stored
        old_value = 0
        if not address.is_wide:
            old_value = self.memory[mem_loc]
            self.memory[mem_loc] = val
        else:
            old_value = self.memory[mem_loc] << 8 | self.memory[mem_loc] << 8 | self.memory[mem_loc+1] & 0xff
            self.memory[mem_loc] = val & 0xff00
            self.memory[mem_loc+1] = val & 0x00ff
        
        return old_value


@dataclass(frozen=True)
class Address():
    val: t.Any
    mem_displacement: t.Optional[int] = 0 
    is_register: t.Optional[bool] = False
    is_memory: t.Optional[bool] = False
    is_displacement: t.Optional[bool] = False 
    is_wide: t.Optional[bool] = True
    mem_from_reg:t.Optional[bool] = False

    def __str__(self):
        if self.is_memory:
            val_str = self.val[0] if (len(self.val) < 2) else f"{self.val[0]} + {self.val[1]}"
            if self.mem_displacement == 0:
                return f"[{val_str}]"
            return f"[{val_str}{self.mem_displacement:+}]"
        if self.is_displacement:
            return f"${self.val:+}"
        
        return f"{self.val}"
    
    @property
    def flags(self):
        f_val = 0
        f_val |= int(self.is_register) # encode register flag
        f_val |= (int(self.is_memory) << 1) # encode memory flag
        f_val |= (int(self.is_displacement) << 2) # encode displacement flag 
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


def serialize_flags(flags: int)->str:
    '''
    flags 
    bit     Description
    0      C : Carry Flag
    1      U : Undefined
    2      P : Parity Flag
    3      U : Undefined
    4      A : Auxiliary Carry Flag
    5      U : Undefined
    6      Z : Zero Flag
    7      S : Sign Flag
    8      T : Trap Flag
    9      I : Interupt Flag
    10      D : Direction Flag
    11      O : Overflow Flag
    12-15   U : Undefined
    '''
    lables = dict()
    lables[0] = 'C'
    lables[2] = 'P'
    lables[4] = 'A'
    lables[6] = 'Z'
    lables[7] = 'S'
    lables[8] = 'T'
    lables[9] = 'I'
    lables[10] = 'D'
    lables[11] = 'O'
    output = ''
    for flag_pos in lables.keys(): 
        flag_val = flags>>flag_pos & 1
        if flag_val == 1:
            output += lables[flag_pos]

    return output

def decode_mod(buf:bytes, buff_off:int, mod_code:int, rm_field:int, is_wide:int)->t.Tuple[Address, Address, int]:
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
        decode_str = Address(encode_address[rm_field], is_memory=True, is_wide=(is_wide==1), mem_from_reg=True) 
        
    elif mod_code == 0b00 and rm_field == 0b110:
        byte_code = 'h' if is_wide else 'b'
        byte_offset = 2 if is_wide else 1
        buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
        new_offset += byte_offset
        decode_str = Address(buffer, is_memory=True, is_wide=(is_wide==1))
    else:
        byte_code = 'h' if mod_code==2 else 'b'
        byte_offset = 2 if mod_code==2 else 1
        buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
        new_offset += byte_offset
        val = buffer[0]
        decode_str = Address(encode_address[rm_field], mem_displacement=val, is_memory=True, is_wide=(is_wide==1), mem_from_reg= True) # This needs to change when simulating memory 


    return decode_str, new_offset

def mem_reg_ops(buf:bytes, buf_off:int)->t.Tuple[Address, Address, int]:
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

def trans_between_immediate_and_accumulator(buf:bytes, buf_off:int, is_memory:bool=False)->t.Tuple[Address, Address, int]:
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
    buf_val = buffer if is_memory else buffer[0]
    src_decode = Address(buf_val, is_memory=is_memory, is_wide=(is_wide==1))

    if is_accum_to_mem == 1:
        temp_decode = dest_decode
        dest_decode = src_decode
        src_decode = temp_decode
    
    print(f"Dest={dest_decode}, Source={src_decode}")
    return dest_decode, src_decode, new_offset

def mov_between_segs_regs_and_memory(buf:bytes, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, str]:
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    ip_reg = register_lables["IP"] 
    ip_old = mem_layout.registers[ip_reg['pos']] 
    new_offset = ip_old
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
    
    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"
    
    #Simming
    
    if src_decode.is_register:
        src_val = mem_layout.get_reg_value(src_decode)
    elif src_decode.is_memory:
        src_val = mem_layout.get_mem_value(src_decode)
    
    reg_move_str = ""
    if dest_decode.is_register:
        old_reg_val = mem_layout.set_reg_value(dest_decode, src_val)
        reg_move_str =f"; {dest_decode}:{old_reg_val:#06x}->{src_val:#06x}"
    elif dest_decode.is_memory:
        old_reg_val = mem_layout.set_mem_value(dest_decode, src_val)
        
    sim_out = f"{output}{reg_move_str}{ip_str} \n"
    return output, sim_out

    
# INSTRUCTION SETS 
def mov_between_mem_and_reg(buf:bytes, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, str]:
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    print("I'm doing mov between memory and register")
    print(f"Byte1: OpCode= {bin(0b100010)} , operation= 'MOV'")
    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old
    dest_decode,src_decode, new_offset = mem_reg_ops(buf, new_offset)
    
    print(f"Dest={dest_decode}, Source={src_decode}")
    output = Instruction("MOV", src_decode, dest_decode)
    
    
    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"

    # Siming

    if src_decode.is_register:
        src_val = mem_layout.get_reg_value(src_decode)
    elif src_decode.is_memory:
        src_val = mem_layout.get_mem_value(src_decode)
    
    reg_move_str = ""
    if dest_decode.is_register:
        old_reg_val = mem_layout.set_reg_value(dest_decode, src_val)
        reg_move_str =f"; {dest_decode}:{old_reg_val:#06x}->{src_val:#06x}"
    elif dest_decode.is_memory:
        old_reg_val = mem_layout.set_mem_value(dest_decode, src_val)
        
    sim_out = f"{output}{reg_move_str}{ip_str} \n"
    return output, sim_out

def mov_immediate_to_reg_or_memory(buf:bytes, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, str]:
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

    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old
    buffer = struct.unpack_from('2B', buf, offset=new_offset)
    new_offset += 2

    is_wide = buffer[0] & 1
    print(f"Byte1: Opcode={bin(0b1011)}, is_wide={is_wide}")
    
    mod_code = buffer[1] >> 6
    rm_code = buffer[1] & 0b111
    dest_decode, new_offset = decode_mod(buf, new_offset, mod_code, rm_code, is_wide)
    
    byte_code = "h" if is_wide else "b"
    byte_offset = 2 if is_wide else 1

    buffer = struct.unpack_from(byte_code, buf, offset=new_offset)
    new_offset += byte_offset
    src_decode = Address(buffer[0], is_wide=(is_wide==1))
    print(f"MOD={bin(mod_code)}, Dest={dest_decode}, Source={src_decode}")
    output = Instruction("MOV", src_decode, dest_decode)

    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"
    
    # Simming
    src_val = src_decode.val
    reg_move_str = ""
    if dest_decode.is_register:
        old_reg_val = mem_layout.set_reg_value(dest_decode, src_val)
        reg_move_str =f"; {dest_decode}:{old_reg_val:#06x}->{src_val:#06x}"
    elif dest_decode.is_memory:
        old_reg_val = mem_layout.set_mem_value(dest_decode, src_val)
 
    sim_out = f"{output}{reg_move_str}{ip_str} \n"
    
    return output, sim_out
    

def mov_immediate_to_reg(buf:bytes,  mem_layout:MemoryLayout8086)->t.Tuple[Instruction, str]:
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
    # Decoding
    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old  
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

    
    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"

    # Simming
    src_val = src_decode.val
    old_reg_val = mem_layout.set_reg_value(dest_decode, src_val)
    
    reg_move_str =f"; {dest_decode}:{old_reg_val:#06x}->{src_val:#06x}"
    sim_out = f"{output}{reg_move_str}{ip_str} \n"
    return output, sim_out


def mov_mem_to_accum(buf:bytes, buf_off:int, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, str]:
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    
    print(f"I'm doing mov from memory to accumilator : OPCODE= {1010000}")
    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old 
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, buf_off, is_memory=True)

    output = Instruction("MOV", src_decode, dest_decode)
 
    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"

    src_val = mem_layout.get_mem_value(src_decode)
    
    old_reg_val = mem_layout.set_reg_value(dest_decode, src_val)
    reg_move_str =f"; {dest_decode}:{old_reg_val:#06x}->{src_val:#06x}"
    sim_out = f"{output}{reg_move_str}{ip_str} \n"
    return output, sim_out


def mov_accum_to_mem(buf:bytes, buf_off:int, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, str]:
    """Reference Manual: Intel 8086 Family User's Manual October 1979
       Reference page: 4-22 MOV instruction
    """
    print(f"I'm doing mov from accumilator to memory. OPCODE: {1010001}")
    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old 
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, buf_off,is_memory=True)

    output = Instruction("MOV", src_decode, dest_decode)

    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"
    src_val = mem_layout.get_reg_value(src_decode)
    
    old_reg_val = mem_layout.set_mem_value(dest_decode, src_val)
    sim_out = f"{output}{ip_str} \n"
    return output, sim_out


def set_flags(flags: bytes, res: bytes, val_dest:bytes, val_src:bytes, arith_op:bytes, n_bytes: t.Optional[int] = 2)->t.Tuple[bytes,str]:
    # Generate flags
    flags_old = flags
    flags_str_old = serialize_flags(flags_old)
    most_significant_bit = 8 * n_bytes - 1;
    usgn_src = val_src if val_src >= 0 else (-val_src + 2**most_significant_bit)  
    usgn_dest = val_dest if val_dest >=0 else (-val_dest + 2**most_significant_bit)
    usgn_res = res if res >=0 else (-res + 2**most_significant_bit)

    flags_new = flags_old
    # Parity Flag Calculation
    mask = 1 << flag_bit_positions['P']
    low_nibble = usgn_res & 0xff
    parity_flag = low_nibble ^ (low_nibble >> 1)
    parity_flag = parity_flag ^ (parity_flag >> 2)
    parity_flag = parity_flag ^ (parity_flag >> 4)
    parity_flag = (~parity_flag) & 1
    flags_new = (flags_new & ~mask) | (parity_flag << flag_bit_positions['P'])
    # setting sign flag
    mask= 1 << flag_bit_positions['S']
    
    sign_flag = (usgn_res >> most_significant_bit) & 1
    flags_new = (flags_new & ~mask) | (sign_flag << flag_bit_positions['S'])

    # setting zero flag
    mask= 1 << flag_bit_positions['Z']
    zero_flag = int(res & (2**(8*n_bytes)-1)== 0)
    flags_new = (flags_new & ~mask) | (zero_flag << flag_bit_positions['Z'])

    # calc overflow flag
    
    """ Truth Table Overflow flag 
    (FOR ADD)
    src     dest    res     expected    Notes                           
    0       0       0       0           (+a) + (+b) = (+c)
    0       0       1       1           (+a) + (+b) = (-c) (OVERFLOW)
    0       1       0       0           (+a) + (-b) = (+c) (if a > b)
    0       1       1       0           (+a) + (-b) = (-c) (if b > a)
    1       0       0       0           (-a) + (+b) = (+c) (if b > a) 
    1       0       1       0           (-a) + (+b) = (-c) (if a > b)
    1       1       0       1           (-a) + (-b) = (+c) (OVERFLOW)
    1       1       1       0           (-a) + (-b) = (-c)

    (For SUB (dest - src) )
    src     dest    res     expected    Notes                           
    0       0       0       0           -(+a) + (+b) = (+c) (if b > a)
    0       0       1       0           -(+a) + (+b) = (-c) (if a > b)
    0       1       0       1           -(+a) + (-b) = (+c) (OVERFLOW)
    0       1       1       0           -(+a) + (-b) = (-c) 
    1       0       0       0           -(-a) + (+b) = (+c) 
    1       0       1       1           -(-a) + (+b) = (-c) (OVERFLOW)
    1       1       0       0           -(-a) + (-b) = (+c) (if a > b)
    1       1       1       0           -(-a) + (-b) = (-c) (if b > a)
    """
    
    """ DEBUG VARS
    src_sbin = bin(val_src)
    dest_sbin = bin(val_dest)
    res_sbin = bin(res)
    src_ubin = bin(usgn_src)
    dest_ubin = bin(usgn_dest)
    res_ubin = bin(usgn_res)
    src_hex = hex(val_src)
    res_hex = hex(res)
    dest_hex = hex(val_dest)
    """
    # TODO: FIND a way to remove branching
    sign_bit_src = (usgn_src >> most_significant_bit) & 1
    sign_bit_dest = (usgn_dest >> most_significant_bit) & 1 
    sign_bit_res = (usgn_res >> most_significant_bit) & 1
    
    mask = 1 << flag_bit_positions['O']

    if arith_op % 2 == 0:
        overflow_flag = ((~sign_bit_src ^ sign_bit_dest) & (sign_bit_dest ^ sign_bit_res)) & 1 
    else:
        overflow_flag =  ((sign_bit_src^sign_bit_dest) & ~(sign_bit_src ^ sign_bit_res)) & 1
    
    flags_new = (flags_new & ~mask) | (int(overflow_flag) << flag_bit_positions['O'])
    
    """ Understanding Auxilary Flag
    5th bit Truth Table
    dest    src     res     AF
    0       0       0       0
    0       0       1       1
    0       1       0       1     
    0       1       1       0
    1       0       0       1
    1       0       1       0
    1       1       0       0
    1       1       1       1

    """
    mask = 1 << flag_bit_positions['A']
    auxilary_flag = ((val_src ^ val_dest ^ res) & 0b10000) != 0
    flags_new = (flags_new & ~mask) | (int(auxilary_flag) << flag_bit_positions['A'])
    
    """ Undesrtanding Carry Flag
    The requirement changes for additions and subtractions
    TODO: Find a way to remove the branching
    (ADD Carry Out)
    8th/16th bit truth table
    
    dest(a) src(b)  res(r)  CF      Notes
    0       0       0       0       small numbers being added not large enough for 8th/16th bit            
    0       0       1       0       small numbers added turning on the 8th/16th bit            
    0       1       0       1       CARRY. Overflow of the 8th/16th bit.      
    0       1       1       0       Numbers being added not overflowing.
    1       0       0       0       CARRY. Overflow of the 8th/16th bit.  
    1       0       1       0       Number being added not overflowing.      
    1       1       0       1       CARRY. Numbers being added causing overflow 
    1       1       1       1       Will always overflow as two sign bit numbers added.
    
    SUB (Carry in/Borrow)
    Its simple. In a-b, if b > a its a borrow. 
    """
    mask = 1 << flag_bit_positions['C']
    if arith_op % 2 == 0:
        carry_flag = res >= 2**(most_significant_bit+1)
    else:
        carry_flag = val_src > val_dest
    #carry_flag = (((sign_bit_src | sign_bit_dest) & ~sign_bit_res) | (sign_bit_src & sign_bit_dest)) & 1
    flags_new = (flags_new & ~mask) | (int(carry_flag) << flag_bit_positions['C'])

    flags_str_new = serialize_flags(flags_new)
   
    flags_str = f" flags: {flags_str_old}->{flags_str_new} " if (flags_new != flags_old) else ""

    return flags_new, flags_str

# ARITHMETIC INSTRUCTIONS
arith_opcodes = dict()
arith_opcodes[0b000] = {"decode" : "ADD", "desc": "I'm doing an add. Flavor : Immediate to register/memory"}
arith_opcodes[0b010] = {"decode" : "ADC", "desc": "I'm doing an add with carry. Flavor : Immediate to register/memory"}
arith_opcodes[0b101] = {"decode" : "SUB", "desc": "I'm doing an sub. Flavor : Immediate from register/memory"}
arith_opcodes[0b011] = {"decode" : "SBB", "desc": "I'm doing an subtract with borrow. Flavor : Immediate from register/memory"}
arith_opcodes[0b111] = {"decode" : "CMP", "desc": "I'm doing a compare. Flavor : Immediate from register/memory"}


def arith_sim(src_decode:Address, dest_decode:Address, mem_layout:MemoryLayout8086, arith_opcode: bytes, ip_str:str)->str:
    # Simming
    sim_out = ""
    if src_decode.is_immediate:
        src_val = src_decode.val
    elif src_decode.is_memory:
        src_val = mem_layout.get_mem_value(src_decode)
    elif src_decode.is_register:
        src_val = mem_layout.get_reg_value(src_decode)
        
    src_val = src_val & 0xffff 
    dest_nbytes = 2 if dest_decode.is_wide else 1   
    dest_reg = register_lables[dest_decode.val]
    old_reg_val=0
    if dest_decode.is_memory:
        old_reg_val = mem_layout.get_mem_value(dest_decode)
    elif dest_decode.is_register:
        old_reg_val = mem_layout.get_reg_value(dest_decode) 
    new_val = old_reg_val
    
    # All the add opcodes are even while sub opcodes are odd.
    # CMP (0b111) is a sub opcode without saving the value.
    is_add = (arith_opcode % 2) == 0
    #is_neg = ((old_reg_val>>most_sig_bit) & 1) == 1
    #is_add = (not is_add) if is_neg else is_add
    if is_add:
        new_val = (old_reg_val + src_val) & 0xffff # Bit addition
    else:
        new_val = (old_reg_val + ~src_val + 1) & 0xffff #Bit subtraction
    
    # Do not set value if it's a CMP operator (0b111). 
    reg_activity=""
    if arith_opcode != 0b111:
        if dest_decode.is_memory:
            mem_layout.set_mem_value(dest_decode, new_val)
        elif dest_decode.is_register:
            mem_layout.set_reg_value(dest_decode, new_val) 
        reg_activity=f"{dest_decode}:{old_reg_val:#06x}->{mem_layout.registers[dest_reg['pos']]:#06x} "  
        
    mem_layout.flags, flags_str = set_flags(mem_layout.flags, new_val, old_reg_val, src_val , arith_opcode, dest_nbytes)
    
    sim_out = f"; {reg_activity}{ip_str}{flags_str} \n"
    
    return sim_out

def arith_immediate_to_register_memory(buf:bytes, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, str]:
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
    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old 
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

    print(f"mod={bin(mod_code)}, Dest={dest_decode}, Source={src_decode}")
    output = Instruction(memonic, src_decode, dest_decode)
     
    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"
    
    # Simming
    sim_out = arith_sim(src_decode, dest_decode, mem_layout, arith_opcode, ip_str)
    sim_out = f"{output}{sim_out}"
    
    return output, sim_out


def add_between_register_memory(buf:bytes, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, int, str]:
    print(f"I'm doing an add flavor : reg/memory with register to either. OPCODE:{000000}")
    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old 
    dest_decode, src_decode, new_offset = mem_reg_ops(buf, new_offset)
    print(f" Dest={dest_decode}, Source={src_decode}")
    output = Instruction("ADD", src_decode, dest_decode)

    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"
    #Simming
    sim_out = str(output) 
    print("HI")
    sim_out += arith_sim(src_decode,dest_decode, mem_layout, 0b000, ip_str) 
    return output, sim_out


def add_immediate_to_accumulator(buf:bytes, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, int, str]:
    print(f"I'm doing an add flavor : Immediate to accumilator. OPCODE:{bin(0b000010)}")
    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old 
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, new_offset)
    output = Instruction("ADD", src_decode, dest_decode)

    ip_reg = register_lables["IP"] 
    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"

    sim_out = str(output)
    sim_out += arith_sim(src_decode,dest_decode, mem_layout, 0b000, ip_str)
    return output, sim_out


def sub_between_register_memory(buf:bytes, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, int, str]:
    print("I'm doing an sub flavor : reg/memory with register to either")
    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old 
    dest_decode, src_decode, new_offset = mem_reg_ops(buf, new_offset)

    print(f" Dest={dest_decode}, Source={src_decode}")
    output = Instruction("SUB", src_decode, dest_decode)
    
    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"
    
    sim_out = str(output)
    sim_out += arith_sim(src_decode,dest_decode, mem_layout,0b101, ip_str) 

    return output, sim_out


def sub_immediate_from_accumulator(buf:bytes, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, int, str]: 
    print(f"I'm doing an sub flavor : Immediate from accumilator.{bin(0b0010110)}")
    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old 
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, new_offset)
    
    print(f" Dest={dest_decode}, Source={src_decode}")
    output = Instruction("SUB", src_decode, dest_decode)

    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"

    sim_out = str(output)
    sim_out += arith_sim(src_decode,dest_decode, mem_layout, 0b101, ip_str) 

    return output, sim_out


def cmp_between_register_memory(buf:bytes, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, str]:
    print(f"I'm doing an cmp flavor : reg/memory with register to either. {bin(0b001110)}")
    
    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old 
    dest_decode, src_decode, new_offset = mem_reg_ops(buf, new_offset)

    print(f" Dest={dest_decode}, Source={src_decode}")
    output = Instruction("CMP", src_decode, dest_decode)

    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"

    sim_out = str(output)
    sim_out += arith_sim(src_decode,dest_decode, mem_layout, 0b111, ip_str)
    return output, sim_out


def cmp_immediate_from_accumulator(buf:bytes, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, str]:
    print(f"I'm doing an cmp flavor : Immediate from accumilator.{bin(0b0010110)}")
    
    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old 
    dest_decode, src_decode, new_offset = trans_between_immediate_and_accumulator(buf, new_offset)
    
    print(f"Dest={dest_decode}, Source={src_decode}")
    output = Instruction("CMP", src_decode, dest_decode)

    ip_reg = register_lables["IP"] 
    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val
    ip_str = f" ip:{ip_old:#x}->{ip_address.val:#x}"

    sim_out = str(output)
    sim_out += arith_sim(src_decode,dest_decode, mem_layout, 0b111, ip_str)

    return output, sim_out


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

def jmp_sim(instruction: Instruction, mem_layout:MemoryLayout8086):
    new_ip = mem_layout.registers[12] # IP Register
    flags = mem_layout.flags
    if instruction.memonic == "JNE": # JNZ or JNE not equal or not equal to zero
        displacement = int(instruction.dest.val)
        bit_pos = flag_bit_positions['Z']
        is_zero = flags>>bit_pos & 1
        if not is_zero:
            new_ip += displacement - 2 # Fixing the +2 offset we performed earlier to guide NASM.
    return new_ip


def jmp_unconditional(buf:bytes, mem_layout:MemoryLayout8086)->t.Tuple[Instruction, str]:
    '''
    Byte 1
    Jump OpCode                                             - 8 bits

    Byte 2
    DISP                                                    - 8 bits
    '''
    print("I'm doing a conditional jump")
    
    ip_reg = register_lables["IP"]
    ip_old = mem_layout.registers[ip_reg["pos"]] 
    new_offset = ip_old 
    buffer = struct.unpack_from('B', buf, offset=new_offset)
    new_offset += 1

    opcode = buffer[0]
    operation_decode = jump_opcodes[opcode]
    
    buffer = struct.unpack_from('b', buf, offset=new_offset)
    new_offset +=1

    # +2 is an offset for NASM to jump to the right memory location. 
    # For Jumps NASM assumes the provided memory location includes the offset done by the Jump.
    # However it does encode the value in Binary correctly by subtracting 2.
    disp = buffer[0] + 2

    dest_decode = Address(disp, is_wide=False, is_displacement=True)
    print(f"jump operation: {operation_decode}, displacement={dest_decode}")
    output = Instruction(operation_decode, dest=dest_decode)

    ip_address = Address(new_offset, is_register=True)
    mem_layout.registers[ip_reg["pos"]] = ip_address.val

    ip_new = jmp_sim(output, mem_layout)
    ip_str = f" ip:{ip_old:#x}->{ip_new:#x}"
    mem_layout.registers[ip_reg["pos"]] = ip_new
    sim_out = f"{output}; {ip_str} \n"
    return output, sim_out

