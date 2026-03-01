#include <print>

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

		while (!WindowShouldClose()) {
			BeginDrawing();
			ClearBackground(RAYWHITE);
			EndDrawing();
		}
		CloseWindow();
	}

	Engine::Perf::Shutdown();
}
