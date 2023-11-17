#ifndef JSON_PARSER_CPP 
#define JSON_PARSER_CPP
#include <iostream>
#include <stdexcept>
#include <string>
#include <boost\regex.hpp>
#include <unordered_map>
#include <any>
#include <vector>
#include <algorithm>
#include <optional>
#include <limits>
#include <math.h>
#include <inttypes.h>

#include "haversine_formula.cpp"


typedef std::unordered_map<std::string, std::any> dict;
typedef std::string str;


namespace json
{

	class JSONDecodeError : public std::exception {
	private:
		char* message;

	public:
		JSONDecodeError(char* msg, str doc, size_t pos) {
			std::string::difference_type line_no = std::count(doc.begin(), doc.begin() + pos, '\n') + 1;
			size_t col_no = pos - doc.rfind("\n", 0, pos);
			sprintf_s(message, sizeof(msg) + 100, "%s: line no:%llu col no: %llu(char %llu) ", msg, (size_t)line_no, col_no, pos);

		}
		char* what() {
			return message;
		}

	};

	class StopIterationError : public std::exception {
	private:
		char* message;

	public:
		StopIterationError(char* msg, size_t val) : message(msg), value(val) {}
		char* what() {
			return message;
		}
		size_t value;
	};

	static std::pair<std::any, size_t> JSONDecoder(const str &s, size_t idx);

	static std::unordered_map<char, char> BACKSLASH = { {'"', '"'}, {'\\', '\\'}, {'/', '/'}, {'b', '\b'}, {'f','\f'}, {'n', '\n'}, {'r','\r'}, {'t','\t'} };

	static std::pair<str, size_t> JSONScanString(const str &s, size_t end, std::unordered_map<char, char> _b = BACKSLASH)
	{

		size_t begin = end - 1;
		while (1)
		{
			char nextchar = s[end];

			if (nextchar == '"')
			{

				return { s.substr(begin + 1, end - begin - 1) , end + 1 };
			}
			else if (nextchar == '\\')
			{
				throw JSONDecodeError((char*)"Unterminated string starting at %d", s, begin);
			}
			end++;
		}

	}
	// Needed Regex patterns 
	static boost::regex WHITESPACE("[ \\t\\n\\r]*");
	static str  WHITESPACE_STR = " \t\n\r";


	static std::pair<dict, int> JSONDict(const std::pair<str, size_t> &data_and_end, std::pair<std::any, size_t>(*JSONDecoder)(const str&, size_t), boost::regex _w = WHITESPACE, str _ws = WHITESPACE_STR)
	{
		str data;
		size_t end;
		std::tie(data, end) = data_and_end;
		std::vector<std::pair<str, std::any>> pairs;
		char nextchar = data[end];

		if (nextchar != '"')
		{
			size_t found = WHITESPACE_STR.find(nextchar);
			if (found != std::string::npos)
			{
				end = data.find_first_not_of(WHITESPACE_STR, end);
				nextchar = data[end];
			}

			if (nextchar == '}')
			{
				// Empty object
				return { dict(), end + 1 };
			}
			else if (nextchar != '"')
			{
				throw JSONDecodeError((char*)"Expecting property name enclosed in double quotes", data, end);
			}
		}

		end++;
		while (true)
		{
			str key;
			std::tie(key, end) = JSONScanString(data, end);
			if (data[end] != ':')
			{
				end = data.find_first_not_of(WHITESPACE_STR, end);
				if (data[end] != ':')
				{
					throw JSONDecodeError((char*)"Expecting ':' delimiter", data, end);
				}
			}

			end++;

			try
			{
				size_t found = WHITESPACE_STR.find(data[end]);
				if (found != std::string::npos)
				{
					end = data.find_first_not_of(WHITESPACE_STR, end);
				}
			}
			catch (std::out_of_range& e) {}
			std::any value;
			try
			{
				std::tie(value, end) = JSONDecoder(data, end);
			}
			catch (StopIterationError& e)
			{
				throw JSONDecodeError((char*)"Expecting value", data, e.value);
			}
			pairs.push_back({ key, value });

			try
			{
				nextchar = data[end];
				size_t found = WHITESPACE_STR.find(data[end]);
				if (found != std::string::npos)
				{
					end = data.find_first_not_of(WHITESPACE_STR, end);
					nextchar = data[end];
				}

			}
			catch (std::out_of_range& e)
			{
				nextchar = '\0';
			}
			end++;

			if (nextchar == '}')
			{
				break;
			}
			else if (nextchar != ',')
			{
				throw JSONDecodeError((char*)"Expecting ',' delimiter", data, end - 1);
			}

			end = data.find_first_not_of(WHITESPACE_STR, end);
			nextchar = data[end];
			end++;
			if (nextchar != '"')
			{
				throw JSONDecodeError((char*)"Expecting property name enclosed in double quotes", data, end - 1);
			}

		}

		dict new_pairs(pairs.begin(), pairs.end());

		return { new_pairs, end };
	}

