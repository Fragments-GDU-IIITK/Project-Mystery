#include "asset_manager.hpp"

#include <type_traits>

namespace Engine {

template<typename T>
error_t* AssetManager::LoadAsset(int id, const char* file_path)
{
	static_assert(
		std::is_base_of<Asset, T>::value,
		"Can't Cast type to Engine::Asset*");

	auto res = m_AssetTable.emplace(id, std::make_shared<Asset>());

	return !res.second ? new error_t("Couldn't Insert this Type") : nullptr;
}

}
