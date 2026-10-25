package net.kdt.pojavlaunch.performance;

/**
 * Android-free half of {@link PerformanceMode}: the numbers and the string handling that decide how
 * much memory the game may use and which JVM flags are injected. Kept free of Android imports so it
 * can be covered by plain JVM unit tests.
 */
public final class PerformanceBudget {

    /**
     * Extra JVM flags injected while Performance Mode is on, one source of truth with
     * {@link net.kdt.pojavlaunch.compat.VersionTuning#jvmFlags()}.
     *
     * <p>{@code DisableExplicitGC} stops mods that call {@code System.gc()} from freezing the render
     * thread, {@code MaxGCPauseMillis} keeps pauses short, {@code AlwaysPreTouch} removes the page
     * faults that show up as random 10 FPS seconds, and {@code PerfDisableSharedMem} avoids the
     * JVM writing perf counters to disk mid-frame. All of them are plain HotSpot flags supported by
     * every Java version the launcher ships, so they cannot break a launch.
     */
    public static final String[] PERF_JVM_FLAGS =
            net.kdt.pojavlaunch.compat.VersionTuning.jvmFlags();

    private PerformanceBudget() { }

    /**
     * Heap size for the game based on how much RAM the device reports, in MB.
     *
     * <p>The point is a floor, not a ceiling: a 700 MB heap on a 6 GB phone makes the garbage
     * collector run constantly, which is exactly the "50 FPS, then 10 FPS" stutter pattern.
     */
    public static int recommendedRamMbForTotal(long totalMb) {
        if (totalMb <= 0) return 2048;
        if (totalMb <= 3072) return 1024;
        if (totalMb <= 4096) return 1536;
        if (totalMb <= 6144) return 2560;
        if (totalMb <= 8192) return 3072;
        return 4096;
    }

    /**
     * Garbage collector selectors. HotSpot refuses to start when two of them are present
     * ("Multiple garbage collectors selected"), so a collector the user chose is never overridden.
     */
    private static final String[] GC_SELECTORS = {
            "-XX:+UseSerialGC",
            "-XX:+UseParallelGC",
            "-XX:+UseConcMarkSweepGC",
            "-XX:+UseG1GC",
            "-XX:+UseZGC",
            "-XX:+UseShenandoahGC",
    };

    /**
     * The subset of {@link #PERF_JVM_FLAGS} that should be appended to {@code current}: skips flags
     * that are already there and never adds a second garbage collector.
     */
    public static String[] flagsToAdd(String current) {
        String base = current == null ? "" : current.trim();
        boolean userPickedCollector = hasAnyGcSelector(base);
        java.util.List<String> additions = new java.util.ArrayList<>();
        for (String flag : PERF_JVM_FLAGS) {
            if (base.contains(flag)) continue;
            // Respect an existing collector choice: adding a second one would stop the JVM.
            if (userPickedCollector && isGcSelector(flag)) continue;
            additions.add(flag);
        }
        return additions.toArray(new String[0]);
    }

    /** Appends the stability flags that are not present yet, preserving the user's own arguments. */
    public static String addPerfFlags(String current) {
        return applyFlags(current, flagsToAdd(current));
    }

    /** Appends exactly the given flags. */
    public static String applyFlags(String current, String[] flags) {
        StringBuilder builder = new StringBuilder(current == null ? "" : current.trim());
        if (flags == null) return builder.toString();
        for (String flag : flags) {
            if (flag == null || flag.isEmpty() || builder.indexOf(flag) >= 0) continue;
            if (builder.length() > 0) builder.append(' ');
            builder.append(flag);
        }
        return builder.toString();
    }

    /** Removes exactly the given flags (the ones this launcher added), keeping everything else. */
    public static String removeFlags(String current, String[] flags) {
        String result = current == null ? "" : current;
        if (flags != null) {
            for (String flag : flags) {
                if (flag == null || flag.isEmpty()) continue;
                result = result.replace(flag, "");
            }
        }
        return result.replaceAll("\\s+", " ").trim();
    }

    /**
     * The managed flags minus a GC selector the user wrote themselves. Used when there is no record
     * of what this launcher added, so a manual collector choice survives.
     */
    public static String[] flagsToRemoveWithoutUserCollector(String current) {
        boolean userPickedCollector = hasAnyGcSelector(current == null ? "" : current);
        if (!userPickedCollector) return PERF_JVM_FLAGS;
        java.util.List<String> removable = new java.util.ArrayList<>();
        for (String flag : PERF_JVM_FLAGS) {
            if (isGcSelector(flag)) continue;
            removable.add(flag);
        }
        return removable.toArray(new String[0]);
    }

    public static boolean isGcSelector(String flag) {
        for (String selector : GC_SELECTORS) {
            if (selector.equals(flag)) return true;
        }
        return false;
    }

    public static boolean hasAnyGcSelector(String arguments) {
        if (arguments == null) return false;
        for (String selector : GC_SELECTORS) {
            if (arguments.contains(selector)) return true;
        }
        return false;
    }

    /**
     * Best-effort removal of the whole managed flag set. Used when the launcher has no record of
     * which flags it added (first run after an update); {@link #removeFlags} is preferred.
     */
    public static String removePerfFlags(String current) {
        return removeFlags(current, PERF_JVM_FLAGS);
    }
}
