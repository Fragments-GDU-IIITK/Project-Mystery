#pragma once

#include "engine/error.hpp"

namespace Game {

/* Gotta initialize dem all
 * 1. Loggers
 * 2. Resources
 * 3. Config
 * 4. States
 */
Engine::error_t* Initialize();

void Shutdown();

} // namespace Game
