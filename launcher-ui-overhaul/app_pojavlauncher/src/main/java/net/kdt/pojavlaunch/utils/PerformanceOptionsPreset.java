package net.kdt.pojavlaunch.utils;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

import net.kdt.pojavlaunch.compat.VersionEra;
import net.kdt.pojavlaunch.compat.VersionTuning;

/**
 * Reversible, per-era Minecraft video settings for the FPS profile.
 *
 * <p>The keys are produced by {@link VersionTuning#videoOptions(VersionEra)}, so a 1.8.9 instance
 * gets {@code limitFramerate} and a 1.21.11 instance gets {@code maxFps} + {@code simulationDistance}.
 * Everything written is recorded in the snapshot, which is what makes switching the profile off
 * restore exactly the values the user had (and remove keys that did not exist before).
 */
public final class PerformanceOptionsPreset {

    private PerformanceOptionsPreset() { }

    /** What the instance looked like before the profile was applied. */
    public static final class Snapshot {
        /** Values the user had, for every key the profile ever wrote. */
        public Map<String, String> originalValues = new LinkedHashMap<>();
        /** Keys that did not exist before the profile wrote them. */
        public Set<String> originallyMissing = new LinkedHashSet<>();
        /** Values the profile wrote, so restore can tell its own edits from the user's. */
        public Map<String, String> appliedValues = new LinkedHashMap<>();
    }

    /** Options for one era. */
    public static Map<String, String> forEra(VersionEra era) {
        return Collections.unmodifiableMap(VersionTuning.videoOptions(era));
    }

    /**
     * Records the instance's current values for everything this era will write, keeping anything a
     * previous run already captured (the era can change when the user switches instance).
     *
     * @param existing  snapshot read from disk, or {@code null} on the first apply
     * @param current   the instance's options as loaded from {@code options.txt}
     * @param era       version era of the instance being launched
     */
    public static Snapshot capture(Snapshot existing, Map<String, String> current, VersionEra era) {
        Snapshot snapshot = isValidSnapshot(existing) ? existing : new Snapshot();
        if (snapshot.originalValues == null) snapshot.originalValues = new LinkedHashMap<>();
        if (snapshot.originallyMissing == null) snapshot.originallyMissing = new LinkedHashSet<>();
        if (snapshot.appliedValues == null) snapshot.appliedValues = new LinkedHashMap<>();

        Map<String, String> options = forEra(era);
        for (Map.Entry<String, String> entry : options.entrySet()) {
            String key = entry.getKey();
            if (snapshot.originalValues.containsKey(key) || snapshot.originallyMissing.contains(key)) {
                continue; // already captured by an earlier apply
            }
            if (current.containsKey(key)) {
                snapshot.originalValues.put(key, current.get(key));
            } else {
                snapshot.originallyMissing.add(key);
            }
        }
        // Remember what we are about to write, for every era applied to this instance.
        snapshot.appliedValues.putAll(options);
        return snapshot;
    }

    /** Writes the era options into the instance map. */
    public static void apply(Map<String, String> currentOptions, VersionEra era) {
        currentOptions.putAll(forEra(era));
    }

    /** Convenience overload used before an era is known (tests, legacy callers). */
    public static void apply(Map<String, String> currentOptions) {
        apply(currentOptions, VersionEra.MODERN);
    }

    /**
     * Restores an option only if it still holds the value this preset wrote. An option the user
     * changed while the profile was on is kept as the user left it.
     */
    public static void restore(Map<String, String> currentOptions, Snapshot snapshot) {
        if (!isValidSnapshot(snapshot)) return;

        Map<String, String> applied = snapshot.appliedValues;
        if (applied == null || applied.isEmpty()) {
            // Snapshots written by older builds: fall back to the modern table.
            applied = forEra(VersionEra.MODERN);
        }
        for (Map.Entry<String, String> entry : applied.entrySet()) {
            String key = entry.getKey();
            if (!Objects.equals(currentOptions.get(key), entry.getValue())) continue;
            if (snapshot.originallyMissing != null && snapshot.originallyMissing.contains(key)) {
                currentOptions.remove(key);
            } else if (snapshot.originalValues != null) {
                String original = snapshot.originalValues.get(key);
                if (original != null) currentOptions.put(key, original);
            }
        }
    }

    public static boolean isValidSnapshot(Snapshot snapshot) {
        return snapshot != null
                && snapshot.originalValues != null
                && snapshot.originallyMissing != null;
    }
}
