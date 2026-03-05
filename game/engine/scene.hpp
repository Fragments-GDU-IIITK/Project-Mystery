#pragma once

namespace Engine {

/**
 * All scenes will be allocated all at once, as this is a small game
 */
class Scene {
public:
	/**
	 * Coupled Update and Render because, when u update variables,
	 * they are already in the Cache, so just immediately use them
	 * for displaying, instead of updating all the entities, and then
	 * rendereing all of them, and by that time, the cache may not
	 * have what we want, so it'll be a bit slow
	 */
	virtual void UpdateAndRender() = 0;

	// For Debugging
	virtual const char* GetName() const = 0;
};

} // namespace Engine
