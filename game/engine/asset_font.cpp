#include "asset_font.hpp"
#include "raylib.h"

namespace Engine {

error_t* Font::Load(const char* file_path)
{
	/**
	 * TODO(gowrish): What if the file_path doesnt exist?
	 * use Raylib::FileExists to see if it exists first, otherwise fallback to some
	 * default Font using this Raylib::GetFontDefault
	 */

    if (!FileExists(file_path))
    {
        return new error_t("Path %s Doesn't Exist", file_path);
    }

	m_Font = LoadFont(file_path);

    return nullptr;
}

void Font::Unload()
{
	UnloadFont(m_Font);
}

} // namespace Engine
