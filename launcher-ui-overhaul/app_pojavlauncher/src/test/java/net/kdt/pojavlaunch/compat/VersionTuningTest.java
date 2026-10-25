package net.kdt.pojavlaunch.compat;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.util.Arrays;
import java.util.Map;

/** The era table must produce keys the matching Minecraft build really understands. */
public class VersionTuningTest {

    @Test
    public void legacyVersionsGetTheLegacyFrameLimiter() {
        Map<String, String> options = VersionTuning.videoOptions(VersionEra.LEGACY_LWJGL2);
        assertEquals(VersionTuning.UNLIMITED_FPS, options.get("limitFramerate"));
        assertFalse(options.containsKey("maxFps"));
        assertEquals("false", options.get("fancyGraphics"));
        assertEquals("false", options.get("ambientOcclusion"));
        assertFalse("modern 'ao' key must not be written for legacy builds",
                options.containsKey("ao"));
        assertEquals("true", options.get("useVbo"));
        assertEquals("false", options.get("clouds"));
        assertFalse(options.containsKey("simulationDistance"));
        assertFalse(options.containsKey("graphicsMode"));
    }

    @Test
    public void lwjgl3SwapstoMaxFpsAndKeepsModernTogglesOff() {
        Map<String, String> options = VersionTuning.videoOptions(VersionEra.LWJGL3);
        assertEquals(VersionTuning.UNLIMITED_FPS, options.get("maxFps"));
        assertFalse(options.containsKey("limitFramerate"));
        assertEquals("0", options.get("graphicsMode"));
        assertEquals("false", options.get("renderClouds"));
        // simulationDistance only exists from 1.17 on.
        assertFalse(options.containsKey("simulationDistance"));
    }

    @Test
    public void modernVersionsLowerSimulationDistanceToo() {
        for (VersionEra era : new VersionEra[]{
                VersionEra.MODERN, VersionEra.MODERN_21, VersionEra.NEW_PIPELINE}) {
            Map<String, String> options = VersionTuning.videoOptions(era);
            assertEquals("4", options.get("simulationDistance"));
            assertEquals(String.valueOf(era.renderDistance), options.get("renderDistance"));
        }
    }

    @Test
    public void everyEraDisablesTheExpensiveEffects() {
        for (VersionEra era : VersionEra.values()) {
            Map<String, String> options = VersionTuning.videoOptions(era);
            assertEquals("false", options.get("enableVsync"));
            assertEquals("false", options.get("clouds"));
            assertEquals("false", options.get("entityShadows"));
            assertEquals("2", options.get("particles"));
            assertTrue("ambient occlusion must be off in every era",
                    options.containsKey("ao") || options.containsKey("ambientOcclusion"));
            assertNotNull(options.get("renderDistance"));
            assertNotNull(options.get("mipmapLevels"));
        }
    }

    @Test
    public void noOptionValueIsEverBlank() {
        for (VersionEra era : VersionEra.values()) {
            for (Map.Entry<String, String> entry : VersionTuning.videoOptions(era).entrySet()) {
                assertNotNull("null value for " + entry.getKey(), entry.getValue());
                assertFalse("blank value for " + entry.getKey(), entry.getValue().trim().isEmpty());
                assertFalse("null key in " + era, entry.getKey() == null);
            }
        }
    }

    @Test
    public void renderScaleIsPerEraAndStaysAboveTheFloor() {
        // 1080p-class phone.
        float legacy = VersionTuning.renderScale(1f, true, 2400, 1080, VersionEra.LEGACY_LWJGL2);
        float modern = VersionTuning.renderScale(1f, true, 2400, 1080, VersionEra.NEW_PIPELINE);
        assertEquals("legacy eras can afford sharper frames", 1.0f, legacy, 0.001f);
        assertTrue(modern < legacy);

        // 4K panel: the floor protects the image quality.
        float huge = VersionTuning.renderScale(1f, true, 3840, 2160, VersionEra.NEW_PIPELINE);
        assertEquals(VersionEra.NEW_PIPELINE.minRenderScale, huge, 0.001f);
    }

    @Test
    public void renderScaleIsUntouchedWhenTheProfileIsOff() {
        assertEquals(1f, VersionTuning.renderScale(1f, false, 2400, 1080, VersionEra.NEW_PIPELINE), 0f);
        assertEquals(0.5f,
                VersionTuning.renderScale(0.5f, false, 2400, 1080, VersionEra.LEGACY_LWJGL2), 0f);
    }

    @Test
    public void jvmFlagsAreTheGcStabilitySet() {
        String joined = Arrays.toString(VersionTuning.jvmFlags());
        assertTrue(joined.contains("-XX:+DisableExplicitGC"));
        assertTrue(joined.contains("-XX:MaxGCPauseMillis=20"));
        assertTrue(joined.contains("-XX:+AlwaysPreTouch"));
        assertTrue(joined.contains("-XX:+PerfDisableSharedMem"));
        assertTrue(joined.contains("-XX:+UseG1GC"));
    }

    @Test
    public void legacyRecipesOnlyContainLegacySafeProperties() {
        String[] legacy = VersionTuning.systemProperties(VersionEra.LEGACY_LWJGL2);
        String joined = Arrays.toString(legacy);
        assertTrue(joined.contains("allowSoftwareOpenGL=false"));
        assertFalse(joined.contains("maxCachedBufferSize"));

        String[] modern = VersionTuning.systemProperties(VersionEra.NEW_PIPELINE);
        assertTrue(Arrays.toString(modern).contains("maxCachedBufferSize"));
    }

    @Test
    public void driverEnvQuietsTheLegacyWrapper() {
        assertTrue(VersionTuning.driverEnv(VersionEra.LEGACY_LWJGL2).containsKey("LIBGL_NOBANNER"));
        assertEquals("0", VersionTuning.driverEnv(VersionEra.NEW_PIPELINE).get("vblank_mode"));
    }
}
