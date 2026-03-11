#include "scenes.hpp"

#include "raylib.h"
#include "imgui.h"

#include <vector>
#include <string>

namespace Game {

void InGame::UpdateAndRender()
{
	ClearBackground(BLACK);
	DrawText("InGame", 0, 0, 20, RED);
}

void InGame::GUI()
{
	if (ImGui::CollapsingHeader("NPC 1")) {
		static std::vector<std::string> messages_2_npc1{};
		static char buf1[256] = "";

		// Input Area
		if (ImGui::InputTextWithHint("##Message NPC1", "Write a message...", buf1, IM_ARRAYSIZE(buf1), ImGuiInputTextFlags_EnterReturnsTrue))
		{
			messages_2_npc1.emplace_back(buf1);
			buf1[0] = '\0';
		}

		ImGui::SameLine(); 
		if(ImGui::Button("Clear")) { buf1[0] = '\0'; }

		// Preview Section
		ImGui::TextDisabled("Live Preview:");
		ImGui::BeginChild("Chat with NPC 1", ImVec2(0, 300), true);
		for (std::string_view str : messages_2_npc1)
			ImGui::TextWrapped("%s\n", str.data());
		ImGui::EndChild();
	}	

	if (ImGui::CollapsingHeader("NPC 2")) {
		static std::vector<std::string> messages_2_npc2{};
		static char buf2[256] = "";

		// Input Area
		if (ImGui::InputTextWithHint("##Message NPC1", "Write a message...", buf2, IM_ARRAYSIZE(buf2), ImGuiInputTextFlags_EnterReturnsTrue))
		{
			messages_2_npc2.emplace_back(buf2);
			buf2[0] = '\0';
		}

		ImGui::SameLine(); 
		if(ImGui::Button("Clear")) { buf2[0] = '\0'; }

		// Preview Section
		ImGui::TextDisabled("Live Preview:");
		ImGui::BeginChild("Chat with NPC 2", ImVec2(0, 300), true);
		for (std::string_view str : messages_2_npc2)
			ImGui::TextWrapped("%s\n", str.data());
		ImGui::EndChild();
	}	
}

} // namespace Game
