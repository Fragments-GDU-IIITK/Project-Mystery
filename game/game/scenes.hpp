#pragma once

#include "global.hpp"

#include "engine/scene.hpp"

namespace Game {

enum class Scenes {
	kMainMenu,
	kInGame,
	kOptionsMenu,
	kScenesCount
};

class MainMenu : public Engine::Scene {
public:
	virtual void UpdateAndRender() override;
	virtual void GUI() override { }

	virtual const char* GetName() const override 
    {
        return "Main Menu";
    }
};

class OptionsMenu : public Engine::Scene {
public:
	virtual void UpdateAndRender() override;
	virtual void GUI() override { }

	virtual const char* GetName() const override
    {
        return "Options Menu";
    }
};

} // namespace Game
