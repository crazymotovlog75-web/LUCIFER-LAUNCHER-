package net.kdt.pojavlaunch.utils;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import net.kdt.pojavlaunch.compat.VersionEra;
import net.kdt.pojavlaunch.compat.VersionTuning;

import org.junit.Test;

import java.util.HashMap;
import java.util.Map;

public class PerformanceOptionsPresetTest {

    @Test
    public void presetIsReversibleForTheEraItWasAppliedTo() {
        Map<String, String> options = new HashMap<>();
        options.put("renderDistance", "12");
        options.put("graphicsMode", "2");
        options.put("enableVsync", "true");
        options.put("mipmapLevels", "4");
        Map<String, String> original = new HashMap<>(options);

        VersionEra era = VersionEra.NEW_PIPELINE;
        PerformanceOptionsPreset.Snapshot snapshot =
                PerformanceOptionsPreset.capture(null, options, era);
        PerformanceOptionsPreset.apply(options, era);

        assertEquals("4", options.get("renderDistance"));
        assertEquals("4", options.get("simulationDistance"));
        assertEquals("false", options.get("enableVsync"));
        assertEquals(VersionTuning.UNLIMITED_FPS, options.get("maxFps"));
        assertEquals("0", options.get("graphicsMode"));
        assertTrue(PerformanceOptionsPreset.isValidSnapshot(snapshot));

        PerformanceOptionsPreset.restore(options, snapshot);
        assertEquals(original, options);
    }

    @Test
    public void legacyInstancesGetLegacyKeysAndARestoreThatRemovesThem() {
        Map<String, String> options = new HashMap<>();
        options.put("renderDistance", "8");
        options.put("limitFramerate", "120");
        Map<String, String> original = new HashMap<>(options);

        VersionEra era = VersionEra.LEGACY_LWJGL2;
        PerformanceOptionsPreset.Snapshot snapshot =
                PerformanceOptionsPreset.capture(null, options, era);
        PerformanceOptionsPreset.apply(options, era);

        assertEquals(VersionTuning.UNLIMITED_FPS, options.get("limitFramerate"));
        assertFalse("legacy builds have no maxFps option", options.containsKey("maxFps"));
        assertNull("legacy builds have no simulationDistance option",
                options.get("simulationDistance"));

        PerformanceOptionsPreset.restore(options, snapshot);
        assertEquals(original, options);
    }

    @Test
    public void restoreKeepsOptionsChangedByTheUserWhileTheProfileWasOn() {
        Map<String, String> options = new HashMap<>();
        options.put("renderDistance", "12");
        options.put("graphicsMode", "2");

        VersionEra era = VersionEra.MODERN;
        PerformanceOptionsPreset.Snapshot snapshot =
                PerformanceOptionsPreset.capture(null, options, era);
        PerformanceOptionsPreset.apply(options, era);
        options.put("renderDistance", "8");
        options.put("maxFps", "90");

        PerformanceOptionsPreset.restore(options, snapshot);

        assertEquals("8", options.get("renderDistance"));
        assertEquals("90", options.get("maxFps"));
        assertEquals("2", options.get("graphicsMode"));
        assertFalse(options.containsKey("simulationDistance"));
    }

    @Test
    public void switchingEraMergesTheSnapshotInsteadOfLosingOriginals() {
        Map<String, String> options = new HashMap<>();
        options.put("renderDistance", "10");
        options.put("limitFramerate", "120");

        // First launch of a 1.8.9 instance.
        PerformanceOptionsPreset.Snapshot legacy =
                PerformanceOptionsPreset.capture(null, options, VersionEra.LEGACY_LWJGL2);
        PerformanceOptionsPreset.apply(options, VersionEra.LEGACY_LWJGL2);

        // Same instance folder later opened by a 1.21.11 build.
        PerformanceOptionsPreset.Snapshot merged =
                PerformanceOptionsPreset.capture(legacy, options, VersionEra.NEW_PIPELINE);
        PerformanceOptionsPreset.apply(options, VersionEra.NEW_PIPELINE);

        assertEquals("4", options.get("simulationDistance"));

        PerformanceOptionsPreset.restore(options, merged);
        assertEquals("10", options.get("renderDistance"));
        assertEquals("120", options.get("limitFramerate"));
        assertFalse(options.containsKey("simulationDistance"));
        assertFalse(options.containsKey("maxFps"));
    }

    @Test
    public void invalidSnapshotNeverTouchesTheOptions() {
        Map<String, String> options = new HashMap<>();
        options.put("renderDistance", "4");
        Map<String, String> copy = new HashMap<>(options);

        PerformanceOptionsPreset.restore(options, null);
        assertEquals(copy, options);
        assertFalse(PerformanceOptionsPreset.isValidSnapshot(null));
    }
}
