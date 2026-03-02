#include <print>

#include "rlImGui.h"
#include "imgui.h"

#include "engine/engine.hpp"
#include "engine/perf.hpp"
#include "engine/scene_manager.hpp"

#include "init.hpp"

#include "raylib.h"

// TODO(gowrish): handle a kill signal and have a clean exit

/**
 * NOTE(gowrish): the scopes looks ugly af, but its fine cus ima move it to their own functions later, so we chil
 */
int main() {
	Engine::Perf::Init();

	{
		PERF_SCOPE();

		{
			PERF_SCOPE_NAME("Game Init");
			InitWindow(800, 600, "Hello World");
			rlImGuiSetup(true);
		}

		Engine::error_t* err = Game::Initialize();
		if (err) {
			TraceLog(LOG_ERROR, "Failed To Initialize Game");
			Engine::Perf::Shutdown();
			exit(EXIT_FAILURE);
		}

		TraceLog(LOG_INFO, "Initialized Game Successfully");

		while (!WindowShouldClose()) {
			PERF_SCOPE_NAME("MainLoop");

			{
				PERF_SCOPE_NAME("Frame Init");
				BeginDrawing();
				rlImGuiBegin();
			}

			{
				PERF_SCOPE_NAME("GAME");
				ClearBackground(RAYWHITE);
				Engine::SceneManager::Get().Run();
			}

			{
				PERF_SCOPE_NAME("Frame Cleanup");
				rlImGuiEnd();
				EndDrawing();
			}
		}

		{
			PERF_SCOPE_NAME("Game Shutdown");
			rlImGuiShutdown();
			CloseWindow();
		}
	}

	Engine::Perf::Shutdown();
}
