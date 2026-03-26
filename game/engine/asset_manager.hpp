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
    // the implementation is required in the header file, cus we CPP (wilter flower x3)
	template<typename T>
	error_t* LoadAsset(int id, const char* file_path)
    {
        static_assert(
        std::is_base_of<Asset, T>::value,
        "Can't Cast type to Engine::Asset*");

        auto res = m_AssetTable.emplace(id, std::static_pointer_cast<Engine::Asset>(std::make_shared<T>()));

        if (!res.second) return new error_t("Couldn't Insert this Type");

        return m_AssetTable[id]->Load(file_path);
    }

    template <typename T>
    std::shared_ptr<T> GetAsset(int id) {
        auto it = m_AssetTable.find(id);
        if (it != m_AssetTable.end()) {
            return std::static_pointer_cast<T>(it->second);
        }
        return nullptr;
    }

    ~AssetManager()
    {
        for (const auto [id, asset] : m_AssetTable)
        {
            asset->Unload();
        }
    }

private:
	AssetManager() = default;

	std::unordered_map<int, std::shared_ptr<Asset>> m_AssetTable;
};

} // namespace Engine
