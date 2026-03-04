#pragma once

#include "error.hpp"
#include "asset.hpp"

#include <unordered_map>
#include <memory>

namespace Engine {

class AssetManager {
public:
	static AssetManager& Get()
	{
		static AssetManager instance{};
		return instance;
	}

	// TODO(gowrish): Maybe int might not be the best type here
	template<typename T>
	error_t* LoadAsset(int id, const char* file_path);

private:
	AssetManager() = default;

	std::unordered_map<int, std::shared_ptr<Asset>> m_AssetTable;
};

} // namespace Engine
