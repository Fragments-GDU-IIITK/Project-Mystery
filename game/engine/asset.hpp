#pragma once

#include "error.hpp"

namespace Engine {

class Asset
{
public:

	/**
	 * Methods reqiured by the Asset Manager to call to load and unload
	 */
    virtual error_t* Load(const char* file_path) = 0;
	virtual void Unload() = 0;

    virtual ~Asset() = default;
};

} // namespace Engine
