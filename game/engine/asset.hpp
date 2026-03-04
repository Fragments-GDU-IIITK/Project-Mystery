#pragma once

namespace Engine {

class Asset
{
public:

	/**
	 * Methods reqiured by the Asset Manager to call to load and unload
	 */
	virtual void Load(const char* file_path) = 0;
	virtual void Unload() = 0;
};

} // namespace Engine
