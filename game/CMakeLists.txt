cmake_minimum_required(VERSION 4.0)

project(MysteryGame
		VERSION 0.1
		DESCRIPTION "Game with LLMs"
		LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 26)

## Submodules
add_subdirectory(raylib)

## Engine

add_library(engine 
	engine/engine.hpp
	engine/engine.cpp
	engine/error.hpp
	engine/error.cpp
)

target_link_libraries(engine raylib)

## Game

add_executable(game
	game/main.cpp
	game/init.hpp
	game/init.cpp
)
target_link_libraries(game engine raylib)
target_include_directories(game PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
