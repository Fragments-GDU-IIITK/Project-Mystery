#include "scene_manager.hpp"
#include "perf.hpp"

#include <cassert>

#include "raylib.h"
#include "imgui.h"

namespace Engine {

// TODO(gowrish): Add logs and tracing to all of these

void SceneManager::GUI()
{
	PERF_SCOPE();

	ImGui::Begin("Scene Selector");
	for (int i = 0; i < m_Scenes.size(); i++) {
		if (ImGui::CollapsingHeader(TextFormat("%s", m_Scenes[i]->GetName()))) {
			if (ImGui::Button(TextFormat("Switch to %s", m_Scenes[i]->GetName()))) {
				SceneManager::Get().SetNextScene(i);
			}
			m_Scenes[i]->GUI();
		}
	}
	ImGui::End();
}

void SceneManager::UpdateAndRender()
{
	PERF_SCOPE();

	if (m_Scenes.size() < 0) return;

	if (m_NextScene != INVALID_SCENE_INDEX) {
		m_CurrentScene = m_NextScene;
		m_NextScene = INVALID_SCENE_INDEX;
	}

	// m_CurrentScene is guarenteed to be in range cus SetNextScene would check it
	m_Scenes[m_CurrentScene]->UpdateAndRender();
}

void SceneManager::InitializeScenes(std::vector<std::unique_ptr<Scene>> scenes)
{
	PERF_SCOPE();

	m_Scenes = std::move(scenes);

	TraceLog(LOG_INFO, "Scenes Initialized");
	for (int i = 0; i < m_Scenes.size(); i++) {
		TraceLog(LOG_INFO, "\tScene: %s", m_Scenes[i]->GetName());
	}
}

void SceneManager::SetNextScene(int scene_index)
{
	PERF_SCOPE();

	assert(
		0 <= scene_index &&
		scene_index < m_Scenes.size() &&
		"SetNextScene got an invalid index");

	m_NextScene = scene_index;

	// TODO(gowrish) : Better loggin
	TraceLog(LOG_INFO, "Switching Next Scene to ID:%d", m_NextScene);
}

}
