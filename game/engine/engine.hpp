#pragma once

#include "error.hpp"
#include "raylib.h"

namespace Engine {

struct Context
{
	int window_width;
	int window_height;

	RenderTexture2D render_target;

	static Context& Get()
	{
		static Context instance{};
		return instance;
	}
};


error_t* Initialize();

void Shutdown();

} // namespace Engine
