/**
 * Single place to edit character IDs, display names, avatars, and input hints.
 * Order in this array is left → right in the UI.
 *
 * `id` must match `character_id` values registered in the backend (e.g. character_model.json).
 */
export const CHARACTERS = [
    {
        id: "tara_001",
        displayName: "Tara",
        avatar: "./assets/scientist.svg",
        inputPlaceholder: "Message the Tara",
    },
    {
        id: "leo_001",
        displayName: "Leo",
        avatar: "./assets/rat.svg",
        inputPlaceholder: "Message the Leo",
    },
];
