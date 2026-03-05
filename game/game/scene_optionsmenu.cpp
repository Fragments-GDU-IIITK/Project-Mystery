#include "scenes.hpp"

#include "raylib.h"

namespace Game {

void OptionsMenu::UpdateAndRender()
{
	ClearBackground(BLACK);
	DrawText("Options", 0, 0, 20, RED);
}

} // namespace Game
