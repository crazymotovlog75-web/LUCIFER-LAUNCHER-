package net.kdt.pojavlaunch.compat;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Minecraft render eras.
 *
 * <p>Every era changed something the launcher has to mirror to get frames: the LWJGL generation,
 * the OpenGL context the game asks for, the names of the video options in {@code options.txt}, and
 * how much work a frame costs. Treating all versions the same is why a 1.8.9 install and a 1.21.11
 * install ended up with the same mediocre frame rate.
 */
public enum VersionEra {
    /** 1.0 - 1.2.5: fixed-function GL1 era, tiny world, extremely cheap frames. */
    LEGACY_GL1(0, 2, 9999, 1080, 0.60f, 8, 1.00f),
    /** 1.3 - 1.12.2: LWJGL2, {@code limitFramerate}, boolean cloud/particle options. */
    LEGACY_LWJGL2(3, 12, 9999, 1080, 0.60f, 6, 1.00f),
    /** 1.13 - 1.16.5: LWJGL3, {@code maxFps}, {@code graphicsMode} from 1.16. */
    LWJGL3(13, 16, 9999, 960, 0.50f, 5, 0.85f),
    /** 1.17 - 1.20.6: chunk pipeline rewrite, {@code simulationDistance} world. */
    MODERN(17, 20, 9999, 900, 0.45f, 4, 0.70f),
    /** 1.21 - 1.21.10: post-trailer pipeline, still GL 3.3 core compatible. */
    MODERN_21(21, 21, 10, 850, 0.45f, 4, 0.55f),
    /** 1.21.11+: brand new render pipeline, needs a real GL 3.3+ core context. */
    NEW_PIPELINE(21, 21, 9999, 800, 0.45f, 4, 0.45f);

    /** Inclusive Minecraft minor version range ({@code 1.<minMinor>} .. {@code 1.<maxMinor>}). */
    public final int minMinor;
    public final int maxMinor;
    /** Highest patch accepted for {@code maxMinor}; 9999 means "any patch". */
    public final int maxPatch;
    /** Target short side of the render surface while the FPS profile is on. */
    public final int renderShortSide;
    /** Never render a smaller fraction of the screen than this, or the image turns to mush. */
    public final float minRenderScale;
    /** Safe block distance for this era; each new era costs more per chunk than the previous. */
    public final int renderDistance;
    /** Relative cost of one frame in this era, used to justify the resolution budgets above. */
    public final float frameCost;

    VersionEra(int minMinor, int maxMinor, int maxPatch,
               int renderShortSide, float minRenderScale, int renderDistance, float frameCost) {
        this.minMinor = minMinor;
        this.maxMinor = maxMinor;
        this.maxPatch = maxPatch;
        this.renderShortSide = renderShortSide;
        this.minRenderScale = minRenderScale;
        this.renderDistance = renderDistance;
        this.frameCost = frameCost;
    }

    private static final Pattern SNAPSHOT = Pattern.compile("\\b(\\d{2})w(\\d{2})[a-z]\\b");
    private static final Pattern VERSION = Pattern.compile("(\\d+)\\.(\\d+)(?:\\.(\\d+))?");

    /**
     * Classifies an instance id.
     *
     * <p>Understands plain releases ({@code 1.8.9}), loader ids
     * ({@code fabric-loader-0.16.9-1.21.11}, {@code forge-1.12.2-14.23.5.2860}) and snapshots
     * ({@code 25w31a}, which always means "newest era").
     */
    public static VersionEra of(String versionId) {
        if (versionId == null) return MODERN;
        String id = versionId.trim();
        if (id.isEmpty()) return MODERN;

        // Snapshots have no release number; they are always newer than the last release.
        if (SNAPSHOT.matcher(id).find()) return NEW_PIPELINE;

        int[] parsed = lastReleaseVersion(id);
        if (parsed == null) return MODERN;

        int minor = parsed[1];
        int patch = parsed[2];
        for (VersionEra era : values()) {
            if (minor < era.minMinor || minor > era.maxMinor) continue;
            if (minor == era.maxMinor && patch > era.maxPatch) continue;
            return era;
        }
        return NEW_PIPELINE;
    }

    /** Finds the last {@code 1.x[.y]} token, so loader prefixes are skipped. */
    private static int[] lastReleaseVersion(String id) {
        Matcher matcher = VERSION.matcher(id);
        int[] best = null;
        while (matcher.find()) {
            try {
                if (Integer.parseInt(matcher.group(1)) != 1) continue;
                int minor = Integer.parseInt(matcher.group(2));
                int patch = matcher.group(3) == null ? 0 : Integer.parseInt(matcher.group(3));
                best = new int[]{1, minor, patch};
            } catch (NumberFormatException ignored) {
                // skip malformed tokens
            }
        }
        return best;
    }

    /** Era of the instance the launcher currently has selected, safe to call from anywhere. */
    public static VersionEra ofCurrentInstance() {
        try {
            net.kdt.pojavlaunch.value.launcherprofiles.MinecraftProfile profile =
                    net.kdt.pojavlaunch.value.launcherprofiles.LauncherProfiles.getCurrentProfile();
            if (profile != null) return of(profile.lastVersionId);
        } catch (Throwable ignored) {
            // no profile readable (early startup, damaged file): use the neutral era
        }
        return MODERN;
    }

    public boolean isLegacyLwjgl2() {
        return this == LEGACY_GL1 || this == LEGACY_LWJGL2;
    }

    public boolean usesSimulationDistance() {
        return this == MODERN || this == MODERN_21 || this == NEW_PIPELINE;
    }

    public boolean usesMaxFpsKey() {
        return !isLegacyLwjgl2();
    }

    public boolean usesGraphicsMode() {
        return !isLegacyLwjgl2();
    }

    /** Human readable name, used in the launcher, the logs and the release notes. */
    public String label() {
        switch (this) {
            case LEGACY_GL1: return "1.0-1.2.5 legacy";
            case LEGACY_LWJGL2: return "1.3-1.12.2 LWJGL2";
            case LWJGL3: return "1.13-1.16.5 LWJGL3";
            case MODERN: return "1.17-1.20.6 modern";
            case MODERN_21: return "1.21-1.21.10 modern";
            default: return "1.21.11+ new pipeline";
        }
    }
}
