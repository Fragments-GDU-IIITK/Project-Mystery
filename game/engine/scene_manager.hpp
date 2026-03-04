#pragma once

#include "scene.hpp"

#include <vector>
#include <climits>
#include <memory>

#define INVALID_SCENE_INDEX INT_MAX

namespace Engine {

// Singleton
class SceneManager {
public:
	static SceneManager& Get()
	{
		static SceneManager instance{};
		return instance;
	}

	void UpdateAndRender();

	void InitializeScenes(std::vector<std::unique_ptr<Scene>> scenes);
	void SetNextScene(int scene_index);

private:
	SceneManager() = default;

private:
	std::vector<std::unique_ptr<Scene>> m_Scenes;

	int m_CurrentScene{INVALID_SCENE_INDEX};
	int m_NextScene{INVALID_SCENE_INDEX};
};

} // namespace Engine
