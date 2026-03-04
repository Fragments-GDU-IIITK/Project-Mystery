#include "engine/engine.hpp"
#include "engine/main_loop.hpp"

#include "init.hpp"

#include "raylib.h"

// TODO(gowrish): handle kill signal (SIGINT) and have a clean exit

int main() {
	Engine::error_t* err;

	err = Engine::Initialize();
	if (err) {
		TraceLog(LOG_ERROR, "Failed To Initialize Engine: %s", err->Error().data());
		Engine::Shutdown();
		exit(EXIT_FAILURE);
	}

	err = Game::Initialize();

	if (err) {
		TraceLog(LOG_ERROR, "Failed To Initialize Game: %s", err->Error().data());
		Game::Shutdown();
		Engine::Shutdown();
		exit(EXIT_FAILURE);
	}

	TraceLog(LOG_INFO, "Initialized Game Successfully");

	Engine::Run();

	TraceLog(LOG_INFO, "Closing Game Now...");

	Game::Shutdown();

	Engine::Shutdown();

	TraceLog(LOG_INFO, "Bye");
}
