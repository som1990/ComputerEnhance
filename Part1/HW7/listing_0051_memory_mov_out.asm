; listing_0051_memory_mov
bits 16
MOV word [1000], 1
MOV word [1002], 2
MOV word [1004], 3
MOV word [1006], 4
MOV BX, 1000
MOV word [BX+4], 10
MOV BX, [1000]
MOV CX, [1002]
MOV DX, [1004]
MOV BP, [1006]
