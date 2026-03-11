#include "engine.hpp"
#include "perf.hpp"

#include "raylib.h"
#include "rlImGui.h"
#include "imgui.h"


namespace Engine {

error_t* Initialize()
{
	PERF_SCOPE();

	SetConfigFlags(FLAG_WINDOW_RESIZABLE);

	InitWindow(Context::Get().window_width, 
			   Context::Get().window_height, 
			   "Hello World");

	rlImGuiSetup(true);

	Context::Get().window_width = 800;
	Context::Get().window_height = 600;

	Context::Get().render_target = LoadRenderTexture(Context::Get().window_width, 
						  							 Context::Get().window_height);

	Perf::Init();

	ImGui::GetIO().ConfigFlags |= ImGuiConfigFlags_DockingEnable;

	return nullptr;
}

void Shutdown()
{
	rlImGuiShutdown();
	CloseWindow();

	Perf::Shutdown();
}

} // namespace Engine
