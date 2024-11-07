

export function setThemeColor(color) {
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    metaThemeColor.setAttribute('content', color);
  } else {
    const meta = document.createElement('meta');
    meta.name = 'theme-color';
    meta.content = color;
    document.getElementsByTagName('head')[0].appendChild(meta);
  }
}
