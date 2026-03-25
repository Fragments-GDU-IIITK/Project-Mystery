#include "scene_ingame.hpp"

#include "engine/asset.hpp"
#include "engine/asset_font.hpp"
#include "engine/asset_manager.hpp"
#include "engine/scene_manager.hpp"
#include "game/assets.hpp"
#include "raylib.h"
#include "imgui.h"

#include "rlImGuiColors.h"

#include "global.hpp"

#define ABS(x) ((x) < 0 ? -(x) : (x))

namespace Game {

void InGame::UpdateAndRender()
{
    Global::Get().GoodGuy.Update();
    Global::Get().BadGuy.Update();

    ClearBackground(BLACK);
    DrawText("InGame", 0, 0, 20, RED);

    drawInputTextArea();
}

#define INPUT_AREA_MOUSE_TRIGGER_ZONE_START (0.9)

void InGame::drawInputTextArea()
{
    if (m_InputArea.BB.width == 0 || m_InputArea.BB.height == 0)
    {
        m_InputArea.BB.width = 0.8 * GetRenderWidth();
        m_InputArea.BB.height = GetRenderHeight();
        m_InputArea.BB.x = 0.1 * GetRenderWidth();
    }

    #define INPUT_AREA_OPENED_Y (0.6 * GetRenderHeight())
    #define INPUT_AREA_CLOSED_Y (0.9 * GetRenderHeight())

    switch (m_ChatMode)
    {
        case ChatMode::kClosed: {
            m_InputArea.BB.y = INPUT_AREA_CLOSED_Y;

            if (IsKeyPressed(KEY_SPACE))
                m_ChatMode = ChatMode::kOpening;

        } break;

        case ChatMode::kClosing: {
            
            float distance = INPUT_AREA_CLOSED_Y - m_InputArea.BB.y;

            if (ABS(distance) < m_InputArea.Epsilon)
            {
                m_InputArea.BB.y = INPUT_AREA_CLOSED_Y;
                m_ChatMode = ChatMode::kClosed;
            } else {
                m_InputArea.BB.y += distance * m_InputArea.MovementDamp;
            }

        } break;

        case ChatMode::kOpening: {
            
            float distance = m_InputArea.BB.y - INPUT_AREA_OPENED_Y;

            if (ABS(distance) < m_InputArea.Epsilon)
            {
                m_InputArea.BB.y = INPUT_AREA_OPENED_Y;
                m_ChatMode = ChatMode::kOpened;
            } else {
                m_InputArea.BB.y -= distance * m_InputArea.MovementDamp;
            }

        } break;

        case ChatMode::kOpened: {
            m_InputArea.BB.y = INPUT_AREA_OPENED_Y;

            if (IsKeyPressed(KEY_ESCAPE)) {
                m_ChatMode = ChatMode::kClosing;
                break;
            }

            if (IsKeyPressed(KEY_BACKSPACE))
                m_InputArea.Text.len--;

            char c = GetCharPressed();
            while (c) {
                m_InputArea.Text.Buffer[m_InputArea.Text.len++] = c;
                c = GetCharPressed();
            }

        } break;
    }

    DrawRectangleRec(m_InputArea.BB, RED);

    auto font = GET_FONT(m_InputArea.FontID);

    m_InputArea.Text.Buffer[m_InputArea.Text.len] = 0;
    DrawTextEx(font->GetFont(), m_InputArea.Text.Buffer, 
               Vector2{m_InputArea.BB.x, m_InputArea.BB.y}, 
               m_InputArea.FontSize, m_InputArea.FontSpacing, 
               m_InputArea.FontTint);
}

void InGame::drawChatBot(Npc& npc)
{
    if (ImGui::CollapsingHeader(npc.Name.c_str())) {
        // Input Area

        // make sure user can't input when the npc is streaming
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

    if (ImGui::CollapsingHeader("Input Area Properties"))
    {
        ImGui::Text("Chat Mode");
        
        int e = static_cast<int>(m_ChatMode);

        #define GUI_GEN_INPUTAREA_STATE_SWITCHER(state) \
            if (ImGui::RadioButton(#state, &e, static_cast<int>(ChatMode::state))) \
                m_ChatMode = ChatMode::state;

            GUI_GEN_INPUTAREA_STATE_SWITCHER(kOpened);
            ImGui::SameLine();
            GUI_GEN_INPUTAREA_STATE_SWITCHER(kOpening);
            ImGui::SameLine();
            GUI_GEN_INPUTAREA_STATE_SWITCHER(kClosing);
            ImGui::SameLine();
            GUI_GEN_INPUTAREA_STATE_SWITCHER(kClosed);

        #undef GUI_GEN_INPUTAREA_STATE_SWITCHER

        ImGui::SliderFloat("X", &m_InputArea.BB.x, 0, GetRenderWidth() * 2);
        ImGui::SliderFloat("Y", &m_InputArea.BB.y, 0, GetRenderHeight() * 2);

        ImGui::SliderFloat("Width", &m_InputArea.BB.width, 10, GetRenderWidth() * 2);
        ImGui::SliderFloat("Height", &m_InputArea.BB.height, 10, GetRenderHeight() * 2);

        ImGui::SliderFloat("Damp", &m_InputArea.MovementDamp, 0.001, 0.5);
        ImGui::SliderFloat("Epsilon", &m_InputArea.Epsilon, 0.001, 0.1);

        const char* fonts[] = { "Font 1", "Font 2", "Font 3", "Font 4", "Font 5" };
        static int font_index = 0;

        if (ImGui::Combo("Select Font", &font_index, fonts, IM_ARRAYSIZE(fonts)))
        {
            int base = static_cast<int>(AssetID::kTypeWriterFont1);
            int index = base + font_index;

            m_InputArea.FontID = static_cast<AssetID>(index);
        }

        ImGui::SliderFloat("Font Size", &m_InputArea.FontSize, 20, 50);
        ImGui::SliderFloat("Font Spacing", &m_InputArea.FontSpacing, 0.01, 1.0);

        ImVec4 imGuiColor = rlImGuiColors::Convert(m_InputArea.FontTint);

        if (ImGui::ColorEdit4("Color Picker", &imGuiColor.x, ImGuiColorEditFlags_PickerHueWheel))
        {
            m_InputArea.FontTint = rlImGuiColors::Convert(imGuiColor);
        }
    }
}

} // namespace Game
