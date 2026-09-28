(function () {
    "use strict";

    window.toggleSidebar = function () {
        var sidebar = document.getElementById("mobileSidebar");
        var overlay = document.getElementById("sidebarOverlay");
        if (!sidebar || !overlay) return;
        sidebar.classList.toggle("active");
        overlay.classList.toggle("active");
        document.body.classList.toggle("sidebar-open", sidebar.classList.contains("active"));
    };

    window.slideScroll = function (element, direction) {
        var wrapper = element.closest(".slider-wrapper");
        if (!wrapper) return;
        var container = wrapper.querySelector(".slider-container");
        if (!container) return;
        var isMobile = window.innerWidth < 768;
        var amount = isMobile ? window.innerWidth * 0.85 : 400;
        container.scrollBy({ left: direction === "left" ? -amount : amount, behavior: "smooth" });
    };

    document.addEventListener("DOMContentLoaded", function () {
        var toasts = document.querySelectorAll(".premium-toast");
        toasts.forEach(function (toast) {
            setTimeout(function () {
                toast.style.opacity = "0";
                setTimeout(function () { toast.remove(); }, 320);
            }, 4200);
        });

        document.addEventListener("click", function (e) {
            var btn = e.target.closest("[data-action='like'], [data-action='save']");
            if (!btn) return;
            e.preventDefault();
            fetch(btn.getAttribute("href"), { headers: { "X-Requested-With": "fetch" }, credentials: "same-origin" })
                .then(function (res) {
                    if (res.status === 401) { window.location.href = "/login"; return null; }
                    return res.json();
                })
                .then(function (data) {
                    if (!data || !data.ok) return;
                    if (btn.getAttribute("data-action") === "like") {
                        btn.classList.toggle("btn-danger", data.liked);
                        btn.classList.toggle("btn-outline-danger", !data.liked);
                        var icon = btn.querySelector("i");
                        if (icon) icon.className = data.liked ? "fa-solid fa-heart" : "fa-regular fa-heart";
                        var lab = btn.querySelector("[data-like-label]");
                        if (lab) lab.textContent = data.liked ? "Beğendin" : "Beğen";
                        var count = document.querySelector("[data-like-count]");
                        if (count) count.textContent = data.likes;
                    } else {
                        btn.classList.toggle("btn-light", data.saved);
                        btn.classList.toggle("btn-outline-secondary", !data.saved);
                        var ic = btn.querySelector("i");
                        if (ic) ic.className = data.saved ? "fa-solid fa-bookmark" : "fa-regular fa-bookmark";
                        var sl = btn.querySelector("[data-save-label]");
                        if (sl) sl.textContent = data.saved ? "Kaydedildi" : "Kaydet";
                    }
                });
        });

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") {
                var back = document.querySelector(".qz-back");
                if (back) window.location.href = back.getAttribute("href");
            }
            var tag = (e.target && e.target.tagName) || "";
            var typing = tag === "INPUT" || tag === "TEXTAREA";
            var sheet = document.getElementById("shortcut-sheet");
            if (e.key === "?" && !typing && sheet) sheet.hidden = !sheet.hidden;
            if (e.key === "/" && !typing) {
                var search = document.getElementById("home-search") || document.querySelector(".search-input");
                if (search) {
                    e.preventDefault();
                    search.focus();
                }
            }
        });
        var sheet = document.getElementById("shortcut-sheet");
        if (sheet) {
            sheet.addEventListener("click", function (e) {
                if (e.target === sheet) sheet.hidden = true;
            });
        }

        var copyBtn = document.querySelector("[data-copy-link]");
        if (copyBtn) {
            copyBtn.addEventListener("click", function () {
                if (navigator.clipboard) navigator.clipboard.writeText(window.location.href);
                copyBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
                setTimeout(function () { copyBtn.innerHTML = '<i class="fa-solid fa-link"></i>'; }, 1400);
            });
        }

        document.querySelectorAll(".nav-chip").forEach(function (chip) {
            chip.addEventListener("mousemove", function (e) {
                var r = chip.getBoundingClientRect();
                var x = (e.clientX - r.left) / r.width - 0.5;
                var y = (e.clientY - r.top) / r.height - 0.5;
                chip.style.transform = "translate(" + (x * 6) + "px," + (y * 4) + "px) scale(1.04)";
            });
            chip.addEventListener("mouseleave", function () {
                chip.style.transform = "";
            });
        });
    });
})();
