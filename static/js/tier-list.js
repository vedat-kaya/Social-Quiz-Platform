(function () {
    "use strict";

    var app = document.getElementById("tier-app");
    if (!app) return;

    var items = [];
    var node = document.getElementById("tier-items-data");
    try { items = JSON.parse((node && node.textContent) || "[]"); } catch (e) { items = []; }

    var pool = document.getElementById("tier-pool");
    var board = document.getElementById("tier-board");
    var selected = null;
    var quizKey = "sorsana-tiers-" + (app.dataset.quiz || "x");
    var MAX_LABEL = 100;

    var DEFAULT_ROWS = [
        { name: "S — En iyiler", color: "#ff7b7b" },
        { name: "A — Harika", color: "#ffb347" },
        { name: "B — İyi", color: "#ffe066" },
        { name: "C — Orta", color: "#c6ff6b" },
        { name: "D — Zayıf", color: "#7dff9a" },
        { name: "E — Kötü", color: "#6bffb5" },
        { name: "F — En alt", color: "#7ad7ff" }
    ];

    function cloneDefaults() {
        return DEFAULT_ROWS.map(function (r) { return { name: r.name, color: r.color }; });
    }

    function normalizeRows(raw) {
        if (!Array.isArray(raw) || !raw.length) return cloneDefaults();
        var mapped = raw.map(function (r) {
            var name = String((r && (r.name || r.title || r.key)) || "").trim().slice(0, MAX_LABEL);
            return {
                name: name,
                color: (r && r.color) || "#c9b6ff"
            };
        }).filter(function (r) { return r.name; });
        return mapped.length ? mapped : cloneDefaults();
    }

    function loadRows() {
        try {
            var saved = JSON.parse(localStorage.getItem(quizKey) || "null");
            return normalizeRows(saved);
        } catch (e) {
            return cloneDefaults();
        }
    }

    var rows = loadRows();

    function saveRows() {
        try {
            if (!rows.length) {
                localStorage.removeItem(quizKey);
                return;
            }
            localStorage.setItem(quizKey, JSON.stringify(rows));
        } catch (e) {}
    }

    function escapeAttr(value) {
        return String(value || "").replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
    }

    function autosize(el) {
        el.style.height = "auto";
        el.style.height = Math.min(el.scrollHeight, 88) + "px";
        var row = el.closest(".tier-row");
        if (row) row.style.minHeight = Math.max(72, el.scrollHeight + 28) + "px";
    }

    function chipEl(item) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "tier-chip";
        btn.draggable = true;
        btn.dataset.id = String(item.id);
        btn.innerHTML = '<img src="' + item.image + '" alt="' + escapeAttr(item.name) + '"><span>' + escapeAttr(item.name) + "</span>";
        return btn;
    }

    function fillPool() {
        pool.innerHTML = "";
        items.forEach(function (item) { pool.appendChild(chipEl(item)); });
    }

    function rowEl(row, index) {
        var wrap = document.createElement("div");
        wrap.className = "tier-row";
        wrap.dataset.index = String(index);
        wrap.innerHTML =
            '<div class="tier-label" style="background:' + row.color + '">' +
                '<textarea class="tier-name" maxlength="' + MAX_LABEL + '" rows="2" placeholder="Satır adı">' + escapeAttr(row.name) + "</textarea>" +
                '<input class="tier-color" type="color" value="' + escapeAttr(row.color) + '">' +
            "</div>" +
            '<div class="tier-drop" data-drop="row-' + index + '"></div>' +
            '<div class="tier-row-ops">' +
                '<button type="button" data-move="-1" title="Yukarı">↑</button>' +
                '<button type="button" data-move="1" title="Aşağı">↓</button>' +
                '<button type="button" data-del="1" title="Sil">✕</button>' +
            "</div>";
        var ta = wrap.querySelector(".tier-name");
        autosize(ta);
        return wrap;
    }

    function renderBoardKeepChips() {
        var chipsByRow = {};
        board.querySelectorAll(".tier-row").forEach(function (el, i) {
            chipsByRow[i] = Array.from(el.querySelectorAll(".tier-chip"));
        });
        board.innerHTML = "";
        rows.forEach(function (row, i) {
            var el = rowEl(row, i);
            board.appendChild(el);
            (chipsByRow[i] || []).forEach(function (chip) {
                el.querySelector(".tier-drop").appendChild(chip);
            });
        });
        saveRows();
    }

    function clearSelect() {
        app.querySelectorAll(".tier-chip.is-selected").forEach(function (el) {
            el.classList.remove("is-selected");
        });
        selected = null;
    }

    function dropTarget(el) {
        return el && el.closest ? el.closest("[data-drop]") : null;
    }

    app.addEventListener("dragstart", function (e) {
        var chip = e.target.closest(".tier-chip");
        if (!chip || !e.dataTransfer) return;
        chip.classList.add("is-dragging");
        e.dataTransfer.setData("text/plain", chip.dataset.id);
        e.dataTransfer.effectAllowed = "move";
    });

    app.addEventListener("dragend", function (e) {
        var chip = e.target.closest(".tier-chip");
        if (chip) chip.classList.remove("is-dragging");
        app.querySelectorAll(".is-over").forEach(function (el) { el.classList.remove("is-over"); });
    });

    app.addEventListener("dragover", function (e) {
        var zone = dropTarget(e.target);
        if (!zone) return;
        e.preventDefault();
        zone.classList.add("is-over");
    });

    app.addEventListener("dragleave", function (e) {
        var zone = dropTarget(e.target);
        if (zone) zone.classList.remove("is-over");
    });

    app.addEventListener("drop", function (e) {
        var zone = dropTarget(e.target);
        if (!zone) return;
        e.preventDefault();
        zone.classList.remove("is-over");
        var id = e.dataTransfer.getData("text/plain");
        var chip = app.querySelector('.tier-chip[data-id="' + id + '"]');
        if (chip) zone.appendChild(chip);
        clearSelect();
    });

    app.addEventListener("click", function (e) {
        var move = e.target.closest("[data-move]");
        var del = e.target.closest("[data-del]");
        if (move || del) {
            var row = e.target.closest(".tier-row");
            var idx = Number(row.dataset.index);
            if (del) {
                row.querySelectorAll(".tier-chip").forEach(function (c) { pool.appendChild(c); });
                rows.splice(idx, 1);
                if (!rows.length) {
                    try { localStorage.removeItem(quizKey); } catch (err) {}
                    rows = cloneDefaults();
                }
            } else {
                var dir = Number(move.dataset.move);
                var next = idx + dir;
                if (next < 0 || next >= rows.length) return;
                var tmp = rows[idx];
                rows[idx] = rows[next];
                rows[next] = tmp;
                var a = board.children[idx];
                var b = board.children[next];
                if (dir < 0) board.insertBefore(a, b);
                else board.insertBefore(b, a);
                Array.from(board.children).forEach(function (el, i) { el.dataset.index = String(i); });
                saveRows();
                return;
            }
            renderBoardKeepChips();
            return;
        }

        var chip = e.target.closest(".tier-chip");
        var zone = dropTarget(e.target);
        if (chip) {
            if (selected === chip) { clearSelect(); return; }
            clearSelect();
            selected = chip;
            chip.classList.add("is-selected");
            return;
        }
        if (zone && selected && !e.target.closest(".tier-row-ops") && !e.target.closest(".tier-label")) {
            zone.appendChild(selected);
            clearSelect();
        }
    });

    app.addEventListener("input", function (e) {
        var row = e.target.closest(".tier-row");
        if (!row) return;
        var idx = Number(row.dataset.index);
        if (e.target.classList.contains("tier-name")) {
            e.target.value = e.target.value.slice(0, MAX_LABEL);
            rows[idx].name = e.target.value;
            autosize(e.target);
        }
        if (e.target.classList.contains("tier-color")) {
            rows[idx].color = e.target.value;
            row.querySelector(".tier-label").style.background = e.target.value;
        }
        saveRows();
    });

    document.getElementById("tier-add-row")?.addEventListener("click", function () {
        rows.push({ name: "Yeni satır", color: "#c9b6ff" });
        renderBoardKeepChips();
    });

    document.getElementById("tier-reset")?.addEventListener("click", function () {
        try { localStorage.removeItem(quizKey); } catch (e) {}
        rows = cloneDefaults();
        board.innerHTML = "";
        renderBoardKeepChips();
        fillPool();
        clearSelect();
    });

    fillPool();
    renderBoardKeepChips();
})();
