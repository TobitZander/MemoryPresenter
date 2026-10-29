const socket = io();
let state = null;
let previousMatchStatus = null;
let pendingRevealIndex = null;
let selectedColumn = null;
let selectedRow = null;
let hoveredCardIndex = null;

function showMatchCelebration() {
    const celebration = document.getElementById("matchCelebration");
    if (!celebration) return;
    celebration.innerHTML = '<strong>🎉</strong>' +
        Array.from({length: 28}, (_, index) =>
            `<i style="--particle-angle:${index * (360 / 28)}deg;--particle-distance:${140 + (index % 5) * 34}px;--particle-color:hsl(${index * 47 % 360} 85% 55%)"></i>`
        ).join("");
    celebration.classList.remove("active");
    void celebration.offsetWidth;
    celebration.classList.add("active");
    window.setTimeout(() => celebration.classList.remove("active"), 3000);
}

function formatTime(seconds) {
    return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}
function formatMismatchTime(seconds) {
    return `Noch offen: ${Math.max(0, Math.ceil(seconds))}s`;
}
function publishZoomTransform() {
    socket.emit("zoom_transform", {
        scale: zoomScale,
        offset_x: zoomOffsetX,
        offset_y: zoomOffsetY
    });
}

function openSelection() {
    if (selectedColumn === null || selectedRow === null) return;
    const cardIndex = selectedRow * state.grid_cols + selectedColumn;
    const card = state.cards[cardIndex];
    if (!card || card.open || card.matched) {
        selectedColumn = null;
        selectedRow = null;
        socket.emit("selection", { column: null, row: null });
        return;
    }
    pendingRevealIndex = cardIndex;
    socket.emit("open_card", { card: cardIndex });
    socket.emit("selection", { column: null, row: null });
}

