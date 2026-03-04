#include "asset_texture.hpp"

namespace Engine {

void Texture::Load(const char* file_path)
{
	/**
	 * TODO(gowrish): What if the file_path doesnt exist?
	 * use Raylib::FileExists to see if it exists first, otherwise fallback to some
	 * default texture using this Raylib::GenImageChecked
	 */
	m_Texture = LoadTexture(file_path);
}

void Texture::Unload()
{
	UnloadTexture(m_Texture);
}

} // namespace Engine
