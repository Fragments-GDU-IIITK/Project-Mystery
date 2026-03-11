#include "imgui.h"
#include "rlImGui.h"
#include "raylib.h"

#include "perf.hpp"
#include "main_loop.hpp"
#include "scene_manager.hpp"

#include "engine.hpp"

namespace Engine {

void frameBegin()
{
	PERF_SCOPE();
	BeginTextureMode(Context::Get().render_target);
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
	
	EndTextureMode();

	BeginDrawing();

	rlImGuiBegin();
	

	ImGui::DockSpaceOverViewport();

	Engine::SceneManager::Get().GUI();

	// DrawTexture(Context::Get().render_target.texture, 0, 0, WHITE);

	ImGui::Begin("Main Window");
	rlImGuiImageRenderTexture(&Context::Get().render_target);
	ImGui::End();

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
