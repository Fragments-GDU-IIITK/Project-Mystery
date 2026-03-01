#include <print>

#include "rlImGui.h"
#include "imgui.h"

#include "engine/engine.hpp"
#include "engine/perf.hpp"

#include "init.hpp"

#include "raylib.h"


int main() {
	Engine::Perf::Init();

	{
		PERF_SCOPE();

		InitWindow(800, 600, "Hello World");

		Engine::error_t* err = Game::Initialize();
		if (err) {
			TraceLog(LOG_ERROR, "Failed To Initialize Game");
			exit(EXIT_FAILURE);
		}
		TraceLog(LOG_INFO, "Initialized Game Successfully");

		rlImGuiSetup(true);

		while (!WindowShouldClose()) {
			BeginDrawing();
			rlImGuiBegin();

			bool open = true;
			ImGui::ShowDemoWindow(&open);

			ClearBackground(RAYWHITE);

			rlImGuiEnd();
			EndDrawing();
		}

		rlImGuiShutdown();

		CloseWindow();
	}

	Engine::Perf::Shutdown();
}