function update(stateData) {
    if (stateData.match_status === "match" && previousMatchStatus !== "match") {
        showMatchCelebration();
    }
    previousMatchStatus = stateData.match_status;
    state = stateData;
    if (pendingRevealIndex !== null) {
        const pendingCard = state.cards[pendingRevealIndex];
        if (!pendingCard || (!pendingCard.open && !pendingCard.matched)) {
            pendingRevealIndex = null;
        }
    }
    document.body.classList.toggle("light-mode", state.theme === "light");
    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) themeToggle.textContent = state.theme === "light" ? "Dark-Mode" : "White-Mode";
    const pauseToggle = document.getElementById("pauseToggle");
    if (pauseToggle) {
        const timerPaused = state.paused || state.match_status === "match";
        pauseToggle.textContent = "Pause";
        pauseToggle.classList.toggle("pause-active", timerPaused);
        pauseToggle.setAttribute("aria-pressed", String(timerPaused));
    }
    const settings = document.getElementById("settings");
    const settingsToggle = document.getElementById("settingsToggle");
    if (settingsToggle && settings) {
        settingsToggle.setAttribute("aria-expanded", String(!settings.hidden));
    }
    selectedColumn = state.selected_column;
    selectedRow = state.selected_row;
    const hoveredCard = state.hovered_card;
    hoveredCardIndex = hoveredCard;
    const hoveredColumn = hoveredCard === null ? null : hoveredCard % state.grid_cols;
    const hoveredRow = hoveredCard === null ? null : Math.floor(hoveredCard / state.grid_cols);
    const memoryName = document.getElementById("memoryName");
    if (memoryName) memoryName.textContent = state.memory;
    const memoryList = document.getElementById("memoryList");
    if (memoryList) {
        memoryList.innerHTML = state.memory_sets.map((memory) =>
            `<button type="button" class="${memory === state.memory ? "current" : ""}" data-memory="${memory}">${memory}</button>`
        ).join("");
    }
    const active = document.getElementById("activeTeam");
    const time = document.getElementById("time");
    if (active) active.textContent = state.team_names[state.active_team];
    if (time) {
        time.hidden = state.mismatch_time !== null;
        time.textContent = formatTime(state.time);
        time.className = state.mismatch_time !== null
            ? ""
            : state.time <= 10 ? "danger" : state.time <= 20 ? "warning" : "";
    }
    const mismatchTime = document.getElementById("mismatchTime");
    if (mismatchTime) {
        mismatchTime.hidden = state.mismatch_time === null;
        mismatchTime.textContent = state.mismatch_time === null
            ? ""
            : formatMismatchTime(state.mismatch_time);
        mismatchTime.className = state.mismatch_time === null ? "" : "mismatch-active";
    }
    const matchStatus = document.getElementById("matchStatus");
    if (matchStatus) {
        matchStatus.textContent = state.match_status === "match"
            ? "✅"
            : state.match_status === "mismatch"
            ? "❌"
            : "";
        matchStatus.setAttribute("aria-label", state.match_status === "match"
            ? "Treffer"
            : state.match_status === "mismatch"
            ? "Fehlversuch"
            : "");
    }
    const teamList = document.querySelector(".teams");
    const visibleTeams = state.visible_teams || state.team_names.map((_, index) => index);
    if (teamList && teamList.children.length !== visibleTeams.length) {
        teamList.innerHTML = visibleTeams.map(() => "<li class=\"team\"></li>").join("");
    }
    document.querySelectorAll(".team").forEach((element, index) => {
        const teamIndex = visibleTeams[index];
        element.textContent = `${teamIndex + 1}. ${state.team_names[teamIndex]}: ${state.scores[teamIndex]}`;
        element.classList.toggle("active", teamIndex === state.active_team);
    });
    const tiebreakButton = document.getElementById("tiebreakButton");
    if (tiebreakButton) tiebreakButton.hidden = !state.tiebreak_pending;
    const board = document.querySelector(".board");
    if (board) {
        board.style.gridTemplateColumns = `repeat(${state.grid_cols}, minmax(0, 1fr))`;
        board.style.gridTemplateRows = `repeat(${state.grid_rows}, minmax(0, 1fr))`;
        if (board.children.length !== state.grid_rows * state.grid_cols) {
            board.innerHTML = Array.from({length: state.grid_rows * state.grid_cols}, () => '<button class="card" type="button"></button>').join("");
        }
    }
    document.querySelectorAll(".letters").forEach((letters) => {
        letters.style.gridTemplateColumns = `repeat(${state.grid_cols}, minmax(0, 1fr))`;
        letters.innerHTML = Array.from({length: state.grid_cols}, (_, index) => `<span>${String.fromCharCode(65 + index)}</span>`).join("");
    });
    document.querySelectorAll(".row-numbers").forEach((rows) => {
        rows.style.gridTemplateRows = `repeat(${state.grid_rows}, minmax(0, 1fr))`;
        rows.innerHTML = Array.from({length: state.grid_rows}, (_, index) => `<span>${index + 1}</span>`).join("");
    });
    document.querySelectorAll(".letters span").forEach((element, index) => {
        element.classList.toggle("selected", index === selectedColumn || index === hoveredColumn);
    });
    document.querySelectorAll(".row-numbers span").forEach((element, index) => {
        element.classList.toggle("selected", index === selectedRow || index === hoveredRow);
    });
    document.querySelectorAll(".card").forEach((element, index) => {
        const card = state.cards[index];
        if (!card) {
            element.hidden = false;
            element.className = "card empty";
            element.removeAttribute("data-index");
            element.removeAttribute("title");
            delete element.dataset.renderState;
            delete element.dataset.revealPending;
            element.replaceChildren();
            return;
        }
        element.hidden = false;
        const column = index % state.grid_cols;
        const row = Math.floor(index / state.grid_cols);
        const displayHovered = document.body.classList.contains("display") && index === hoveredCard;
        const wasRevealed = element.classList.contains("revealed");
        const wasAnimating = Boolean(element.querySelector(".card-face.reveal-animation"));
        const revealPending = element.dataset.revealPending === "true";
        element.className = `card${card.open || card.matched ? " revealed" : ""}${card.matched ? " matched" : ""}${column === selectedColumn || displayHovered ? " selected-column" : ""}${row === selectedRow ? " selected-row" : ""}`;
        element.style.setProperty("--pair-color", card.pair_color);
        element.dataset.index = index;
        if (card.open || card.matched) {
            const imageUrl = new URL(card.image_path, window.location.href).href;
            if (revealPending) {
                element.className = `card reveal-pending${column === selectedColumn || displayHovered ? " selected-column" : ""}${row === selectedRow ? " selected-row" : ""}`;
                element.dataset.renderState = "loading";
                return;
            }
            let image = element.querySelector("img");
            if (!image || image.src !== imageUrl) {
                element.dataset.revealPending = "true";
                element.className = `card reveal-pending${column === selectedColumn || displayHovered ? " selected-column" : ""}${row === selectedRow ? " selected-row" : ""}`;
                element.innerHTML = "";
                const preloader = new Image();
                let finished = false;
                const finishPreload = () => {
                    if (finished) return;
                    finished = true;
                    if (!element.isConnected || element.dataset.index !== String(index)) return;
                    const currentCard = state && state.cards[index];
                    if (!currentCard || (!currentCard.open && !currentCard.matched)) {
                        delete element.dataset.revealPending;
                        return;
                    }
                    preloader.draggable = false;
                    preloader.alt = "Gefundene Karte";
                    const face = document.createElement("span");
                    face.className = "card-face reveal-animation";
                    face.append(preloader);
                    element.replaceChildren(face);
                    delete element.dataset.revealPending;
                    element.className = `card revealed${currentCard.matched ? " matched" : ""}${column === selectedColumn || displayHovered ? " selected-column" : ""}${row === selectedRow ? " selected-row" : ""}`;
                    element.dataset.renderState = "image";
                    face.addEventListener("animationend", (event) => {
                        if (event.animationName === "card-flip-in") {
                            face.classList.remove("reveal-animation");
                        }
                    }, {once: true});
                };
                preloader.addEventListener("load", () => {
                    if (typeof preloader.decode === "function") {
                        preloader.decode().then(finishPreload).catch(finishPreload);
                    } else {
                        finishPreload();
                    }
                }, {once: true});
                preloader.addEventListener("error", finishPreload, {once: true});
                preloader.src = imageUrl;
                element.dataset.renderState = "loading";
                return;
            }
            const shouldAnimate = !wasRevealed || pendingRevealIndex === index;
            if (shouldAnimate && !wasAnimating) {
                const face = element.querySelector(".card-face");
                if (!face) return;
                face.classList.add("reveal-animation");
                face.addEventListener("animationend", (event) => {
                    if (event.animationName === "card-flip-in") {
                        face.classList.remove("reveal-animation");
                    }
                }, {once: true});
                if (pendingRevealIndex === index) pendingRevealIndex = null;
            }
            element.dataset.renderState = "image";
            if (document.body.classList.contains("moderator")) {
                element.title = card.description || "";
            }
        } else if (document.body.classList.contains("moderator")) {
            delete element.dataset.revealPending;
            element.innerHTML = `<span class="pair-label" style="--pair-color:${card.pair_color}">${card.display_pair_id}</span>`;
            element.dataset.renderState = "label";
        } else {
            delete element.dataset.revealPending;
            element.title = "";
            if (element.dataset.renderState !== "back") {
                element.innerHTML = `<img class="card-back" src="/card-back" alt="Verdeckte Karte">`;
                element.dataset.renderState = "back";
            }
        }
    });
    const descriptionPanels = document.querySelectorAll(".card-description-panel");
    if (descriptionPanels.length) {
        const descriptionIndices = state.description_card_indices || [];
        descriptionPanels.forEach((panel, panelIndex) => {
            const describedCard = descriptionIndices[panelIndex] === undefined
                ? null
                : state.cards[descriptionIndices[panelIndex]];
            panel.textContent = describedCard && describedCard.description
                ? describedCard.description
                : "Noch keine Karte geöffnet.";
            panel.classList.toggle("has-description", Boolean(describedCard && describedCard.description));
        });
    }
    const winner = document.getElementById("winner");
    if (winner) {
        winner.hidden = state.winner === null;
        if (state.winner !== null) {
            const rankingIndices = state.tiebreak_pending
                ? state.winner
                : state.team_names.map((_, index) => index);
            const ranking = rankingIndices.map((index) => ({
                score: state.scores[index],
                index
            }))
                .sort((a, b) => b.score - a.score);
            let previousScore = null;
            let competitionRank = 0;
            const groupedRanking = [];
            ranking.forEach(({score, index}, indexInRanking) => {
                if (score !== previousScore) competitionRank = indexInRanking + 1;
                previousScore = score;
                const group = groupedRanking[groupedRanking.length - 1];
                if (group && group.rank === competitionRank) {
                    group.names.push(state.team_names[index]);
                } else {
                    groupedRanking.push({
                        rank: competitionRank,
                        score,
                        names: [state.team_names[index]]
                    });
                }
            });
            const medals = {1: "🥇", 2: "🥈", 3: "🥉"};
            const winners = groupedRanking.map((group) => {
                const rankLabel = medals[group.rank] || `${group.rank}.`;
                return `${rankLabel} ${group.names.join(", ")} (${group.score} Punkte)`;
            });
            winner.className = `winner display-winner winner-count-${state.winner.length}${state.tiebreak_pending ? " pending-tiebreak" : ""}`;
            const heading = state.tiebreak_pending
                ? "🏆 Zwischenstand – Zusatzrunde erforderlich"
                : "🏆 Gewinner";
            winner.innerHTML = `<strong>${heading}</strong><div class="winner-results">${winners.join("<br>")}</div>`;
        }
    }
    const enlarged = state.zoom_card === null ? null : state.cards[state.zoom_card];
    const lightbox = document.getElementById("lightbox");
    if (lightbox) {
        lightbox.hidden = !enlarged || !(enlarged.open || enlarged.matched);
        if (enlarged && (enlarged.open || enlarged.matched)) {
            const closeButton = document.body.classList.contains("moderator")
                ? '<button class="lightbox-close" type="button">Schließen (Esc)</button>'
                : "";
            const description = document.body.classList.contains("moderator") && enlarged.description
                ? `<p class="image-description">${enlarged.description}</p>` : "";
            const currentImage = lightbox.querySelector("img");
            const imageUrl = new URL(enlarged.image_path, window.location.href).href;
            if (!currentImage || currentImage.src !== imageUrl) {
                lightbox.innerHTML = `<img draggable="false" src="${enlarged.image_path}" alt="Vergrößerte Karte">${description}${closeButton}`;
            }
            zoomScale = state.zoom_scale;
            zoomOffsetX = state.zoom_offset_x;
            zoomOffsetY = state.zoom_offset_y;
            applyZoomTransform();
        }
    }
    const rules = document.getElementById("rules");
    if (rules) rules.hidden = !state.rules_visible;
    ["settingRows", "settingCols", "settingTeams", "settingRoundTime", "settingCloseDelay"].forEach((id) => {
        const input = document.getElementById(id);
        if (input && document.activeElement !== input) {
            const values = {
                settingRows: state.grid_rows, settingCols: state.grid_cols,
                settingTeams: state.team_names.length, settingRoundTime: state.round_time_seconds,
                settingCloseDelay: state.auto_close_delay
            };
            input.value = values[id];
        }
    });
    const randomMemories = document.getElementById("settingRandomMemories");
    if (randomMemories) randomMemories.checked = state.randomize_all_memories;
}

