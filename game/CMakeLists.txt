cmake_minimum_required(VERSION 4.0)

project(MysteryGame
		VERSION 0.1
		DESCRIPTION "Game with LLMs"
		LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 26)

## Submodules
add_subdirectory(raylib)

### Imgui
set(IMGUI_SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/imgui)
add_library(imgui STATIC
	${IMGUI_SOURCE_DIR}/imgui.cpp
	${IMGUI_SOURCE_DIR}/imgui_draw.cpp
	${IMGUI_SOURCE_DIR}/imgui_demo.cpp
	${IMGUI_SOURCE_DIR}/imgui_tables.cpp
	${IMGUI_SOURCE_DIR}/imgui_widgets.cpp
	# ${IMGUI_SOURCE_DIR}/backends/imgui_impl_glfw.cpp
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
	engine/engine.hpp
	engine/engine.cpp
	engine/error.hpp
	engine/error.cpp
	engine/perf.hpp
	engine/perf.cpp
)

target_link_libraries(engine raylib)

## Game

add_executable(game
	game/main.cpp
	game/init.hpp
	game/init.cpp
)
target_link_libraries(game engine raylib imgui rlImgui)
target_include_directories(game PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_include_directories(game PUBLIC ${IMGUI_SOURCE_DIR})
target_include_directories(game PUBLIC ${RLIMGUI_SOURCE_DIR})
