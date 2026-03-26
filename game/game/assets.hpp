#pragma once

namespace Game {

enum class AssetID
{
    kFont1942,
    kFontSpecialElite,
    kFontSplendidB,
    kFontSplendidN,
    kFontatwriter,
    kFontTrovicalCalmFreeItalic,
    kFontTrovicalCalmFreeRegular
};

} // namespace Game

#define GET_FONT(font_id) \
    ::Engine::AssetManager::Get().GetAsset<::Engine::Font>(static_cast<int>(font_id))
