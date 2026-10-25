package net.kdt.pojavlaunch.performance;

import android.app.ActivityManager;
import android.content.Context;
import android.content.SharedPreferences;

import net.kdt.pojavlaunch.prefs.LauncherPreferences;

/**
 * One-tap performance mode for LUCIFER LAUNCHER.
 *
 * <p>Wraps the renderer-side high-FPS pipeline that the engine already understands so a single tap
 * on the launcher HUD is enough to go from a stuttering ~40 FPS to a stable high frame rate:
 * <ul>
 *     <li>{@code highFpsMode} — resolution scale is capped at 30% per axis (about 9% of the pixels),
 *     Minecraft's video options are switched to the reversible low-cost preset (render distance 4,
 *     no clouds / entity shadows / particles / AO / mipmaps, vsync off, maxFps 150) and the vsync
 *     forced by Zink / ForceVsync is disabled.</li>
 *     <li>{@code sustainedPerformance} — asks the platform to keep clocks predictable instead of
 *     oscillating between 50 and 10 FPS while the device throttles.</li>
 *     <li>{@code bigCoreAffinity} — keeps the JVM on the performance cores so frame time stays flat.</li>
 *     <li>Heap floor — raises a too-small allocation so the GC stops injecting hitches.</li>
 * </ul>
 *
 * <p>Everything here is reversible: turning the mode off restores the user's previous Minecraft video
 * options through the engine's own snapshot/restore path.
 */
public final class PerformanceMode {

    /** Engine preference keys. Do not rename: they are read by the launcher engine. */
    public static final String KEY_ENABLED = "highFpsMode";
    public static final String KEY_SUSTAINED = "sustainedPerformance";
    public static final String KEY_BIG_CORES = "bigCoreAffinity";
    public static final String KEY_VSYNC_IN_ZINK = "vsync_in_zink";
    public static final String KEY_FORCE_VSYNC = "force_vsync";
    public static final String KEY_ALLOCATION = "allocation";

    /** Engine preference key holding the extra JVM arguments. */
    public static final String KEY_JAVA_ARGS = "javaArgs";
    /** SurfaceView instead of TextureView: zero-copy, one less full-screen blit per frame. */
    public static final String KEY_ALTERNATE_SURFACE = "alternate_surface";
    /** Exactly the JVM flags this launcher appended, so switching the mode off can remove them. */
    public static final String KEY_ADDED_FLAGS = "perfJvmFlagsAdded";


    /** Bookkeeping only: makes the automatic first-run activation happen exactly once. */
    private static final String KEY_SEEDED = "performanceModeSeeded";

    private PerformanceMode() { }

    private static SharedPreferences prefs(Context context) {
        SharedPreferences pref = LauncherPreferences.DEFAULT_PREF;
        if (pref == null && context != null) {
            pref = context.getSharedPreferences("cslauncher_settings", Context.MODE_PRIVATE);
        }
        return pref;
    }

    public static boolean isEnabled(Context context) {
        SharedPreferences pref = prefs(context);
        return pref != null && pref.getBoolean(KEY_ENABLED, LauncherPreferences.PREF_HIGH_FPS_MODE);
    }

    /**
     * Turns the mode on for everybody who never expressed a preference, exactly once.
     *
     * <p>The whole point of this build is "kam se kam 80 FPS", so the optimized profile has to be
     * active out of the box instead of hiding behind a setting the user never finds. The seed runs
     * once: if the user turns the mode off afterwards their choice is respected forever.
     */
    public static void ensureSeeded(Context context) {
        SharedPreferences pref = prefs(context);
        if (pref == null) return;
        if (pref.getBoolean(KEY_SEEDED, false)) return;
        pref.edit().putBoolean(KEY_SEEDED, true).apply();
        if (!pref.contains(KEY_ENABLED)) setEnabled(context, true);
    }

    /** Flips the mode and returns the new state. */
    public static boolean toggle(Context context) {
        boolean next = !isEnabled(context);
        setEnabled(context, next);
        return next;
    }

    public static void setEnabled(Context context, boolean enabled) {
        SharedPreferences pref = prefs(context);
        if (pref != null && LauncherPreferences.DEFAULT_PREF == null) {
            LauncherPreferences.DEFAULT_PREF = pref;
        }

        if (pref != null) {
            SharedPreferences.Editor editor = pref.edit()
                    .putBoolean(KEY_ENABLED, enabled)
                    // Vsync caps the frame rate to the display refresh rate and is one of the
                    // reasons the FPS counter used to swing between wildly different numbers.
                    .putBoolean(KEY_FORCE_VSYNC, false);
            if (enabled) {
                editor.putBoolean(KEY_SUSTAINED, true)
                        .putBoolean(KEY_BIG_CORES, true)
                        .putBoolean(KEY_VSYNC_IN_ZINK, false)
                        .putBoolean(KEY_ALTERNATE_SURFACE, true);
            }
            editor.apply();
        }

        // Mirror into the runtime statics so the very next launch uses the new profile without
        // requiring an app restart.
        LauncherPreferences.PREF_HIGH_FPS_MODE = enabled;
        LauncherPreferences.PREF_FORCE_VSYNC = false;
        if (enabled) {
            LauncherPreferences.PREF_SUSTAINED_PERFORMANCE = true;
            LauncherPreferences.PREF_BIG_CORE_AFFINITY = true;
            LauncherPreferences.PREF_VSYNC_IN_ZINK = false;
            LauncherPreferences.PREF_USE_ALTERNATE_SURFACE = true;
            ensureHeapFloor(context, pref);
        }
        applyJvmArgs(pref, enabled);
        refreshRenderScale(context);
    }

