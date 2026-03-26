#include "init.hpp"
#include "engine/asset_font.hpp"
#include "engine/asset_manager.hpp"
#include "raylib.h"
#include "scenes.hpp"

#include "assets.hpp"

#include <vector>
#include <memory>

#include "engine/scene_manager.hpp"
#include "engine/perf.hpp"

#include "scene_ingame.hpp"

namespace Game {

Engine::error_t* initLoggers();
Engine::error_t* loadResources();
Engine::error_t* initStates();

Engine::error_t* Initialize()
{
	PERF_SCOPE();

	Engine::error_t* err{nullptr};

    SetExitKey(0);

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

    Engine::error_t* err{nullptr};

    #define LOAD_ASSET(_type, _id, _path)                                                   \
        err = Engine::AssetManager::Get().LoadAsset<_type>(static_cast<int>(_id), _path);   \
        if (err) return err;

        #define LOAD_FONT(name) \
            LOAD_ASSET(Engine::Font, AssetID::kFont##name, "./res/" #name ".ttf")

            LOAD_FONT(1942);
            LOAD_FONT(SpecialElite);
            LOAD_FONT(SplendidB);
            LOAD_FONT(SplendidN);
            LOAD_FONT(atwriter);
            LOAD_FONT(TrovicalCalmFreeItalic);
            LOAD_FONT(TrovicalCalmFreeRegular);


        #undef LOAD_FONT

    #undef LOAD_ASSET

	return err;
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

	Engine::SceneManager::Get().SetNextScene(static_cast<int>(Scenes::kInGame));

	return nullptr;
}

void Shutdown()
{
	PERF_SCOPE();
}

} // namespace Game
