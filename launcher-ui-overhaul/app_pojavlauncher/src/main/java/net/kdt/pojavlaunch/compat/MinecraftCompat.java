package net.kdt.pojavlaunch.compat;

import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Version rules for the modern Minecraft render pipeline.
 *
 * <p>From 1.21.11 onwards the game draws through the new GPU pipeline, which needs a real
 * OpenGL 3.3+ core context with buffer-storage / uniform-buffer support. The old GL4ES wrapper
 * ({@code opengles2}) only emulates GL 2.x, so the window comes up completely black — the game keeps
 * running, the sound and the controls work, but nothing is ever drawn.
 *
 * <p>This class holds the rules only: no Android imports, so it is covered by plain JVM unit tests.
 * {@link GameCompatBootstrap} applies the decisions to the launcher preferences.
 */
public final class MinecraftCompat {

    /** First version that uses the modern render pipeline. */
    public static final int MODERN_MAJOR = 1;
    public static final int MODERN_MINOR = 21;
    public static final int MODERN_PATCH = 11;

    /** Renderer ids, most capable first for a modern pipeline. */
    public static final String RENDERER_ZINK = "opengles3_desktopgl_zink";
    public static final String RENDERER_MOBILEGLUES = "opengles_mobileglues";
    public static final String RENDERER_KRYPTON = "opengles3_KW";
    public static final String RENDERER_ANGLE = "opengles3_ltw";
    public static final String RENDERER_GL4ES = "opengles2";
    /** Speed profile of GL4ES. Same GL 2.1 emulation, so it is legacy-pipeline only. */
    public static final String RENDERER_HOLY_GL4ES = "holy_gl4es";

    /** {@code 1.21.11}, {@code 1.22}, {@code 1.21} — but not loader versions like {@code 0.16.9}. */
    private static final Pattern VERSION_PATTERN = Pattern.compile("(\\d+)\\.(\\d+)(?:\\.(\\d+))?");

    private MinecraftCompat() { }

    /**
     * Extracts the Minecraft version out of an instance id.
     *
     * <p>Handles plain ids ({@code 1.21.11}), loader ids
     * ({@code fabric-loader-0.16.9-1.21.11}, {@code forge-1.21.10-52.0.12}) and pre-release suffixes
     * ({@code 1.21.11-pre2}, {@code 1.21.11-rc1}). Loader numbers (major 0) and build numbers are
     * skipped, because only the Minecraft version starts with {@code 1.}.
     *
     * @return {@code {major, minor, patch}} or {@code null} when the id carries no usable version
     *         (snapshots such as {@code 25w31a}, or an empty id)
     */
    public static int[] parseVersion(String versionId) {
        if (versionId == null) return null;
        String trimmed = versionId.trim();
        if (trimmed.isEmpty()) return null;

        Matcher matcher = VERSION_PATTERN.matcher(trimmed);
        int[] best = null;
        while (matcher.find()) {
            int major;
            try {
                major = Integer.parseInt(matcher.group(1));
            } catch (NumberFormatException ignored) {
                continue;
            }
            // Minecraft release versions are 1.x; loader/build versions are 0.x or 5x.x.
            if (major != 1) continue;
            int minor;
            int patch;
            try {
                minor = Integer.parseInt(matcher.group(2));
                patch = matcher.group(3) == null ? 0 : Integer.parseInt(matcher.group(3));
            } catch (NumberFormatException ignored) {
                continue;
            }
            best = new int[]{major, minor, patch};
        }
        return best;
    }

    /** @return true when the instance is 1.21.11 or newer, i.e. uses the modern pipeline. */
    public static boolean requiresModernGl(String versionId) {
        int[] parsed = parseVersion(versionId);
        if (parsed == null) return false;
        if (parsed[1] != MODERN_MINOR) return parsed[1] > MODERN_MINOR;
        return parsed[2] >= MODERN_PATCH;
    }

    /**
     * The modern pipeline blits through a {@code TextureView}. On several drivers that path produces
     * a black or frozen frame once the game starts using the new pipeline, while the zero-copy
     * {@code SurfaceView} path keeps working — and it is faster too.
     */
    public static boolean prefersSurfaceView(String versionId) {
        return requiresModernGl(versionId);
    }

    /**
     * Picks a renderer that can provide OpenGL 3.3+ for a modern instance.
     *
     * @param currentRenderer the renderer the instance currently uses (may be null)
     * @param compatible      renderer ids this device can actually run, as reported by the engine
     * @return the renderer id to switch to, or {@code null} when the current one is already fine (or
     *         nothing better is available)
     */
    public static String pickModernRenderer(String currentRenderer, List<String> compatible) {
        if (compatible == null || compatible.isEmpty()) return null;
        if (isModernCapable(currentRenderer)) return null;

        String[] preference = {RENDERER_ZINK, RENDERER_MOBILEGLUES, RENDERER_KRYPTON, RENDERER_ANGLE};
        for (String candidate : preference) {
            if (compatible.contains(candidate)) return candidate;
        }
        return null;
    }

    /** @return true when the renderer exposes a desktop-class GL version (3.3+). */
    public static boolean isModernCapable(String renderer) {
        if (renderer == null || renderer.isEmpty()) return false;
        // Legacy GL4ES only emulates GL 2.1, and HOLY GL4ES is the same emulation with faster
        // settings: neither can serve the 1.21.11+ pipeline.
        if (RENDERER_GL4ES.equals(renderer)) return false;
        if (RENDERER_HOLY_GL4ES.equals(renderer)) return false;
        return renderer.contains("zink")
                || renderer.contains("mobileglues")
                || renderer.contains("ltw")
                || renderer.contains("KW");
    }

    /** Human readable reason, shown once when the compatibility profile kicks in. */
    public static String compatSummary(String versionId, String newRenderer) {
        return "Minecraft " + versionId + ": modern render pipeline → SurfaceView + "
                + (newRenderer == null ? "current renderer" : newRenderer)
                + " (black-screen fix)";
    }
}
