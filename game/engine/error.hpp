#pragma once

#include <string>

namespace Engine {

/**
 * Go style Errors 
 */
struct error_t {
public:
	std::string_view Error() const { return m_ErrorMsg; }
	error_t(const char* fmt, ...);

private:
	std::string m_ErrorMsg;
};

} // namespace Engine
