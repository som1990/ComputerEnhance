from __future__ import annotations
import typing as t
import random 
import json
import struct
import haverstine_formula as hf

def gen_haversine_pairs(num: int, buff: bytes, buff_offset: int, seed:int = 0, )->t.Tuple(t.Dict[str,t.Any], float, bytes):
    pairs: t.List[t.Dict[str,float]] = [{}] * num
    hv_val = 0
    buf_off = buff_offset
    for i in range(num):
        random.seed(seed)
        x0 = random.uniform(-180.0, 180.0)
        x1 = random.uniform(-180.0, 180.0)
        y0 = random.uniform(-90.0, 90.0)
        y1 = random.uniform(-90.0, 90.0)
        struct.pack_into("dddd", buff, buf_off, x0,y0,x1,y1)
        buf_off = buf_off + 32
        pair = {"x0": x0, "y0": y0, "x1": x1, "y1": y1}
        pairs[i] = pair
        hv_val += hf.ReferenceHaversine(x0,y0,x1,y1, 6472.8)
        

    return pairs, hv_val/num, buff, buf_off

"""
pack format:

num of values: i (4 bytes)
For each value in num values:
    x0 : d (8 bytes)
    y0 : d (8 bytes)
    x1 : d (8 bytes)
    y1 : d (8 bytes)
"""

def gen_haversine_data(num_vals: int, seed:int, filepath: str, bin_path: str):
    buffer = bytearray(4 + (32*num_vals) + 4) 
    buff_off = 0
    struct.pack_into("i", buffer, buff_off, num_vals)
    buff_off = buff_off + 4
    pairs, running_total, buffer, buff_off = gen_haversine_pairs(num=num_vals, buff=buffer, buff_offset=buff_off, seed=seed)
    struct.pack_into("f", buffer, buff_off, running_total)
    data = dict()
    data["pairs"] = pairs
    with open(bin_path, "wb") as bfile:
        bfile.write(buffer)
    with open(filepath, "w") as out_file:
        json.dump(data, fp=out_file, indent=4)
    print(f"RunningTotal: {running_total}")




filepath = ".\\haversine_data_10000.json"
bin_path = ".\\haversine_data_10000.bin"
seed1= 26346346346346
seed2= 34634234
gen_haversine_data(10000, seed2, filepath, bin_path)