; listing_0049_conditional_jumps
bits 16
MOV CX, 3
MOV BX, 1000
ADD BX, 10
SUB CX, 1
JNE $-6
ADD BX, 10
SUB CX, 1
JNE $-6
ADD BX, 10
SUB CX, 1
JNE $-6
