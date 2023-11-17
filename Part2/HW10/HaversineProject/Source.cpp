#include <iostream>
#include <fstream>
#include <string>
#include "json_parser.cpp"
#include <tuple>
#include <sstream>
#include <any>
#include <regex>
#include <boost/regex.hpp>
#include "haversine_formula.cpp"

#include "platform_metrics.cpp"

static void testRegex()
{
	str reg_str2 = R"((-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?)";
	boost::regex NUMBER_RE2(reg_str2);
	str test_float = R"(-1.23323523)";
	str test_int = R"(234235)";
	str test_float_exp ="1.24e-203";
	str test_multiline_float = "1.235235,\n-122.235235";
	str new_test = "";
	size_t pos = -1;
	boost::smatch m;
	pos = test_float.find_first_not_of("+-0123456789.eE");
	new_test = test_float.substr(0, pos);
	boost::regex_match(test_float, m, NUMBER_RE2);
	std::cout << "Regex for source : " << test_float << "\n";
	std::cout << "Match size: " << m.size() << "\n";
	std::cout << "Matches: " << m[0] << "\t" << m[1] << "\t" << m[2] << "\t" << m[3] << "\n";
	
	boost::smatch m1;
	pos = test_int.find_first_not_of("+-0123456789.eE");
	new_test = test_int.substr(0, pos);
	boost::regex_match(test_int, m1, NUMBER_RE2);
	std::cout << "Regex for source : " << test_int << "\n";
	std::cout << "Match size: " << m1.size() << "\n";
	std::cout << "Matches: " << m1[0] << "\t" << m1[1] << "\t" << m1[2] << "\t" << m1[3] << "\n";

	boost::smatch m2;
	pos = test_float_exp.find_first_not_of("+-0123456789.eE");
	new_test = test_float_exp.substr(0, pos);
	boost::regex_match(test_float_exp, m2, NUMBER_RE2);
	std::cout << "Regex for source : " << test_float_exp << "\n";
	std::cout << "Match size: " << m2.size() << "\n";
	std::cout << "Matches: " << m2[0].str() << "\t" << m2[1].str() << "\t" << m2[2].str() << "\t" << m2[3].str() << "\n";

	boost::smatch m3;
	pos = test_multiline_float.find_first_not_of("+-0123456789.eE");
	new_test = test_multiline_float.substr(0, pos);
	bool success = boost::regex_match(new_test, m3, NUMBER_RE2);
	std::cout << "Regex for source : " << new_test << "\n";
	std::cout << "Match success: " << success << "\n";
	std::cout << "Matches: " << m3[0] << "\t" << m3[1].str() << "\t" << m3[2].str() << "\t" << m3[3].str() << "\n";

}

static void PrintTimeElapsed(char const* Label, u64 TotalTSCElapsed, u64 Begin, u64 End)
{
	u64 CPUFreq = EstimateCPUTimerFreq();
	u64 Elapsed = End - Begin;
	f64 Percent = 100.0 * ((f64)Elapsed / (f64)TotalTSCElapsed);
	f64 time = 1000 * Elapsed / (f64)CPUFreq;
	printf("  %s: %.4fms (%.2f%%)\n", Label, time, Percent);
}

int main(int argc, char** args)
{
	u64 timer_begin = 0;
	u64 timer_fileReadBegin = 0;
	u64 timer_fileReadEnd = 0;
	u64 timer_parseJSONEnd = 0;
	u64 timer_sumEnd = 0;
	timer_begin = ReadCPUTimer();

	if (argc > 0)
	{
		

		//std::string filepath = args[1];
		std::string filepath = "D:\\Work\\Courses\\ComputerEnhance\\haversine_data_10000.json";
		std::cout << filepath << "\n";

		timer_fileReadBegin = ReadCPUTimer();
		std::ifstream infile(filepath);
		size_t end;
		std::ostringstream ss = std::ostringstream();
		std::any obj;
		ss << infile.rdbuf();
		timer_fileReadEnd = ReadCPUTimer();

		std::tie(obj, end) = json::JSONDecoder(ss.str(),0);
		timer_parseJSONEnd = ReadCPUTimer();
		
		dict JSONobj = std::any_cast<dict>(obj);
		std::vector<std::any> pairs = std::any_cast<std::vector<std::any>>(JSONobj["pairs"]);
		double running_total = 0;
		size_t pair_size = pairs.size();
		for (size_t i = 0; i < pairs.size(); ++i)
		{
			dict m_pair = std::any_cast<dict>( pairs[i]);
			double x0 = std::any_cast<double>(m_pair["x0"]);
			double x1 = std::any_cast<double>(m_pair["x1"]);
			double y0 = std::any_cast<double>(m_pair["y0"]);
			double y1 = std::any_cast<double>(m_pair["y1"]);

			running_total += hf::referenceHaversine(x0, y0, x1, y1, 6472.8);
		}

		running_total = running_total / (1.0 * pair_size);
		timer_sumEnd = ReadCPUTimer();

		std::cout << "Reference Total: " << running_total << "\n";
		
		u64 TotalCPUElapsed = timer_sumEnd - timer_begin;

		u64 CPUFreq = EstimateCPUTimerFreq();
		if (CPUFreq)
		{
			printf("\nTIMINGS:\n");
			printf("\nTotal time: %0.4fms (CPU freq %llu)\n", 1000.0 * (f64)TotalCPUElapsed / (f64)CPUFreq, CPUFreq);
			PrintTimeElapsed("\tInit Time", TotalCPUElapsed, timer_begin, timer_fileReadBegin);
			PrintTimeElapsed("\tRead Time", TotalCPUElapsed, timer_fileReadBegin, timer_fileReadEnd);
			PrintTimeElapsed("\tParsing Time", TotalCPUElapsed, timer_fileReadEnd, timer_parseJSONEnd);
			PrintTimeElapsed("\tHav Calc Time", TotalCPUElapsed, timer_parseJSONEnd, timer_sumEnd);
		}
		//testRegex();
		
	}
	
	return 0;
}




