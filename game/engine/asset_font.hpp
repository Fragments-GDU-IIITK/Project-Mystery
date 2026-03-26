#pragma once

#include "asset.hpp"

#include "raylib.h"

namespace Engine {

class Font : public Asset {
public:
	virtual error_t* Load(const char* file_path) override;
	virtual void Unload() override;

    const ::Font& GetFont() const { return m_Font; }

private:
    ::Font m_Font;
};

} // namespace Engine
