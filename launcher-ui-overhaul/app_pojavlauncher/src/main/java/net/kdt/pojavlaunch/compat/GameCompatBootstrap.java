package net.kdt.pojavlaunch.compat;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import net.kdt.pojavlaunch.Tools;
import net.kdt.pojavlaunch.prefs.LauncherPreferences;
import net.kdt.pojavlaunch.value.launcherprofiles.LauncherProfiles;
import net.kdt.pojavlaunch.value.launcherprofiles.MinecraftProfile;

import java.util.List;

/**
 * Applies the compatibility profile for Minecraft 1.21.11 and newer.
 *
 * <p>Those versions replaced the render pipeline. On a phone they only draw correctly when the
 * engine hands the game a GL 3.3+ capable renderer, a zero-copy {@code SurfaceView} and a real
 * GLES3 context — otherwise the world comes up black even though the game is running fine
 * underneath (the exact symptom reported by users).
 *
 * <p>Because the "correct" renderer depends on the device driver, the profile is a small ladder:
 * the first entry that this device reports as compatible is applied, and {@link #cycleStep(Context)}
 * walks down the ladder so a user whose driver dislikes one entry can find the one that works.
 */
public final class GameCompatBootstrap {
    private static final String TAG = "GameCompat";
    /** Preference that remembers which ladder step is active. */
    private static final String KEY_STEP = "modernCompatStep";
    /** Preference storing the renderer the user had before the compatibility profile. */
    private static final String KEY_ORIGINAL_RENDERER = "modernCompatOriginalRenderer";

    /**
     * Ladder of renderers that can supply OpenGL 3.3+ on this engine, best first. The renderer id
     * is what the engine stores in the instance profile.
     */
    public static final String[] RENDERER_LADDER = {
            MinecraftCompat.RENDERER_ZINK,
            MinecraftCompat.RENDERER_MOBILEGLUES,
            MinecraftCompat.RENDERER_KRYPTON,
            MinecraftCompat.RENDERER_ANGLE,
            "opengles3_desktopgl_zink_kopper",
    };

    /** True while the game being launched is a modern (1.21.11+) instance. */
    private static volatile boolean sModernInstance = false;
    /** Version id of the instance being launched, for logging / labels. */
    private static volatile String sVersionId = null;

    private GameCompatBootstrap() { }

    /**
     * @return true when the instance currently being launched needs the modern GL profile.
     *         Falls back to reading the selected profile, because the game can also be started from
     *         a notification without going through the launcher screen.
     */
    public static boolean isModernInstance() {
        if (sModernInstance) return true;
        try {
            MinecraftProfile profile = safeCurrentProfile();
            if (profile != null && MinecraftCompat.requiresModernGl(profile.lastVersionId)) {
                markInstance(profile.lastVersionId);
                return true;
            }
        } catch (Throwable ignored) {
            // fall through: an unknown instance keeps the legacy path
        }
        return false;
    }

    public static String getVersionId() {
        return sVersionId;
    }

    /** Called when an instance is selected, so the runtime knows which profile to use. */
    public static void markInstance(String versionId) {
        sVersionId = versionId;
        sModernInstance = MinecraftCompat.requiresModernGl(versionId);
    }

    private static SharedPreferences prefs(Context context) {
        SharedPreferences pref = LauncherPreferences.DEFAULT_PREF;
        if (pref == null && context != null) {
            pref = context.getSharedPreferences("cslauncher_settings", Context.MODE_PRIVATE);
        }
        return pref;
    }

    private static int step(Context context) {
        SharedPreferences pref = prefs(context);
        return pref == null ? 0 : pref.getInt(KEY_STEP, 0);
    }

