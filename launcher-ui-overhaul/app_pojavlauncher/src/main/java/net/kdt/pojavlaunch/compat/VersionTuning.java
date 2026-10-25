package net.kdt.pojavlaunch.compat;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Per-era frame budget and the exact {@code options.txt} keys that era understands.
 *
 * <p>This is the part that turns "set everything to low" into "set the right thing for this
 * version". The keys really did change between versions:
 *
 * <ul>
 *     <li>1.0-1.12.2 (LWJGL2): {@code limitFramerate}, {@code fancyGraphics}, {@code ambientOcclusion},
 *     {@code clouds}, {@code useVbo}.</li>
 *     <li>1.13-1.16.5: {@code maxFps}, {@code renderClouds}, {@code entityDistanceScaling},
 *     {@code graphicsMode} (1.16+).</li>
 *     <li>1.17+: {@code simulationDistance} appears and is the single cheapest thing to lower.</li>
 *     <li>1.21.11+: new render pipeline, the frame is expensive again, so its resolution budget and
 *     chunk distance are the tightest.</li>
 * </ul>
 *
 * <p>Only keys the era actually reads are written, except for the few renames where Minecraft still
 * migrates the old spelling on load. Unknown keys in {@code options.txt} are preserved by the game,
 * so they would be harmless either way.
 */
public final class VersionTuning {

    /** Value Minecraft stores for "unlimited" in both {@code maxFps} and {@code limitFramerate}. */
    public static final String UNLIMITED_FPS = "260";

    private VersionTuning() { }

    /**
     * Video options for one era.
     *
     * @param era the version era of the instance being launched
     * @return ordered map of {@code options.txt} keys to values
     */
    public static Map<String, String> videoOptions(VersionEra era) {
        LinkedHashMap<String, String> options = new LinkedHashMap<>();
        options.put("renderDistance", String.valueOf(era.renderDistance));

        // Frame limiter: the key was renamed in 1.13.
        if (era.usesMaxFpsKey()) {
            options.put("maxFps", UNLIMITED_FPS);
        } else {
            options.put("limitFramerate", UNLIMITED_FPS);
        }
        options.put("enableVsync", "false");

        // Graphics preset: boolean before 1.16, enum after.
        options.put("fancyGraphics", "false");
        if (era.usesGraphicsMode()) options.put("graphicsMode", "0");

        // Clouds: boolean key everywhere, {@code renderClouds} only from 1.13.
        options.put("clouds", "false");
        if (!era.isLegacyLwjgl2()) options.put("renderClouds", "false");

        options.put("entityShadows", "false");
        options.put("particles", "2");
        // Ambient occlusion / smooth lighting: the key was renamed to {@code ao} in 1.16. Both are
        // booleans, and writing the wrong spelling in the other era would be silently ignored, so
        // each era gets exactly the one it reads.
        options.put(era.isLegacyLwjgl2() ? "ambientOcclusion" : "ao", "false");

        if (era.isLegacyLwjgl2()) {
            // Legacy-only switches: VBO rendering is much faster than display lists through a GL
            // wrapper, and anaglyph is pure cost.
            options.put("useVbo", "true");
            options.put("anaglyph", "false");
            options.put("fboEnable", "true");
            // 2x mipmaps is the sweet spot for the small textures of this era.
            options.put("mipmapLevels", "2");
        } else {
            // Mipmaps reduce texture-cache misses and stop the scaled frame from shimmering.
            options.put("mipmapLevels", "4");
            options.put("entityDistanceScaling", "0.5");
            options.put("biomeBlendRadius", "0");
            options.put("fovEffectScale", "0.0");
            options.put("distortionEffectScale", "0.0");
        }

        if (era.usesSimulationDistance()) {
            // Cheaper than render distance for tick cost, and the biggest 1.17+ win.
            options.put("simulationDistance", "4");
        }
        return options;
    }

    /**
     * JVM flags that reduce frame-time spikes on every era and every Java version the launcher
     * ships (8 through 21). All of them are plain HotSpot flags, no experimental unlocks.
     */
    public static String[] jvmFlags() {
        return new String[]{
                "-XX:+UseG1GC",
                "-XX:+ParallelRefProcEnabled",
                "-XX:MaxGCPauseMillis=20",
                "-XX:+DisableExplicitGC",
                "-XX:+AlwaysPreTouch",
                "-XX:+PerfDisableSharedMem",
        };
    }