socket.on("state", update);
socket.on("error_message", (data) => window.alert(data.message));
socket.on("server_shutdown", () => window.close());
window.addEventListener("load", () => socket.emit("request_state"));
document.addEventListener("keydown", (event) => {
    if (!state) return;
    if (event.ctrlKey && event.key.toLowerCase() === "p") {
        event.preventDefault();
        socket.emit("toggle_pause");
        return;
    }
    if (/^[a-fA-F]$/.test(event.key)) selectedColumn = event.key.toUpperCase().charCodeAt(0) - 65;
    if (/^[1-9]$/.test(event.key)) selectedRow = Number(event.key) - 1;
    if (/^[a-fA-F]$/.test(event.key) || /^[1-9]$/.test(event.key)) {
        socket.emit("selection", {column: selectedColumn, row: selectedRow});
    }
    if (event.code === "Escape") {
        selectedRow = null;
        selectedColumn = null;
        socket.emit("selection", {column: null, row: null});
        socket.emit("zoom", {card: null});
    }
    if (event.code === "Space") {
        event.preventDefault();
        const openIndex = state.cards.findIndex((card) => card.open || card.matched);
        if (openIndex >= 0) {
            socket.emit("zoom", {card: state.zoom_card === null ? openIndex : null});
        } else if (document.body.classList.contains("moderator")) {
            socket.emit("reset_time");
        }
    }
    if (selectedColumn !== null && selectedRow !== null) openSelection();
});
document.addEventListener("click", (event) => {
    const memoryButton = event.target.closest("[data-memory]");
    if (memoryButton) {
        socket.emit("switch_memory", {memory: memoryButton.dataset.memory});
        return;
    }
    const card = event.target.closest(".card");
    if (card && card.dataset.index) {
        const index = Number(card.dataset.index);
        const currentCard = state && state.cards[index];
        if (currentCard && (currentCard.open || currentCard.matched)) {
            socket.emit("zoom", {card: state.zoom_card === index ? null : index});
        } else {
            socket.emit("open_card", { card: index });
        }
    }
    if (event.target.closest(".lightbox-close") || event.target.id === "lightbox") {
        socket.emit("zoom", {card: null});
    }
});
document.addEventListener("mousemove", (event) => {
    if (!document.body.classList.contains("moderator")) return;
    const card = event.target.closest(".card");
    const nextHoveredCardIndex = event.ctrlKey && card && card.dataset.index
        ? Number(card.dataset.index)
        : null;
    if (nextHoveredCardIndex === hoveredCardIndex) return;
    hoveredCardIndex = nextHoveredCardIndex;
    socket.emit("hover_card", {card: hoveredCardIndex});
    if (hoveredCardIndex !== null) {
        selectedColumn = null;
        selectedRow = null;
        socket.emit("selection", {column: null, row: null});
    }
});

