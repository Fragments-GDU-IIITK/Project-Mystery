import { CHARACTERS } from "./characters.js";

const API_URL = "http://localhost:3000/project_mystery_backend/0.1.0/chat/";

function scrollChatsToBottom(chatsEl) {
    chatsEl.scrollTop = chatsEl.scrollHeight;
}

function appendUserMessage(chatsEl, text) {
    const wrap = document.createElement("div");
    wrap.className = "Message RightMessage";
    const p = document.createElement("p");
    p.textContent = text;
    wrap.appendChild(p);
    chatsEl.appendChild(wrap);
    scrollChatsToBottom(chatsEl);
}

function beginAssistantMessage(chatsEl) {
    const wrap = document.createElement("div");
    wrap.className = "Message LeftMessage";
    const p = document.createElement("p");
    p.textContent = "";
    wrap.appendChild(p);
    chatsEl.appendChild(wrap);
    scrollChatsToBottom(chatsEl);
    return p;
}

function createChatAreaColumn(character, index) {
    const area = document.createElement("div");
    area.className = "ChatArea";
    area.id = "NPC-" + String(index + 1);
    area.dataset.characterId = character.id;

    const header = document.createElement("header");
    header.className = "ChatHeader";

    const img = document.createElement("img");
    img.className = "CharacterAvatar";
    img.src = character.avatar;
    img.width = 44;
    img.height = 44;
    img.alt = character.displayName;

    const nameEl = document.createElement("span");
    nameEl.className = "CharacterName";
    nameEl.textContent = character.displayName;

    header.appendChild(img);
    header.appendChild(nameEl);

    const chats = document.createElement("div");
    chats.className = "Chats";
    chats.setAttribute("aria-live", "polite");
    chats.setAttribute("aria-relevant", "additions text");

    const inputArea = document.createElement("div");
    inputArea.className = "InputArea";

    const input = document.createElement("input");
    input.className = "InputAreaBox";
    input.type = "text";
    input.autocomplete = "off";
    input.placeholder =
        character.inputPlaceholder != null && character.inputPlaceholder !== ""
            ? character.inputPlaceholder
            : "Message " + character.displayName + "…";

    const sendBtn = document.createElement("button");
    sendBtn.type = "button";
    sendBtn.className = "SendButton";
    sendBtn.textContent = "Send";

    inputArea.appendChild(input);
    inputArea.appendChild(sendBtn);

    area.appendChild(header);
    area.appendChild(chats);
    area.appendChild(inputArea);

    return area;
}

function setupChatArea(chatArea) {
    const characterId = chatArea.dataset.characterId;
    const chatsEl = chatArea.querySelector(".Chats");
    const input = chatArea.querySelector(".InputAreaBox");
    const sendBtn = chatArea.querySelector(".SendButton");
    let busy = false;

    async function send() {
        const prompt = input.value.trim();
        if (!prompt || busy) return;

        busy = true;
        input.value = "";
        appendUserMessage(chatsEl, prompt);
        const replyP = beginAssistantMessage(chatsEl);

        sendBtn.disabled = true;
        input.disabled = true;

        try {
            const res = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt,
                    character_id: characterId,
                }),
            });

            if (!res.ok) {
                const errBody = await res.text();
                replyP.textContent =
                    "Request failed (" +
                    res.status +
                    "). " +
                    (errBody ? errBody.slice(0, 300) : res.statusText);
                return;
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            for (;;) {
                const { done, value } = await reader.read();
                if (done) break;
                replyP.textContent += decoder.decode(value, { stream: true });
                scrollChatsToBottom(chatsEl);
            }
            replyP.textContent += decoder.decode();
        } catch (err) {
            replyP.textContent =
                "Could not reach the server. If this page is not served from the same origin as the API, enable CORS on the backend or open the UI via the same host as port 3000. (" +
                err.message +
                ")";
        } finally {
            busy = false;
            sendBtn.disabled = false;
            input.disabled = false;
            input.focus();
            scrollChatsToBottom(chatsEl);
        }
    }

    sendBtn.addEventListener("click", send);
    input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();
            send();
        }
    });
}

function mountChats() {
    const holder = document.getElementById("ChatHolder");
    if (!holder) return;

    holder.replaceChildren();
    CHARACTERS.forEach(function (character, index) {
        const column = createChatAreaColumn(character, index);
        holder.appendChild(column);
        setupChatArea(column);
    });
}

mountChats();
