import struct
import os 
import re
import haverstine_formula as hf
from json import JSONDecodeError

import time

FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL

STRINGCHUNK= re.compile(r'(.*?)(["\\\x00-\x1f])', FLAGS)
BACKSLASH= {
    '"':'"', '\\': '\\', '/': '/', 'b': '\b', 'f': '\f',
    'n':'\n', 'r': '\r', 't':'\t'
}

WHITESPACE = re.compile(r'[ \t\n\r]*', FLAGS)
WHITESPACE_STR = ' \t\n\r'

def _decode_uXXXX(s, pos):
    esc = s[pos + 1:pos + 5]
    if len(esc) == 4 and esc[1] not in 'xX':
        try:
            return int(esc, 16)
        except ValueError:
            pass
    msg = "Invalid \\uXXXX escape"
    raise JSONDecodeError(msg, s, pos)


def scanstring(s, end, _b=BACKSLASH, _m=STRINGCHUNK.match):
    chunks = []
    begin = end - 1
    while 1:
        chunk = _m(s, end)
        if chunk is None:
            raise JSONDecodeError("Unterminated string starting at", s, begin)
        end = chunk.end()
        content, terminator = chunk.groups()
        if content:
            chunks.append(content)

        if terminator == '"':
            break
        elif terminator != '\\':
            msg = f"Invalid control character {terminator!r} at"
            raise JSONDecodeError(msg, s, end)
        
        try:
            esc = s[end]
        except IndexError:
            raise JSONDecodeError("Unterminaed string starting at", s, begin) from None
        
        if esc != 'u':
            try:
                char = _b[esc]
            except KeyError:
                msg = "Invalid \\escape: {0!r}".format(esc)
                raise JSONDecodeError(msg, s, end)
            end += 1
        else:
            uni = _decode_uXXXX(s, end)
            end += 5
            if 0xd800 <= uni <= 0xdbff and s[end:end + 2] == '\\u':
                uni2 = _decode_uXXXX(s, end + 1)
                if 0xdc00 <= uni2 <= 0xdfff:
                    uni = 0x10000 + (((uni - 0xd800 << 10) | uni2 - 0xdc00))
                    end += 6
            char = chr(uni)
        chunks.append(char)
    return ''.join(chunks), end

def JSONDict(data_and_end, raw_decode, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, end = data_and_end

    pairs = []
    nextchar = s[end:end + 1]

    memo = {}

    if next != '"':
        if nextchar in _ws:
            end = _w(s,end).end()
            nextchar = s[end:end+1]
        # empty object
        if nextchar == '}':
            pairs = {}
            return pairs, end+1
        elif nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end
            )
    
    end += 1
    while True:
        key, end = scanstring(s, end)
        memo.setdefault(key, key)

        if s[end:end + 1] != ':':
            end = _w(s, end).end()
            if s[end:end + 1] != ':':
                raise JSONDecodeError("Expecting ':' delimiter", s, end)
            
        end += 1

        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end+1).end()
        except IndexError:
            pass

        try:
            value, end = raw_decode(s, end)
        except StopIteration as err:
            raise JSONDecodeError("Expecting value", s, err.value) from None
        pairs.append((key,value))

        try:
            nextchar = s[end]
            if nextchar in _ws:
                end = _w(s, end + 1).end()
                nextchar = s[end]
        except IndexError:
            nextchar = ''
        end += 1

        if nextchar == '}':
            break
        elif nextchar != ',':
            raise JSONDecodeError("Expecting ',' delimiter", s, end - 1 )
        
        end = _w(s,end).end()
        nextchar = s[end:end + 1]
        end += 1
        if nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end - 1)
        
    pairs = dict(pairs)

    return pairs, end

def JSONArray(s_and_end, raw_decode, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, end = s_and_end

    values = []
    nextchar = s[end:end+1]
    if nextchar in _ws:
        end = _w(s, end+1).end()
        nextchar = s[end:end+1]

    if nextchar == ']':
        return values, end + 1

    while True:
        try:
            value, end = raw_decode(s, end)
        except StopIteration as err:
            raise JSONDecodeError("Expecting value", s, err.value) from None
        
        values.append(value)
        nextchar = s[end:end+1]
        if nextchar in _ws:
            end = _w(s, end + 1).end()
            nextchar = s[end:end+1]
        
        end += 1
        if nextchar == ']':
            break
        elif nextchar != ',':
            raise JSONDecodeError("Expecting ',' delimiter", s, end - 1)
        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end+1).end()
        
        except IndexError:
            pass
    
    return values, end

