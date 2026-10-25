package net.kdt.pojavlaunch.compat;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

/** Every Minecraft release family must land in the era whose option keys it actually reads. */
public class VersionEraTest {

    @Test
    public void preThreeVersionsUseTheGl1Era() {
        assertEquals(VersionEra.LEGACY_GL1, VersionEra.of("1.0"));
        assertEquals(VersionEra.LEGACY_GL1, VersionEra.of("1.2.5"));
    }

    @Test
    public void lwjgl2EraCoversOneThreeToTwelve() {
        assertEquals(VersionEra.LEGACY_LWJGL2, VersionEra.of("1.3.2"));
        assertEquals(VersionEra.LEGACY_LWJGL2, VersionEra.of("1.7.10"));
        assertEquals(VersionEra.LEGACY_LWJGL2, VersionEra.of("1.8.9"));
        assertEquals(VersionEra.LEGACY_LWJGL2, VersionEra.of("1.12.2"));
        // Forge/Fabric ids carry the Minecraft version last.
        assertEquals(VersionEra.LEGACY_LWJGL2, VersionEra.of("forge-1.12.2-14.23.5.2860"));
        assertEquals(VersionEra.LEGACY_LWJGL2, VersionEra.of("fabric-loader-0.15.11-1.8.9"));
    }

    @Test
    public void lwjgl3EraCoversThirteenToSixteen() {
        assertEquals(VersionEra.LWJGL3, VersionEra.of("1.13.2"));
        assertEquals(VersionEra.LWJGL3, VersionEra.of("1.14.4"));
        assertEquals(VersionEra.LWJGL3, VersionEra.of("1.16.5"));
    }

    @Test
    public void modernEraCoversSeventeenToTwentySix() {
        assertEquals(VersionEra.MODERN, VersionEra.of("1.17.1"));
        assertEquals(VersionEra.MODERN, VersionEra.of("1.19.2"));
        assertEquals(VersionEra.MODERN, VersionEra.of("1.20.6"));
    }

    @Test
    public void twentyOneIsSplitAtDotEleven() {
        assertEquals(VersionEra.MODERN_21, VersionEra.of("1.21"));
        assertEquals(VersionEra.MODERN_21, VersionEra.of("1.21.4"));
        assertEquals(VersionEra.MODERN_21, VersionEra.of("1.21.10"));
        assertEquals(VersionEra.NEW_PIPELINE, VersionEra.of("1.21.11"));
        assertEquals(VersionEra.NEW_PIPELINE, VersionEra.of("1.21.12"));
        assertEquals(VersionEra.NEW_PIPELINE, VersionEra.of("fabric-loader-0.16.9-1.21.11"));
    }

    @Test
    public void futureReleasesAndSnapshotsUseTheNewestEra() {
        assertEquals(VersionEra.NEW_PIPELINE, VersionEra.of("1.22"));
        assertEquals(VersionEra.NEW_PIPELINE, VersionEra.of("1.23.4"));
        assertEquals(VersionEra.NEW_PIPELINE, VersionEra.of("25w31a"));
        assertEquals(VersionEra.NEW_PIPELINE, VersionEra.of("1.21.11-pre2"));
    }

    @Test
    public void unknownIdsFallBackToTheNeutralEra() {
        assertEquals(VersionEra.MODERN, VersionEra.of(null));
        assertEquals(VersionEra.MODERN, VersionEra.of(""));
        assertEquals(VersionEra.MODERN, VersionEra.of("custom-build"));
    }

    @Test
    public void eraCapabilitiesMatchTheRealOptionKeys() {
        assertTrue(VersionEra.LEGACY_LWJGL2.isLegacyLwjgl2());
        assertFalse(VersionEra.LEGACY_LWJGL2.usesMaxFpsKey());
        assertFalse(VersionEra.LEGACY_LWJGL2.usesSimulationDistance());
        assertFalse(VersionEra.LEGACY_LWJGL2.usesGraphicsMode());

        assertTrue(VersionEra.LWJGL3.usesMaxFpsKey());
        assertFalse(VersionEra.LWJGL3.usesSimulationDistance());

        assertTrue(VersionEra.MODERN.usesSimulationDistance());
        assertTrue(VersionEra.NEW_PIPELINE.usesSimulationDistance());
    }

    @Test
    public void newerErasGetTighterBudgets() {
        assertTrue(VersionEra.LEGACY_LWJGL2.renderShortSide
                > VersionEra.NEW_PIPELINE.renderShortSide);
        assertTrue(VersionEra.LEGACY_LWJGL2.renderDistance
                > VersionEra.NEW_PIPELINE.renderDistance);
        assertTrue(VersionEra.LEGACY_LWJGL2.minRenderScale
                > VersionEra.NEW_PIPELINE.minRenderScale);
    }
}