let zoomScale = 1;
let zoomOffsetX = 0;
let zoomOffsetY = 0;
let dragging = false;
let dragStart = null;
document.addEventListener("wheel", (event) => {
    const lightbox = document.getElementById("lightbox");
    if (!lightbox || lightbox.hidden) return;
    event.preventDefault();
    const image = lightbox.querySelector("img");
    if (!image) return;
    const oldScale = zoomScale;
    const factor = event.deltaY < 0 ? 1.15 : 1 / 1.15;
    zoomScale = Math.min(8, Math.max(1, zoomScale * factor));
    const rect = image.getBoundingClientRect();
    const pointerX = event.clientX - rect.left;
    const pointerY = event.clientY - rect.top;
    zoomOffsetX -= pointerX * (zoomScale / oldScale - 1);
    zoomOffsetY -= pointerY * (zoomScale / oldScale - 1);
    publishZoomTransform();
}, {passive: false});
document.addEventListener("mousedown", (event) => {
    if (event.target.closest("#lightbox img")) {
        event.preventDefault();
        dragging = true;
        dragStart = {x: event.clientX, y: event.clientY};
    }
});
document.addEventListener("mousemove", (event) => {
    if (!dragging) return;
    event.preventDefault();
    zoomOffsetX += event.clientX - dragStart.x;
    zoomOffsetY += event.clientY - dragStart.y;
    dragStart = {x: event.clientX, y: event.clientY};
    publishZoomTransform();
});
document.addEventListener("mouseup", () => { dragging = false; });
document.addEventListener("dragstart", (event) => {
    if (event.target.closest("#lightbox img")) event.preventDefault();
});
function applyZoomTransform() {
    const image = document.querySelector("#lightbox img");
    if (image) image.style.transform = `translate(${zoomOffsetX}px, ${zoomOffsetY}px) scale(${zoomScale})`;
}
document.addEventListener("dblclick", (event) => {
    const card = event.target.closest(".card");
    if (!card || !card.dataset.index || !state) return;
    const index = Number(card.dataset.index);
    if (state.cards[index] && (state.cards[index].open || state.cards[index].matched)) {
        socket.emit("zoom", {card: index});
    }
});
