// ==========================
// Service Search
// ==========================

document.addEventListener("DOMContentLoaded", function () {

    const backendUrl = window.SERVICE_BACKEND_URL;
    if (!backendUrl) {
        throw new Error("The Flask backend URL is not configured.");
    }

    document.querySelectorAll("[data-backend-path]").forEach(link => {
        link.href = new URL(link.dataset.backendPath, backendUrl).href;
    });

    const searchInput = document.getElementById("serviceSearch");

    if (searchInput) {

        searchInput.addEventListener("input", function () {
            const filter = this.value.trim().toLowerCase();
            const cards = document.querySelectorAll(".service-card");
            const emptyMessage = document.getElementById("serviceSearchEmpty");
            let visibleCount = 0;

            cards.forEach(card => {
                const matches = card.innerText.toLowerCase().includes(filter);
                card.style.display = matches ? "" : "none";

                if (matches) {
                    visibleCount += 1;
                }
            });

            if (emptyMessage) {
                emptyMessage.classList.toggle("d-none", visibleCount > 0);
            }
        });

    }

});


// ==========================
// Confirm Booking
// ==========================

function confirmBooking() {

    return confirm(
        "Are you sure you want to book this service?"
    );

}


// ==========================
// Success Message Auto Hide
// ==========================

setTimeout(function () {

    let alerts = document.querySelectorAll(".alert");

    alerts.forEach(alert => {

        alert.style.display = "none";

    });

}, 3000);


// ==========================
// Scroll To Top Button
// ==========================

window.onscroll = function () {

    let btn = document.getElementById("topBtn");

    if (!btn) return;

    if (
        document.body.scrollTop > 200 ||
        document.documentElement.scrollTop > 200
    ) {

        btn.style.display = "block";

    } else {

        btn.style.display = "none";

    }

};


function topFunction() {

    document.body.scrollTop = 0;

    document.documentElement.scrollTop = 0;

}


// ==========================
// Service Card Animation
// ==========================

document.addEventListener("DOMContentLoaded", () => {

    const cards = document.querySelectorAll(".service-card");

    cards.forEach((card, index) => {

        card.style.opacity = "0";

        setTimeout(() => {

            card.style.opacity = "1";

            card.style.transition = "0.5s";

        }, index * 100);

    });

});


// ==========================
// Booking Date Validation
// ==========================

document.addEventListener("DOMContentLoaded", () => {

    const bookingDate =
        document.querySelector(
            "input[name='booking_date']"
        );

    if (bookingDate) {

        let today =
            new Date()
            .toISOString()
            .split("T")[0];

        bookingDate.min = today;

    }

});


// ==========================
// Mobile Menu Close
// ==========================

document.querySelectorAll(".nav-link")
.forEach(link => {

    link.addEventListener("click", () => {

        let navbar =
            document.querySelector(".navbar-collapse");

        if (
            navbar &&
            navbar.classList.contains("show")
        ) {

            navbar.classList.remove("show");

        }

    });

});