NaN = float('nan')
PosInf = float('inf')
NegInf = float('-inf')

_CONSTANTS = {
    '-Infinity': NegInf,
    'Infinity': PosInf,
    'NaN': NaN,
}

NUMBER_RE = re.compile(r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?', FLAGS)
match_number = NUMBER_RE.match
parse_constant = _CONSTANTS.__getitem__

def raw_decode(s, idx=0):
    
    try:
        nextchar = s[idx]
    except IndexError:
        raise StopIteration(idx) from None

    if nextchar == '"':
        return scanstring(s, idx + 1)
    
    elif nextchar == '{':
        return JSONDict((s, idx+1), raw_decode )

    elif nextchar == '[':
        return JSONArray((s, idx + 1), raw_decode)
    elif nextchar == 'n' and s[idx:idx + 4] == 'null':
        return None, idx + 4
    elif nextchar == 't' and s[idx:idx + 4] == 'true':
        return True, idx + 4
    elif nextchar == 'f' and s[idx:idx + 5] == 'false':
        return False, idx + 5
    
    m = match_number(s, idx)
    if m is not None:
        integer, frac, exp = m.groups()
        if frac or exp:
            res = float(integer + (frac or '') + (exp or ''))
        else:
            res = int(integer)
        return res, m.end()
    elif nextchar == 'N' and s[idx:idx + 3] == 'NaN':
        return parse_constant('NaN'), idx + 3
    elif nextchar == 'I' and s[idx:idx + 8] == 'Infinity':
        return parse_constant('Infinity'), idx + 8
    elif nextchar == '-' and s[idx:idx + 9] == '-Infinity':
        return parse_constant('-Infinity'), idx + 9
    else:
        raise StopIteration(idx)


def decode(s: str, _ws=WHITESPACE.match):
    obj, end = raw_decode(s, idx=_ws(s,0).end())
    end = _ws(s,end).end()
    if end != len(s):
        raise JSONDecodeError("Extra data", s, end)
    return obj


def parse_hav_json(filepath: str):
    global init_time, read_time, parse_time, calc_time
    init_time = time.perf_counter_ns()
    with open(filepath, "r") as json_fp:
        data = json_fp.read()
    read_time = time.perf_counter_ns()
    obj = decode(data)
    parse_time = time.perf_counter_ns()
    pairs = obj["pairs"]
    ref_val = 0
    for pair in pairs:
        x0 = pair["x0"]
        x1 = pair["x1"]
        y0 = pair["y0"]
        y1 = pair["y1"]
        ref_val += hf.ReferenceHaversine(x0=x0, x1=x1, y0=y0, y1=y1, earth_radius=6472.8)

    ref_val = ref_val/float(len(pairs))
    calc_time = time.perf_counter_ns()
    return obj, ref_val


start_time= time.perf_counter_ns()
init_time = 0
read_time = 0
parse_time = 0
calc_time = 0
fp = r"D:\Work\Courses\ComputerEnhance\haversine_data_100000.json"
test_obj, ref_hav_val = parse_hav_json(fp)
end_time = time.perf_counter_ns()

init_timing = (init_time - start_time)
read_timing = (read_time - init_time)
parsing_timing = parse_time - read_time
calc_timing = calc_time - parse_time
total_time = end_time - start_time

print(f"TIMINGS: \n\n\t Total Time: {total_time*0.000000001:.3f}s\n\t Init Time:{init_timing*0.000000001:>20.3f}s ({init_timing/float(total_time) * 100.0:.2f}%)")
print(f"\t Read Time:{read_timing*0.000000001:>20.3f}s ({read_timing/float(total_time) * 100.0:.2f}%)")
print(f"\t Parse Time:{parsing_timing *0.000000001:>19.3f}s ({parsing_timing/float(total_time) * 100.0:.2f}%)")
print(f"\t Hav Cal Time:{calc_timing * 0.000000001:>17.3f}s ({calc_timing/float(total_time) * 100.0:.2f}%)")
