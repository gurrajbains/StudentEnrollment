// Shared helpers for the teacher and admin dashboards.
// The Flask app uses HttpOnly JWT cookies and a readable CSRF cookie.
function csrfToken() {
    const item = document.cookie.split(";").map(x => x.trim()).find(x => x.startsWith("csrf_access_token="));
    return item ? decodeURIComponent(item.split("=").slice(1).join("=")) : "";
}

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

async function showWelcome(element) {
    try {
        const user = await api("/api/me");
        if (element) element.textContent = `Welcome, ${user.name || user.username || "User"}!`;
    } catch (error) {
        if (element) element.textContent = "Welcome!";
        // Flask protects the pages too, so this is only a UI convenience.
        if (error.message.startsWith("HTTP 401")) window.location.href = "/";
    }
}

async function logout() {
    try {
        await api("/api/logout", {method: "POST"});
        window.location.href = "/";
    } catch (error) {
        alert("Unable to log out: " + error.message);
    }
}