    /** Extra {@code -D} properties for a given era; empty for eras that do not need them. */
    public static String[] systemProperties(VersionEra era) {
        if (era.isLegacyLwjgl2()) {
            return new String[]{
                    // Do not silently fall back to a software GL implementation.
                    "-Dorg.lwjgl.opengl.Display.allowSoftwareOpenGL=false",
                    // Forge on these versions nags (and slows first launch) over signature checks.
                    "-Dfml.ignoreInvalidMinecraftCertificates=true",
                    "-Dfml.ignorePatchDiscrepancies=true",
            };
        }
        return new String[]{
                // LWJGL3 allocates a lot of small direct buffers; cap the per-thread cache so the
                // JVM does not keep churning them.
                "-Djdk.nio.maxCachedBufferSize=262144",
        };
    }

    /** Environment handed to the GL wrapper / driver for this era (only known-safe names). */
    public static Map<String, String> driverEnv(VersionEra era) {
        LinkedHashMap<String, String> env = new LinkedHashMap<>();
        if (era.isLegacyLwjgl2()) {
            // gl4es: quiet banner + silent stub calls. Both are honoured by gl4es and ignored by
            // every other renderer.
            env.put("LIBGL_NOBANNER", "1");
            env.put("LIBGL_SILENTSTUB", "1");
        }
        // Never block on vblank when the FPS profile is on.
        env.put("vblank_mode", "0");
        return env;
    }

    /** Highest render distance the 1.21+ pack will leave in place; it never raises yours. */
    public static final int MODERN_MAX_RENDER_DISTANCE = 6;
    /** Same for simulation distance: 1.17+ ticks chunks around the player. */
    public static final int MODERN_MAX_SIMULATION_DISTANCE = 5;
    /** Smallest mipmap level the pack accepts; mipmaps cut texture bandwidth. */
    public static final int MODERN_MIN_MIPMAPS = 2;

    /**
     * The 1.21+ FPS pack: a deliberately <b>moderate</b> profile.
     *
     * <p>It only turns off things that cost frames without changing how the game looks from a
     * normal viewing distance (clouds, entity shadows, fancy leaves, biome blend, view-bob nausea,
     * portal distortion, excessive particles), and it only ever <b>lowers</b> render/simulation
     * distance — a player who already runs 4 chunks keeps 4.
     *
     * <p>It deliberately does not touch resolution, CPU affinity, clock modes, heap or JVM flags:
     * those are the knobs that made earlier builds slower than the defaults.
     *
     * @param current the instance's options as they are right now
     */
    public static Map<String, String> modernFpsOptions(Map<String, String> current) {
        LinkedHashMap<String, String> options = new LinkedHashMap<>();
        options.put("renderDistance", String.valueOf(
                Math.min(readInt(current, "renderDistance", 12), MODERN_MAX_RENDER_DISTANCE)));
        options.put("simulationDistance", String.valueOf(
                Math.min(readInt(current, "simulationDistance", 12), MODERN_MAX_SIMULATION_DISTANCE)));
        options.put("enableVsync", "false");
        options.put("maxFps", UNLIMITED_FPS);
        // Fast graphics: also drops fancy leaves + the expensive translucent pass.
        options.put("graphicsMode", "0");
        options.put("fancyGraphics", "false");
        options.put("clouds", "false");
        options.put("renderClouds", "false");
        options.put("entityShadows", "false");
        options.put("entityDistanceScaling", "0.5");
        options.put("particles", "2");
        options.put("biomeBlendRadius", "0");
        options.put("ao", "false");
        options.put("fovEffectScale", "0.0");
        options.put("distortionEffectScale", "0.0");
        options.put("mipmapLevels", String.valueOf(
                Math.max(readInt(current, "mipmapLevels", 0), MODERN_MIN_MIPMAPS)));
        return options;
    }

    private static int readInt(Map<String, String> map, String key, int fallback) {
        if (map == null) return fallback;
        String raw = map.get(key);
        if (raw == null) return fallback;
        try {
            return Integer.parseInt(raw.trim());
        } catch (NumberFormatException ignored) {
            return fallback;
        }
    }

    /**
     * Render scale for one instance: the era decides the target short side and the quality floor.
     * Thin wrapper so callers do not need to know the era table.
     */
    public static float renderScale(float savedScale, boolean highFpsEnabled,
                                    int widthPx, int heightPx, VersionEra era) {
        VersionEra safeEra = era == null ? VersionEra.MODERN : era;
        return net.kdt.pojavlaunch.utils.HighFpsRenderScale.resolveForSize(savedScale,
                highFpsEnabled, widthPx, heightPx,
                safeEra.renderShortSide, safeEra.minRenderScale);
    }

    /** @return {@code true} when the era can safely be pushed to native resolution. */
    public static boolean canRenderNative(VersionEra era) {
        return era.frameCost <= 1.0f;
    }

    /** One-line description of what the profile does for this era, used in toasts and logs. */
    public static String describe(VersionEra era) {
        return era.label() + ": render " + era.renderShortSide + "p, chunks "
                + era.renderDistance + ", all effects off";
    }
}
