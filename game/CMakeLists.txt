cmake_minimum_required(VERSION 4.0)

project(MysteryGame
		VERSION 0.1
		DESCRIPTION "Game with LLMs"
		LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 26)

## Submodules

### Json
add_subdirectory(json)

### Raylib
add_subdirectory(raylib)

### CPP-HTTPlib
add_subdirectory(cpp-httplib)

### Imgui
set(IMGUI_SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/imgui)
add_library(imgui STATIC
	${IMGUI_SOURCE_DIR}/imgui.cpp
	${IMGUI_SOURCE_DIR}/imgui_draw.cpp
	${IMGUI_SOURCE_DIR}/imgui_demo.cpp
	${IMGUI_SOURCE_DIR}/imgui_tables.cpp
	${IMGUI_SOURCE_DIR}/imgui_widgets.cpp
	${IMGUI_SOURCE_DIR}/backends/imgui_impl_opengl3.cpp
)
target_include_directories(imgui PUBLIC ${IMGUI_SOURCE_DIR})

### RlImgui
set(RLIMGUI_SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/rlImGui)
add_library(rlImgui STATIC
	${RLIMGUI_SOURCE_DIR}/rlImGuiColors.h
	${RLIMGUI_SOURCE_DIR}/rlImGui.cpp
	${RLIMGUI_SOURCE_DIR}/rlImGui.h
)
target_link_libraries(rlImgui raylib imgui)
target_include_directories(rlImgui PUBLIC ${IMGUI_SOURCE_DIR})

## Engine

add_library(engine STATIC
	engine/asset.hpp
	engine/asset_texture.cpp
	engine/asset_texture.hpp
	engine/asset_manager.hpp
	engine/asset_manager.cpp
	engine/engine.cpp
	engine/engine.hpp
	engine/error.cpp
	engine/error.hpp
	engine/main_loop.hpp
	engine/main_loop.cpp
	engine/perf.cpp
	engine/perf.hpp
	engine/scene.hpp
	engine/scene_manager.cpp
	engine/scene_manager.hpp
)

target_link_libraries(engine raylib imgui httplib rlImgui nlohmann_json::nlohmann_json)
target_include_directories(engine PUBLIC ${IMGUI_SOURCE_DIR})
target_include_directories(engine PUBLIC ${RLIMGUI_SOURCE_DIR})

## Game

add_executable(game
	game/main.cpp
	game/init.hpp
	game/init.cpp
	game/scenes.hpp
	game/scene_mainmenu.cpp
	game/scene_ingame.cpp
	game/scene_optionsmenu.cpp
)

target_link_libraries(game engine raylib imgui rlImgui httplib nlohmann_json::nlohmann_json)
target_include_directories(game PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_include_directories(game PUBLIC ${IMGUI_SOURCE_DIR})
target_include_directories(game PUBLIC ${RLIMGUI_SOURCE_DIR})

if (CMAKE_BUILD_TYPE STREQUAL "Debug")
	target_compile_definitions(engine PRIVATE DEBUG)
	target_compile_definitions(game PRIVATE DEBUG)
endif()

