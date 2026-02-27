#include "error.hpp"

#include <cstdarg>

namespace Engine {

error_t::error_t(const char* fmt, ...)
{
	// TODO(gowrish) what if this isn't enough size for the buffer

	char buffer[1024];
	va_list args;
	va_start(args, fmt);
	vsnprintf(buffer, sizeof(buffer), fmt, args);
	va_end(args);

	m_ErrorMsg = buffer;
}

} // namespace Engine