	static std::pair<std::vector<std::any>, size_t> JSONArray(const std::pair<str, size_t> &s_and_end, std::pair<std::any, size_t>(*JSONDecoder)(const str&, size_t), boost::regex _w = WHITESPACE, str _ws = WHITESPACE_STR)
	{
		str s;
		size_t end;

		std::tie(s, end) = s_and_end;

		std::vector<std::any> values;

		char nextchar = s[end];
		size_t found = WHITESPACE_STR.find(s[end]);
		if (found != std::string::npos)
		{
			end = s.find_first_not_of(WHITESPACE_STR, end);
			nextchar = s[end];
		}

		if (nextchar == ']')
		{
			return { values, end + 1 };
		}


		while (true)
		{
			std::any value;
			try
			{
				std::tie(value, end) = JSONDecoder(s, end);
			}
			catch (StopIterationError& e)
			{
				throw JSONDecodeError((char*)"Expecting Value", s, e.value);
			}

			values.push_back(value);
			nextchar = s[end];
			found = WHITESPACE_STR.find(s[end]);
			if (found != std::string::npos)
			{
				end = s.find_first_not_of(WHITESPACE_STR, end);
				nextchar = s[end];
			}

			end++;
			if (nextchar == ']') break;
			else if (nextchar != ',') throw JSONDecodeError((char*)"Expecting ',' delimiter", s, end - 1);

			try
			{
				found = WHITESPACE_STR.find(s[end]);
				if (found != std::string::npos)
				{
					end = s.find_first_not_of(WHITESPACE_STR, end);
				}
			}
			catch (std::out_of_range& e) {}

		}

		return { values, end };
	}
	static str reg_str = R"((-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?)";
	static boost::regex NUMBER_RE(reg_str);

	static std::pair<std::any, size_t> JSONDecoder(const str &s, size_t idx = 0)
	{
		char nextchar;
		try
		{
			nextchar = s[idx];
		}
		catch (std::out_of_range& e)
		{
			throw StopIterationError((char*)"Incorrect JSON Data Provided", idx);
		}
		switch (nextchar)
		{
		case '"':
		{
			return JSONScanString(s, idx + 1);
		}
		case '{':
		{
			return JSONDict({ s,idx + 1 }, &JSONDecoder);
		}
		case '[':
			{
			return JSONArray({ s, idx + 1 }, &JSONDecoder);
			}
		case 'n':
		{
			if (s.substr(idx, 4) == "null")
			{
				return { NULL, idx + 4 };
			}
			break;
		}
		case 't':
		{
			if (s.substr(idx, 4) == "true")
			{
				return { true, idx + 4 };
			}
			break;
		}
		case 'f':
		{
			if (s.substr(idx, 5) == "false")
			{
				return { false ,idx + 5 };
			}
			break;
		}
		default:
			break;
		}

		boost::smatch m;
		str spliced_str = s.substr(idx, s.size() - idx - 1);
		size_t break_pos = spliced_str.find_first_not_of("+-0123456789.eE");
		str potential_number = (break_pos != str::npos) ? spliced_str.substr(0, break_pos) : spliced_str;
		
		if (boost::regex_match(potential_number, m, NUMBER_RE))
		{
			// m[0]		:	complete str
			// m[1]		:	integer value
			// m[2]		:	fractional value
			// m[3]		:   exponential magnitude value (E.g.: e+10) 

			if (m[2].matched or m[3].matched)
			{
				str fract = (m[2].matched) ? m[2].str() : "\0";
				str exponential = (m[3].matched) ? m[3].str() : "\0";
				double result = std::stod(m[1].str() + fract + exponential);
				return { result, break_pos + idx };
			}

			else
			{
				long result = std::stol(m[1].str());
				return { result, break_pos + idx };
			}
		}

		else if (nextchar == 'N' && s.substr(idx, 3) == "NaN")
		{
			return { std::numeric_limits<double>::quiet_NaN(), idx + 3 };
		}
		else if (nextchar == 'I' && s.substr(idx, 8) == "Infinity")
		{
			return { std::numeric_limits<double>::infinity(), idx + 8 };
		}
		else if (nextchar == '-' && s.substr(idx, 9) == "-Infinity")
		{
			return { -std::numeric_limits<double>::infinity(), idx + 8 };
		}
		else {
			throw StopIterationError((char*)"Incorrect JSON Data Provided", idx);
		}
	}
}
		
#endif 