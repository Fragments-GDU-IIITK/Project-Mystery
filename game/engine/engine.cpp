#include "engine.hpp"
#include "perf.hpp"

#include "raylib.h"
#include "rlImGui.h"
#include "imgui.h"


namespace Engine {

error_t* Initialize()
{
	PERF_SCOPE();

	InitWindow(800, 600, "Hello World");
	rlImGuiSetup(true);

	Perf::Init();

	return nullptr;
}

void Shutdown()
{
	rlImGuiShutdown();
	CloseWindow();

	Perf::Shutdown();
}

} // namespace Engine
