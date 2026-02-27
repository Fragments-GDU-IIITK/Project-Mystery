#include <print>

#include "engine/engine.hpp"
#include "raylib.h"

#include "init.hpp"

int main() {
	InitWindow(800, 600, "Hello World");

	Game::Initialize();

	while (!WindowShouldClose()) {
		BeginDrawing();
		ClearBackground(RAYWHITE);
		EndDrawing();
	}

	CloseWindow();
}
