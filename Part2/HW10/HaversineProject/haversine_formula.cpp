#pragma once

#include <math.h>

typedef double f64;

namespace hf
{
	static f64 square(f64 A)
	{
		return A * A;
	}

	static f64 radiansFromDegrees(f64 Degrees)
	{
		return 0.01745329251994329577 * Degrees;
	}

	static f64 referenceHaversine(f64 x0, f64 y0, f64 x1, f64 y1, f64 earthRadius)
	{
		f64 lat1 = y0;
		f64 lat2 = y1;
		f64 lon1 = x0;
		f64 lon2 = x1;

		f64 dLat = radiansFromDegrees(lat2 - lat1);
		f64 dLon = radiansFromDegrees(lon2 - lon1);
		lat1 = radiansFromDegrees(lat1);
		lat2 = radiansFromDegrees(lat2);

		f64 a = square(sin(dLat / 2.0) + cos(lat1) * cos(lat2) * square(sin(dLon / 2.0)));
		f64 c = 2.0 * asin(sqrt(a));

		return earthRadius * c;
	}

}