    /**
     * Makes sure the launcher is set up for {@code versionId}.
     *
     * @return a short description of what was changed, or {@code null} when nothing had to change
     */
    public static String applyForVersion(Context context, String versionId) {
        if (context == null || !MinecraftCompat.requiresModernGl(versionId)) return null;
        markInstance(versionId);

        boolean changed = false;
        SharedPreferences pref = prefs(context);

        // 1. Zero-copy surface: TextureView is the path that black-screens the new pipeline.
        if (pref != null && !pref.getBoolean("alternate_surface", true)) {
            pref.edit().putBoolean("alternate_surface", true).apply();
            LauncherPreferences.PREF_USE_ALTERNATE_SURFACE = true;
            changed = true;
        }

        // 2. Renderer: swap a GL2-only wrapper for the first ladder entry this device supports.
        MinecraftProfile profile = safeCurrentProfile();
        String currentRenderer = profile == null ? null : profile.pojavRendererName;
        if (!MinecraftCompat.isModernCapable(currentRenderer)) {
            String replacement = pickRenderer(context);
            if (replacement != null && !replacement.equals(currentRenderer)) {
                if (pref != null && currentRenderer != null
                        && !pref.contains(KEY_ORIGINAL_RENDERER)) {
                    pref.edit().putString(KEY_ORIGINAL_RENDERER, currentRenderer).apply();
                }
                if (profile != null) {
                    profile.pojavRendererName = replacement;
                    safeWrite();
                }
                Tools.LOCAL_RENDERER = replacement;
                changed = true;
                Log.i(TAG, "Renderer switched for " + versionId + ": " + currentRenderer
                        + " -> " + replacement);
            }
        }

        return changed ? MinecraftCompat.compatSummary(versionId,
                profile == null ? null : profile.pojavRendererName) : null;
    }

    /** Walks to the next ladder entry that this device reports as compatible. */
    public static String cycleStep(Context context) {
        SharedPreferences pref = prefs(context);
        int next = step(context) + 1;
        String applied = null;
        for (int i = 0; i < RENDERER_LADDER.length; i++) {
            int index = (next + i) % RENDERER_LADDER.length;
            String candidate = RENDERER_LADDER[index];
            if (!isCompatible(context, candidate)) continue;
            MinecraftProfile profile = safeCurrentProfile();
            if (profile != null) {
                profile.pojavRendererName = candidate;
                safeWrite();
            }
            Tools.LOCAL_RENDERER = candidate;
            applied = candidate;
            if (pref != null) pref.edit().putInt(KEY_STEP, index).apply();
            break;
        }
        return applied;
    }

    /** Short label for the HUD, e.g. {@code "MODERN GL FIX · ZINK"}. */
    public static String statusLabel(Context context) {
        MinecraftProfile profile = safeCurrentProfile();
        String renderer = profile == null ? Tools.LOCAL_RENDERER : profile.pojavRendererName;
        if (!MinecraftCompat.isModernCapable(renderer)) return "BLACK SCREEN FIX";
        return "GL3 FIX: " + shortRendererName(renderer);
    }

    public static String shortRendererName(String renderer) {
        if (renderer == null) return "DEFAULT";
        if (renderer.contains("kopper")) return "ZINK KOPPER";
        if (renderer.contains("zink")) return "ZINK";
        if (renderer.contains("mobileglues")) return "MOBILEGLUES";
        if (renderer.contains("ltw")) return "ANGLE";
        if (renderer.contains("KW")) return "KRYPTON";
        if (renderer.contains("opengles2")) return "GL4ES";
        return renderer.toUpperCase(java.util.Locale.ROOT);
    }

    private static String pickRenderer(Context context) {
        for (String candidate : RENDERER_LADDER) {
            if (isCompatible(context, candidate)) return candidate;
        }
        return null;
    }

    private static boolean isCompatible(Context context, String renderer) {
        try {
            List<String> compatible = Tools.getCompatibleRenderers(context).rendererIds;
            return compatible != null && compatible.contains(renderer);
        } catch (Throwable ignored) {
            return false;
        }
    }

    /** The profile file is also written by the UI thread; a failed write must not crash us. */
    private static void safeWrite() {
        try {
            LauncherProfiles.write();
        } catch (Throwable e) {
            Log.w(TAG, "Could not persist the renderer change", e);
        }
    }

    private static MinecraftProfile safeCurrentProfile() {
        try {
            return LauncherProfiles.getCurrentProfile();
        } catch (Throwable ignored) {
            return null;
        }
    }
}
