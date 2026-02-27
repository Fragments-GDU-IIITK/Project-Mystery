#include "init.hpp"

namespace Game {

Engine::error_t* initLoggers();
Engine::error_t* initResources();
Engine::error_t* initConfig();
Engine::error_t* initStates();

Engine::error_t* Initialize()
{
	return nullptr;
}

} // namespace Game
