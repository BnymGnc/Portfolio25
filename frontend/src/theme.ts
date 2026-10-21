export const themes = [
  {id: 'nature', label: 'Doğa'},
  {id: 'night', label: 'Gece'},
  {id: 'earth', label: 'Toprak'},
] as const;
export type Theme = typeof themes[number]['id'];
const key = 'portfolio25-theme';
export function readTheme(): Theme {
  try {
    const value = localStorage.getItem(key);
    return themes.find(t => t.id === value)?.id ?? 'nature';
  } catch { return 'nature'; }
}
export function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme === 'night' ? 'dark' : 'light';
  try { localStorage.setItem(key, theme); } catch { /* Session preference still works. */ }
}
