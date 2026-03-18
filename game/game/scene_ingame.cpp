#include "scenes.hpp"

#include "raylib.h"
#include "imgui.h"

#include "global.hpp"

#include <vector>
#include <string>

namespace Game {

void InGame::UpdateAndRender()
{
	ClearBackground(BLACK);
	DrawText("InGame", 0, 0, 20, RED);
}

void drawChatBot(Npc& npc)
{
    if (ImGui::CollapsingHeader(npc.Name.c_str())) {
        // Input Area
        if (ImGui::InputTextWithHint("##Message NPC1", "Write a message...", 
                                     npc.InputField, IM_ARRAYSIZE(npc.InputField), 
                                     ImGuiInputTextFlags_EnterReturnsTrue))
        {
            npc.Chat.emplace_back(npc.InputField, "");
            npc.InputField[0] = '\0';
        }

        ImGui::SameLine(); 
        if(ImGui::Button("Clear")) { npc.InputField[0] = '\0'; }

        // Preview Section
        ImGui::TextDisabled("Live Preview:");
        ImGui::BeginChild("Chat with NPC 1", ImVec2(0, 300), true);
        for (const auto& [message, reply] : npc.Chat) {
            ImGui::TextWrapped("You: %s\n", message.c_str());
            ImGui::TextWrapped("%s: %s\n", npc.Name.c_str(), reply.c_str());
        }
        ImGui::EndChild();
    }	
}

void InGame::GUI()
{
    drawChatBot(Global::Get().GoodGuy);
    drawChatBot(Global::Get().BadGuy);
}

} // namespace Game
