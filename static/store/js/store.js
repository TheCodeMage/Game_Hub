
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const menuToggle = document.querySelector("[data-menu-toggle]");
    const navigation = document.querySelector("[data-navigation]");

    if (menuToggle && navigation) {
        menuToggle.addEventListener("click", () => {
            const isOpen = navigation.classList.toggle("is-open");

            menuToggle.setAttribute("aria-expanded", String(isOpen));
            menuToggle.setAttribute(
                "aria-label",
                isOpen ? "Close navigation" : "Open navigation"
            );
        });
    }

    const filterToggle = document.querySelector("[data-filter-toggle]");
    const filterForm = document.querySelector("#catalog-filters");

    if (filterToggle && filterForm) {
        filterToggle.addEventListener("click", () => {
            const isOpen = filterForm.classList.toggle("is-open");

            filterToggle.setAttribute("aria-expanded", String(isOpen));
            filterToggle.textContent = isOpen ? "Hide Filters" : "Filters";
        });
    }

    const catalogForm = document.querySelector("#catalog-filters");

    if (catalogForm) {
        const autoSubmitFields = [
            "#genre-filter",
            "#platform-filter",
            "#sort-filter"
        ];

        autoSubmitFields.forEach((selector) => {
            const field = catalogForm.querySelector(selector);

            if (field) {
                field.addEventListener("change", () => {
                    catalogForm.requestSubmit();
                });
            }
        });
    }

    document.querySelectorAll(".game-card-image img, .detail-cover img, .screenshot-card img")
        .forEach((image) => {
            image.addEventListener("error", () => {
                image.hidden = true;

                const parent = image.parentElement;

                if (parent && !parent.querySelector(".image-load-error")) {
                    const message = document.createElement("div");
                    message.className = "image-placeholder image-load-error";
                    message.textContent = "Image unavailable";
                    parent.appendChild(message);
                }
            });
        });
});
