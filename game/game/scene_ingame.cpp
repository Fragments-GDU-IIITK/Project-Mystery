#include "scenes.hpp"

#include "raylib.h"

namespace Game {

void InGame::UpdateAndRender()
{
	ClearBackground(BLACK);
	DrawText("InGame", 0, 0, 20, RED);
}

} // namespace Game
