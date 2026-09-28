(function () {
    "use strict";

    var root = document.getElementById("blind-rank-app");
    if (!root) return;

    var items = [];
    var dataNode = document.getElementById("blind-items-data");
    try { items = JSON.parse((dataNode && dataNode.textContent) || "[]"); } catch (e) { items = []; }

    var queue = items.slice();
    var ranks = {};
    var SLOT_COUNT = 10;
    var busy = false;

    var stageImg = document.getElementById("blind-stage-img");
    var stageName = document.getElementById("blind-stage-name");
    var remainEl = document.getElementById("blind-remaining");
    var board = document.getElementById("blind-board");
    var playView = document.getElementById("blind-play");
    var resultView = document.getElementById("blind-result");
    var resultList = document.getElementById("blind-result-list");
    var bg = document.getElementById("blind-bg");
    var reel = document.getElementById("blind-reel");

    function remainingSlots() {
        var n = 0, i;
        for (i = 1; i <= SLOT_COUNT; i++) if (!ranks[i]) n++;
        return n;
    }
    function currentItem() { return queue[0] || null; }

    function paintReel() {
        if (!reel) return;
        var rest = queue.slice(0, 12);
        if (!rest.length) { reel.innerHTML = ""; return; }
        var html = rest.concat(rest).map(function (it) {
            return '<img src="' + it.image + '" alt="">';
        }).join("");
        reel.innerHTML = html;
    }

    function setHero(item, spinning) {
        if (!item) return;
        if (stageImg) stageImg.src = item.image;
        if (stageName) stageName.textContent = spinning ? "…" : (item.name || "İsimsiz");
        if (bg) bg.style.backgroundImage = "url('" + item.image + "')";
    }

    function renderStats() {
        if (remainEl) remainEl.textContent = String(queue.length);
    }

    function renderSlots() {
        if (!board) return;
        board.querySelectorAll("[data-rank]").forEach(function (btn) {
            var rank = Number(btn.getAttribute("data-rank"));
            var occupied = ranks[rank];
            var img = btn.querySelector(".qz-rank-thumb");
            btn.classList.toggle("is-filled", !!occupied);
            btn.classList.toggle("is-locked", !!occupied);
            if (img) {
                if (occupied) {
                    img.src = occupied.image;
                    img.hidden = false;
                } else {
                    img.removeAttribute("src");
                    img.hidden = true;
                }
            }
        });
    }

    function finish() {
        if (playView) playView.hidden = true;
        if (reel) reel.hidden = true;
        if (resultView) resultView.hidden = false;
        if (!resultList) return;
        resultList.innerHTML = "";
        var i, item, li;
        for (i = 1; i <= SLOT_COUNT; i++) {
            item = ranks[i];
            li = document.createElement("li");
            li.className = "blind-result-row" + (i <= 3 ? " is-top" : "");
            if (!item) {
                li.innerHTML = '<span class="blind-result-rank">' + i + '</span><div class="blind-result-empty">Boş</div>';
            } else {
                li.innerHTML =
                    '<span class="blind-result-rank">' + i + '</span>' +
                    '<img src="' + item.image + '" alt="">' +
                    '<div><strong>' + (item.name || "İsimsiz") + '</strong><span>#' + i + '</span></div>';
            }
            resultList.appendChild(li);
        }
        if (window.confetti) {
            window.confetti({ particleCount: 110, spread: 68, origin: { y: 0.72 }, colors: ["#ffd60a", "#ff7b00", "#fff"] });
        }
    }

    function spinThenShow(item, done) {
        if (!item || !queue.length) { done(); return; }
        var pool = queue.slice();
        var n = Math.min(10, pool.length);
        var i = 0;
        busy = true;
        var timer = setInterval(function () {
            var flash = pool[Math.floor(Math.random() * pool.length)];
            setHero(flash, true);
            i += 1;
            if (i >= n) {
                clearInterval(timer);
                setHero(item, false);
                busy = false;
                done();
            }
        }, 45);
    }

    function showNext() {
        paintReel();
        renderStats();
        var item = currentItem();
        if (!item || remainingSlots() === 0) {
            finish();
            return;
        }
        spinThenShow(item, function () {});
    }

    function place(rank) {
        if (busy || ranks[rank]) return;
        var item = currentItem();
        if (!item) return;
        ranks[rank] = item;
        queue.shift();
        renderSlots();
        showNext();
    }

    if (board) {
        board.addEventListener("click", function (e) {
            var btn = e.target.closest("[data-rank]");
            if (!btn || btn.classList.contains("is-locked")) return;
            place(Number(btn.getAttribute("data-rank")));
        });
    }

    document.addEventListener("keydown", function (e) {
        if (resultView && !resultView.hidden) return;
        if (e.key === "0") { place(10); return; }
        var n = parseInt(e.key, 10);
        if (n >= 1 && n <= 9) place(n);
    });

    renderSlots();
    showNext();
})();
