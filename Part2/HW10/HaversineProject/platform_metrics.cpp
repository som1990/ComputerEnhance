#include <stdio.h>
#include <stdint.h>

typedef uint64_t u64;
typedef double f64;

#if _WIN64

#include <intrin.h>
#include <windows.h>

static u64 GetOSTimerFreq(void)
{
	LARGE_INTEGER Freq;
	QueryPerformanceFrequency(&Freq);
	return Freq.QuadPart;
}

static u64 ReadOSTimer(void)
{
	LARGE_INTEGER Value;
	QueryPerformanceCounter(&Value);
	return Value.QuadPart;
}

#else

#include <x86intrin.h>
#include <sys/time.h>

static u64 GetOSTimerFreq(void)
{
	return 1000000;
}

static u64 ReadOSTimer(void)
{
	struct timeval Value;
	gettimeofday(&Value, 0);

	u64 Result = GetOSTimerFreq() * (size_t)Value.tv_sec + (size_t)Value.tv_usec;
	return Result;
}

#endif

static u64 ReadCPUTimer(void)
{
	return __rdtsc();
}

static size_t EstimateCPUTimerFreq(void)
{
	u64 MillisecondsToWait = 100;
	u64 OSFreq = GetOSTimerFreq();

	u64 CPUStart = ReadCPUTimer();
	u64 OSStart = ReadOSTimer();
	u64 OSEnd = 0;
	u64 OSElapsed = 0;
	u64 OSWaitTime = OSFreq * MillisecondsToWait / 1000;
	while (OSElapsed < OSWaitTime)
	{
		OSEnd = ReadOSTimer();
		OSElapsed = OSEnd - OSStart;
	}

	//printf(" OS Timer: %llu -> %llu = %llu elapsed\n", OSStart, OSEnd, OSElapsed);
	//printf(" OS Seconds: %.4f\n", (f64)OSElapsed / OSFreq);


	u64 CPUEnd = ReadCPUTimer();
	u64 CPUElapsed = CPUEnd - CPUStart;

	u64 CPUFreq = 0;
	if (OSElapsed)
	{
		CPUFreq = OSFreq * CPUElapsed / OSElapsed;
	}

	return CPUFreq;
}