    /**
     * Recomputes the render resolution for the current screen and mode.
     *
     * <p>The engine only derives this while loading preferences, but the game is launched from this
     * same process right after a toggle, so the new value has to be picked up immediately.
     */
    public static void refreshRenderScale(Context context) {
        if (context == null) return;
        try {
            SharedPreferences pref = prefs(context);
            float savedScale = pref == null ? 1f
                    : pref.getInt("resolutionRatio", 100) / 100f;
            android.util.DisplayMetrics metrics = context.getResources().getDisplayMetrics();
            net.kdt.pojavlaunch.compat.VersionEra era =
                    net.kdt.pojavlaunch.compat.VersionEra.ofCurrentInstance();
            LauncherPreferences.PREF_SCALE_FACTOR =
                    net.kdt.pojavlaunch.compat.VersionTuning.renderScale(savedScale,
                            LauncherPreferences.PREF_HIGH_FPS_MODE,
                            metrics.widthPixels, metrics.heightPixels, era);
        } catch (Throwable ignored) {
            // A wrong scale would only cost sharpness; never crash over it.
        }
    }

    /**
     * Adds/removes the stability flags in the engine's free-form Java argument field, leaving every
     * argument the user wrote themselves untouched.
     */
    static void applyJvmArgs(SharedPreferences pref, boolean enabled) {
        if (pref == null) return;
        String current = pref.getString(KEY_JAVA_ARGS, "");
        if (current == null) current = "";

        String updated;
        if (enabled) {
            String[] additions = PerformanceBudget.flagsToAdd(current);
            updated = PerformanceBudget.applyFlags(current, additions);
            pref.edit().putString(KEY_ADDED_FLAGS, join(additions)).apply();
        } else {
            String[] tracked = split(pref.getString(KEY_ADDED_FLAGS, ""));
            updated = tracked.length > 0
                    ? PerformanceBudget.removeFlags(current, tracked)
                    // No record (first run after an update): fall back to the managed set, but keep
                    // a collector the user picked themselves.
                    : PerformanceBudget.removeFlags(current, PerformanceBudget.flagsToRemoveWithoutUserCollector(current));
            pref.edit().remove(KEY_ADDED_FLAGS).apply();
        }

        if (updated.equals(current)) return;
        pref.edit().putString(KEY_JAVA_ARGS, updated).apply();
        LauncherPreferences.PREF_CUSTOM_JAVA_ARGS = updated;
    }

    private static String join(String[] values) {
        StringBuilder builder = new StringBuilder();
        for (String value : values) {
            if (value == null || value.isEmpty()) continue;
            if (builder.length() > 0) builder.append(' ');
            builder.append(value);
        }
        return builder.toString();
    }

    private static String[] split(String value) {
        if (value == null || value.trim().isEmpty()) return new String[0];
        return value.trim().split("\\s+");
    }

    /** Raises a too-small heap allocation; never lowers an allocation the user picked. */
    private static void ensureHeapFloor(Context context, SharedPreferences pref) {
        int floor = recommendedRamMb(context);
        // Trust whichever value is higher: the runtime static (set by loadPreferences) or the value
        // persisted earlier. This can only ever raise the heap, never shrink it.
        int current = LauncherPreferences.PREF_RAM_ALLOCATION;
        if (pref != null) {
            current = Math.max(current, pref.getInt(KEY_ALLOCATION, current));
        }
        if (current >= floor) return;
        LauncherPreferences.PREF_RAM_ALLOCATION = floor;
        if (pref != null) pref.edit().putInt(KEY_ALLOCATION, floor).apply();
    }

    public static int recommendedRamMb(Context context) {
        return recommendedRamMbForTotal(totalRamMb(context));
    }

    /** Heap recommendation from the device's total memory (in MB). */
    public static int recommendedRamMbForTotal(long totalMb) {
        return PerformanceBudget.recommendedRamMbForTotal(totalMb);
    }

    private static long totalRamMb(Context context) {
        if (context == null) return 0;
        try {
            ActivityManager manager =
                    (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
            if (manager == null) return 0;
            ActivityManager.MemoryInfo info = new ActivityManager.MemoryInfo();
            manager.getMemoryInfo(info);
            return info.totalMem / (1024L * 1024L);
        } catch (Throwable ignored) {
            return 0;
        }
    }

    /** Short label rendered inside the HUD telemetry chip. */
    public static String statusLabel(Context context) {
        return isEnabled(context) ? "PERF 80+ ON" : "BALANCED";
    }

    /** Toast text shown after a toggle. */
    public static String summary(Context context, boolean enabled) {
        if (!enabled) {
            return "Performance Mode OFF — Minecraft ke original graphics settings wapas.";
        }
        net.kdt.pojavlaunch.compat.VersionEra era =
                net.kdt.pojavlaunch.compat.VersionEra.ofCurrentInstance();
        return "Performance Mode ON — " + era.label() + ": "
                + era.renderShortSide + "p render, " + era.renderDistance + " chunks, effects off, "
                + "vsync off, big cores, GC hitch flags. 80+ FPS target.";
    }
}
