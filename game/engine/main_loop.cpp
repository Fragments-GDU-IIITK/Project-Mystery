#include "imgui.h"
#include "rlImGui.h"
#include "raylib.h"

#include "perf.hpp"
#include "main_loop.hpp"
#include "scene_manager.hpp"


namespace Engine {

void frameBegin()
{
	PERF_SCOPE();

	BeginDrawing();
	rlImGuiBegin();
}

void frameUpdateAndRender()
{
	PERF_SCOPE();

	ClearBackground(RAYWHITE);
	Engine::SceneManager::Get().UpdateAndRender();
}

void frameEnd()
{
	PERF_SCOPE();

	rlImGuiEnd();
	EndDrawing();
}

void runFrame()
{
	PERF_SCOPE();

	frameBegin();

	frameUpdateAndRender();

	frameEnd();
}

void Run()
{
	while (!WindowShouldClose())
	{
		runFrame();
	}
}

} // namespace Engine
