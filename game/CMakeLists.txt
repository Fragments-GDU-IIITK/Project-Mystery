cmake_minimum_required(VERSION 4.0)

project(MysteryGame
		VERSION 0.1
		DESCRIPTION "Game with LLMs"
		LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 26)

add_library(engine engine/engine.cpp)

add_executable(game game/main.cpp)
target_link_libraries(game engine)
target_include_directories(game PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/engine)
