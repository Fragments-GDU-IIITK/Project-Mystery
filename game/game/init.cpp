#include "init.hpp"
#include "scenes.hpp"

#include <vector>
#include <memory>

#include "engine/scene_manager.hpp"
#include "engine/perf.hpp"

namespace Game {

Engine::error_t* initLoggers();
Engine::error_t* loadResources();
Engine::error_t* initStates();

Engine::error_t* Initialize()
{
	PERF_SCOPE();

	Engine::error_t* err{nullptr};

	err = initLoggers();
	if (err) return err;

	err = loadResources();
	if (err) return err;

	err = initStates();
	if (err) return err;

	return err;
}

Engine::error_t* initLoggers()
{
	PERF_SCOPE();

	return nullptr;
}

Engine::error_t* loadResources()
{
	PERF_SCOPE();
	return nullptr;
}

Engine::error_t* initStates()
{
	PERF_SCOPE();

	std::vector<std::unique_ptr<Engine::Scene>> scenes(static_cast<int>(Scenes::kScenesCount));

	// Would do this scenes[static_cast<int>(Scenes::kMainMenu)] = std::make_unique<MainMenu>();
#define INITIALIZE_SCENES(scene_name) \
	scenes[static_cast<int>(Scenes::k##scene_name)] = std::make_unique<scene_name>()

	INITIALIZE_SCENES(MainMenu);
	INITIALIZE_SCENES(InGame);
	INITIALIZE_SCENES(OptionsMenu);

#undef INITIALIZE_SCENES

	Engine::SceneManager::Get().InitializeScenes(std::move(scenes));

	Engine::SceneManager::Get().SetNextScene(static_cast<int>(Scenes::kMainMenu));

	return nullptr;
}

void Shutdown()
{
	PERF_SCOPE();
}

} // namespace Game
