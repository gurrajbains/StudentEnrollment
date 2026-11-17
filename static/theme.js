// This script enables a light/dark theme toggle for the Student Enrollment System dashboard by knowing the user's preference and saving it in localStorage. It also updates the theme toggle button's text and aria attributes for accessibility.
(() => {
    const key = 'student-enrollment-theme';
    const root = document.documentElement;
    let saved = null;

    // Restore the previously selected light or dark theme.
    try {
        saved = localStorage.getItem(key);
    } catch (_) {}

    root.dataset.theme = saved === 'dark' ? 'dark' : 'light';

    // Update the theme button to display the available mode by using root.dataset.theme 
    function refreshButtons() {
        const dark = root.dataset.theme === 'dark';
        document.querySelectorAll('.theme-toggle').forEach(button => {
            button.textContent = dark ? 'Light mode' : 'Dark mode';
            button.setAttribute('aria-pressed', String(dark));
            button.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
        });
    }

    // Save theme changes so they persist after reloading the dashboard by using local storage and if not use the default light theme
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.theme-toggle').forEach(button => button.addEventListener('click', () => {
            const dark = root.dataset.theme === 'dark';
            root.dataset.theme = dark ? 'light' : 'dark';
            try {
                localStorage.setItem(key, root.dataset.theme);
            } catch (_) {}
            refreshButtons();
        }));
        refreshButtons();
    });
})();
