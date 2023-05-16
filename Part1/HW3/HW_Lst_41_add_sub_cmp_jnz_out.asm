; HW_Lst_41_add_sub_cmp_jnz
bits 16
ADD BX, [BX + SI]
ADD BX, [BP]
ADD SI, 2
ADD BP, 2
ADD CX, 8
ADD BX, [BP]
ADD CX, [BX + 2]
ADD BH, [BP + SI + 4]
ADD DI, [BP + DI + 6]
ADD [BX + SI], BX
ADD [BP], BX
ADD [BP], BX
ADD [BX + 2], CX
ADD [BP + SI + 4], BH
ADD [BP + DI + 6], DI
ADD byte [BX], 34
ADD word [BP + SI + 1000], 29
ADD AX, [BP]
ADD AL, [BX + SI]
ADD AX, BX
ADD AL, AH
ADD AX, 1000
ADD AL, -30
ADD AL, 9
SUB BX, [BX + SI]
SUB BX, [BP]
SUB SI, 2
SUB BP, 2
SUB CX, 8
SUB BX, [BP]
SUB CX, [BX + 2]
SUB BH, [BP + SI + 4]
SUB DI, [BP + DI + 6]
SUB [BX + SI], BX
SUB [BP], BX
SUB [BP], BX
SUB [BX + 2], CX
SUB [BP + SI + 4], BH
SUB [BP + DI + 6], DI
SUB byte [BX], 34
SUB word [BX + DI], 29
SUB AX, [BP]
SUB AL, [BX + SI]
SUB AX, BX
SUB AL, AH
SUB AX, 1000
SUB AL, -30
SUB AL, 9
CMP BX, [BX + SI]
CMP BX, [BP]
CMP SI, 2
CMP BP, 2
CMP CX, 8
CMP BX, [BP]
CMP CX, [BX + 2]
CMP BH, [BP + SI + 4]
CMP DI, [BP + DI + 6]
CMP [BX + SI], BX
CMP [BP], BX
CMP [BP], BX
CMP [BX + 2], CX
CMP [BP + SI + 4], BH
CMP [BP + DI + 6], DI
CMP byte [BX], 34
CMP word [4834], 29
CMP AX, [BP]
CMP AL, [BX + SI]
CMP AX, BX
CMP AL, AH
CMP AX, 1000
CMP AL, -30
CMP AL, 9
JNE $+4 
JNE $-2 
JNE $-4 
JNE $-2 
JE $+0 
JL $-2 
JLE $-4 
JB $-6 
JBE $-8 
JP $-10 
JO $-12 
JS $-14 
JNE $-16 
JNL $-18 
JNLE $-20 
JNB $-22 
JNBE $-24 
JNP $-26 
JNO $-28 
JNS $-30 
LOOP $-32 
LOOPZ $-34 
LOOPNZ $-36 
JCXZ $-38 
