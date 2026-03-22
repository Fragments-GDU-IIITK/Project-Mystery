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

    Global::Get().GoodGuy.Update();
    Global::Get().BadGuy.Update();
}

void InGame::drawChatBot(Npc& npc)
{
    if (ImGui::CollapsingHeader(npc.Name.c_str())) {
        // Input Area

        auto input_field_flags = 
            (npc.GetNetworkState() == Npc::NetworkState::kIdle)
            ? ImGuiInputTextFlags_EnterReturnsTrue 
            : ImGuiInputTextFlags_ReadOnly;

        if (ImGui::InputTextWithHint(TextFormat("##Message %s", npc.Name.c_str()), 
                                     "Write a message...", 
                                     npc.InputField, IM_ARRAYSIZE(npc.InputField), 
                                     input_field_flags))
        {
            npc.GetResponse();
        }

        ImGui::SameLine(); 

        if (ImGui::Button("Clear")) { npc.InputField[0] = '\0'; }

        // Preview Section
        ImGui::TextDisabled("Live Preview:");
        ImGui::BeginChild(TextFormat("Chat with %s", npc.Name.c_str()), 
                          ImVec2(0, 300), true);

        for (const auto& [message, reply] : npc.Chat)
        {
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
