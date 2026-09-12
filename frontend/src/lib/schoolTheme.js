const DEFAULT_PRIMARY = "#144dd2";
const DEFAULT_SECONDARY = "#0a0a0b";

function normalizeHex(value, fallback) {
  const candidate = String(value || "").trim();
  return /^#[0-9a-fA-F]{6}$/.test(candidate)
    ? candidate.toLowerCase()
    : fallback;
}

function hexToRgb(hex) {
  const normalized = normalizeHex(hex, DEFAULT_PRIMARY).slice(1);
  return {
    r: Number.parseInt(normalized.slice(0, 2), 16),
    g: Number.parseInt(normalized.slice(2, 4), 16),
    b: Number.parseInt(normalized.slice(4, 6), 16),
  };
}

function channelToLinear(channel) {
  const value = channel / 255;
  return value <= 0.03928
    ? value / 12.92
    : ((value + 0.055) / 1.055) ** 2.4;
}

function contrastText(hex) {
  const { r, g, b } = hexToRgb(hex);
  const luminance =
    0.2126 * channelToLinear(r) +
    0.7152 * channelToLinear(g) +
    0.0722 * channelToLinear(b);

  return luminance > 0.52 ? "#0a0a0b" : "#ffffff";
}

function rgbString(hex) {
  const { r, g, b } = hexToRgb(hex);
  return `${r} ${g} ${b}`;
}

export function createSchoolTheme(school) {
  const primary = normalizeHex(
    school?.primary_color,
    DEFAULT_PRIMARY
  );
  const secondary = normalizeHex(
    school?.secondary_color,
    DEFAULT_SECONDARY
  );

  return {
    "--school-primary": primary,
    "--school-primary-rgb": rgbString(primary),
    "--school-secondary": secondary,
    "--school-secondary-rgb": rgbString(secondary),
    "--school-on-primary": contrastText(primary),
    "--school-on-secondary": contrastText(secondary),
  };
}
