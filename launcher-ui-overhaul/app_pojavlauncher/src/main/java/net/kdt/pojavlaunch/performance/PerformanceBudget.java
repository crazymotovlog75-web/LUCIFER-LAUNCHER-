package net.kdt.pojavlaunch.performance;

/**
 * Android-free half of {@link PerformanceMode}: the numbers and the string handling that decide how
 * much memory the game may use and which JVM flags are injected. Kept free of Android imports so it
 * can be covered by plain JVM unit tests.
 */
public final class PerformanceBudget {

    /**
     * Extra JVM flags injected while Performance Mode is on. {@code DisableExplicitGC} stops mods
     * that call {@code System.gc()} from freezing the render thread; {@code MaxGCPauseMillis} asks
     * a generational collector to keep pauses short. Collectors that do not implement a flag ignore
     * it, so these cannot break a launch.
     */
    public static final String[] PERF_JVM_FLAGS = {
            "-XX:+DisableExplicitGC",
            "-XX:MaxGCPauseMillis=20",
    };

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

    /** Appends the stability flags that are not present yet, preserving the user's own arguments. */
    public static String addPerfFlags(String current) {
        String base = current == null ? "" : current.trim();
        StringBuilder builder = new StringBuilder(base);
        for (String flag : PERF_JVM_FLAGS) {
            if (builder.indexOf(flag) >= 0) continue;
            if (builder.length() > 0) builder.append(' ');
            builder.append(flag);
        }
        return builder.toString();
    }

    /** Removes the stability flags this launcher injected, leaving every other argument intact. */
    public static String removePerfFlags(String current) {
        String result = current == null ? "" : current;
        for (String flag : PERF_JVM_FLAGS) {
            result = result.replace(flag, "");
        }
        return result.replaceAll("\\s+", " ").trim();
    }
}
