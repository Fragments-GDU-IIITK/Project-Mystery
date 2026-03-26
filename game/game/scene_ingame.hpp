#pragma once

#include "npc.hpp"
#include "assets.hpp"

#include "engine/scene.hpp"

#include "raylib.h"

namespace Game {

class InGame : public Engine::Scene {
private:
    void drawChatBot(Npc& npc);

public:
	virtual void UpdateAndRender() override;

    void drawInputTextArea();

	virtual void GUI() override;

	virtual const char* GetName() const override 
    {
        return "In Game";
    }

private:

    enum class ChatMode
    {
        kClosed,
        kOpening,
        kClosing,
        kOpened
    } m_ChatMode{ChatMode::kClosed};

    #define MAX_TEXTAREA_BUFFER_SIZE 1024

    struct {
        Rectangle BB{};
        float MovementDamp{0.01};
        float Epsilon{0.1};

        struct {
            char Buffer[MAX_TEXTAREA_BUFFER_SIZE];
            size_t len;
        } Text{0};

        AssetID FontID{AssetID::kFontSpecialElite};
        float FontSize{30};
        float FontSpacing{0.1};
        Color FontTint{WHITE};

    } m_InputArea;
};

} // namespace Game
