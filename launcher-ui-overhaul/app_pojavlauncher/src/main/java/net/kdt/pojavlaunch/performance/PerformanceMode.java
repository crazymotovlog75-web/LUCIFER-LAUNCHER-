package net.kdt.pojavlaunch.performance;

import android.content.Context;
import android.content.SharedPreferences;

import net.kdt.pojavlaunch.prefs.LauncherPreferences;

/**
 * Rollback of the forced FPS profile introduced in v2.7 - v3.1.
 *
 * <p>Those builds shipped a "Performance Mode" that was switched on automatically and, on top of the
 * reversible video preset, also forced CPU affinity, sustained clock mode, a higher heap, a lower
 * render resolution and a set of JVM flags. Users reported the result was slower than the plain
 * engine defaults, so this class now only exists to undo that state exactly once and then keep the
 * launcher on the engine's own defaults.
 *
 * <p>Nothing here turns performance work back on: there is no toggle any more.
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
    /** Exactly the JVM flags the old profile appended. */
    public static final String KEY_ADDED_FLAGS = "perfJvmFlagsAdded";

    /** Bookkeeping: the rollback has already run on this install. */
    private static final String KEY_ROLLED_BACK = "perfProfileRolledBackV32";

    private PerformanceMode() { }

    private static SharedPreferences prefs(Context context) {
        SharedPreferences pref = LauncherPreferences.DEFAULT_PREF;
        if (pref == null && context != null) {
            pref = context.getSharedPreferences("cslauncher_settings", Context.MODE_PRIVATE);
        }
        return pref;
    }

    /**
     * Undoes the forced profile once per install.
     *
     * <p>It is safe to call on every launcher start: after the first run the flag is set and the
     * method returns immediately. The user's own Minecraft video options come back because the
     * engine restores its options snapshot whenever {@code highFpsMode} is off.
     */
    public static void rollbackOnce(Context context) {
        SharedPreferences pref = prefs(context);
        if (pref == null) return;
        if (pref.getBoolean(KEY_ROLLED_BACK, false)) return;

        SharedPreferences.Editor editor = pref.edit()
                .putBoolean(KEY_ROLLED_BACK, true)
                .putBoolean(KEY_ENABLED, false)
                // CPU / clock pins that the profile forced on. Leaving them in place is precisely
                // what made frame times worse on some devices, so they go back to engine defaults.
                .remove(KEY_BIG_CORES)
                .remove(KEY_SUSTAINED);

        // Remove only the JVM flags this launcher appended; anything the user wrote stays.
        String currentArgs = pref.getString(KEY_JAVA_ARGS, "");
        if (currentArgs == null) currentArgs = "";
        String[] tracked = split(pref.getString(KEY_ADDED_FLAGS, ""));
        String[] toRemove = tracked.length > 0
                ? tracked
                : PerformanceBudget.flagsToRemoveWithoutUserCollector(currentArgs);
        String cleanedArgs = PerformanceBudget.removeFlags(currentArgs, toRemove);
        if (!cleanedArgs.equals(currentArgs)) editor.putString(KEY_JAVA_ARGS, cleanedArgs);
        editor.remove(KEY_ADDED_FLAGS);

        editor.apply();

        // Mirror into the runtime statics so nothing in this process re-applies the profile.
        LauncherPreferences.PREF_HIGH_FPS_MODE = false;
        LauncherPreferences.PREF_BIG_CORE_AFFINITY = false;
        LauncherPreferences.PREF_SUSTAINED_PERFORMANCE = false;
        if (!cleanedArgs.equals(currentArgs)) {
            LauncherPreferences.PREF_CUSTOM_JAVA_ARGS = cleanedArgs;
        }
    }

    private static String[] split(String value) {
        if (value == null || value.trim().isEmpty()) return new String[0];
        return value.trim().split("\\s+");
    }
}
