#include "init.hpp"

namespace Game {

Engine::error_t* initLoggers();
Engine::error_t* loadResources();
Engine::error_t* initStates();

Engine::error_t* Initialize()
{
	Engine::error_t* err{nullptr};

	err = initLoggers();
	if (err) return err;

	err = loadResources();
	if (err) return err;

	err = initLoggers();
	if (err) return err;

	return err;
}

Engine::error_t* initLoggers()
{
	return nullptr;
}

Engine::error_t* loadResources()
{
	return nullptr;
}

Engine::error_t* initStates()
{
	return nullptr;
}

} // namespace Game
