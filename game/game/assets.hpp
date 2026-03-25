#pragma once

namespace Game {

enum class AssetID
{
    kTypeWriterFont1,
    kTypeWriterFont2,
    kTypeWriterFont3,
    kTypeWriterFont4,
    kTypeWriterFont5,
};

} // namespace Game

#define GET_FONT(font_id) \
    ::Engine::AssetManager::Get().GetAsset<::Engine::Font>(static_cast<int>(font_id))
