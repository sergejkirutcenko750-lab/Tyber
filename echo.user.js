// ==UserScript==
// @name         Эхо для игры Целуй и знакомься
// @version      1.2
// @description  Повторяет сообщения выбранного игрока
// @match        *://*.vk.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    let targetName = "Руки";
    let enabled = false;
    function log(m) { console.log("[Эхо] " + m); }
    function getInputField() {
        return document.querySelector(".chat-input__input.js-input") ||
               document.querySelector("textarea") ||
               document.querySelector("input[type='text']");
    }
    function getSendButton() {
        return document.querySelector(".chat-input__send.js-button") ||
               document.querySelector("button[type='submit']") ||
               document.querySelector("button.chat__send");
    }
    function addControls() {
        if (document.getElementById("echoPanel")) return;
        const panel = document.createElement("div");
        panel.id = "echoPanel";
        panel.style.cssText = "position:fixed;bottom:80px;right:20px;z-index:9999;background:#2c3e50;color:white;padding:8px;border-radius:8px;display:flex;gap:8px;font-family:sans-serif;font-size:14px;";
        panel.innerHTML = `<input id="echoNick" type="text" placeholder="Ник цели" value="${targetName}" style="background:#34495e;color:white;border:1px solid #61dafb;border-radius:4px;padding:4px;width:100px;">
            <button id="echoSet" style="background:#61dafb;color:black;border:none;border-radius:4px;padding:4px 8px;cursor:pointer;">Уст</button>
            <button id="echoToggle" style="background:#61dafb;color:black;border:none;border-radius:4px;padding:4px 8px;cursor:pointer;">OFF</button>`;
        document.body.appendChild(panel);
        document.getElementById("echoSet").onclick = () => {
            let n = document.getElementById("echoNick").value.trim();
            if (n) { targetName = n; log("Ник: " + targetName); }
        };
        document.getElementById("echoToggle").onclick = (e) => {
            enabled = !enabled;
            e.target.textContent = enabled ? "ON" : "OFF";
            log(enabled ? "Включён" : "Выключен");
        };
    }
    function watchMessages() {
        setInterval(() => {
            if (!enabled) return;
            document.querySelectorAll(".chat__message").forEach(msg => {
                if (msg.getAttribute("data-echo")) return;
                let nameEl = msg.querySelector(".chat__sender-name");
                let textEl = msg.querySelector(".chat__word-break");
                if (nameEl && textEl && nameEl.textContent.trim() === targetName) {
                    msg.setAttribute("data-echo", "1");
                    let text = textEl.textContent.trim();
                    log("Найдено: " + text);
                    setTimeout(() => {
                        let input = getInputField(), btn = getSendButton();
                        if (input && btn) {
                            input.value = text;
                            input.dispatchEvent(new Event("input", { bubbles: true }));
                            btn.click();
                        }
                    }, 200);
                }
            });
        }, 500);
    }
    addControls();
    watchMessages();
})();
