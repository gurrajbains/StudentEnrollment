// The Flask application uses JWT cookies and CSRF protection.

// Read the CSRF cookie required for authenticated write requests
function csrfToken() {
    const item = document.cookie.split(";").map(x => x.trim()).find(x => x.startsWith("csrf_access_token="));
    return item ? decodeURIComponent(item.split("=").slice(1).join("=")) : "";
}

// Centralize Flask API for calls, CSRF headers, JSON parsing, and errors.
async function api(url, options = {}) {
    const method = (options.method || "GET").toUpperCase();
    const headers = new Headers(options.headers || {});
    if (!["GET", "HEAD", "OPTIONS"].includes(method)) headers.set("X-CSRF-TOKEN", csrfToken());
    const response = await fetch(url, {...options, method, headers, credentials: "same-origin"});
    const body = await response.text();
    let data = null;

    if (body) {
        try { data = JSON.parse(body); }
        catch { data = body; }
    }

    if (!response.ok) {
        const message = data && typeof data === "object" ? (data.error || data.message) : null;
        throw new Error(message || `HTTP ${response.status}`);
    }

    return data;
}

// Display the authenticated user's name on their dashboard.
async function showWelcome(element) {
    try {
        const user = await api("/api/me");
        if (element) element.textContent = `Welcome, ${user.name || user.username || "User"}!`;
    } catch (error) {
        if (element) element.textContent = "Welcome!";
        // If the user is not logged in, redirect to the home page but flasks does this automatically 

        if (error.message.startsWith("HTTP 401")) window.location.href = "/";
    }
}

// Flask will clear the JWT cookie and we will redirect the user to the home page after logging out.
async function logout() {
    try {
        await api("/api/logout", {method: "POST"});
        window.location.href = "/";
    } catch (error) {
        alert("Unable to log out: " + error.message);
    }
}
