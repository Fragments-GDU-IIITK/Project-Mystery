#include "asset_texture.hpp"

namespace Engine {

error_t* Texture::Load(const char* file_path)
{
	/**
	 * TODO(gowrish): What if the file_path doesnt exist?
	 * use Raylib::FileExists to see if it exists first, otherwise fallback to some
	 * default texture using this Raylib::GenImageChecked
	 */


    if (!FileExists(file_path))
    {
        return new error_t("Path %s Doesn't Exist", file_path);
    }

	m_Texture = LoadTexture(file_path);

    return nullptr;
}

void Texture::Unload()
{
	UnloadTexture(m_Texture);
}

} // namespace Engine
