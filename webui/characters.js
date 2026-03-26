/**
 * Single place to edit character IDs, display names, avatars, and input hints.
 * Order in this array is left → right in the UI.
 *
 * `id` must match `character_id` values registered in the backend (e.g. character_model.json).
 */
export const CHARACTERS = [
    {
        id: "scientist_001",
        displayName: "Scientist",
        avatar: "./assets/scientist.svg",
        inputPlaceholder: "Message the Scientist…",
    },
    {
        id: "rat_001",
        displayName: "Rat",
        avatar: "./assets/rat.svg",
        inputPlaceholder: "Message the Rat…",
    },
];
