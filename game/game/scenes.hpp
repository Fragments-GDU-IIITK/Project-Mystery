#pragma once

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
	virtual void GUI() override
	{
		
	}

	virtual const char* GetName() const { return "Main Menu"; }
};

class InGame : public Engine::Scene {
public:
	virtual void UpdateAndRender() override;
	virtual void GUI() override;

	virtual const char* GetName() const { return "In Game"; }
};

class OptionsMenu : public Engine::Scene {
public:
	virtual void UpdateAndRender() override;
	virtual void GUI() override
	{

	}

	virtual const char* GetName() const { return "Options Menu"; }
};

} // namespace Game
