#include "asset.hpp"

#include "raylib.h"

namespace Engine {

class Texture : Asset {
public:
	virtual void Load(const char* file_path) override;
	virtual void Unload() override;

	const Texture2D& GetTexture() const { return m_Texture; }

private:
	Texture2D m_Texture;
};

} // namespace Engine
