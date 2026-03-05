#include "scenes.hpp"

#include "raylib.h"

namespace Game {

void MainMenu::UpdateAndRender()
{
	ClearBackground(BLACK);
	DrawText("MainMenu", 0, 0, 20, RED);
}

} // namespace Game
