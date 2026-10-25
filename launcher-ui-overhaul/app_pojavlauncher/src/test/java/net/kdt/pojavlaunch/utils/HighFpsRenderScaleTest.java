package net.kdt.pojavlaunch.utils;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class HighFpsRenderScaleTest {

    @Test
    public void largePanelIsBudgetedToTheTargetShortSide() {
        // 16:9 1080p-class phone in landscape.
        float scale = HighFpsRenderScale.resolveForSize(1f, true, 2400, 1080);
        float shortSide = 1080 * scale;
        assertEquals(HighFpsRenderScale.TARGET_SHORT_SIDE, shortSide, 2f);
    }

    @Test
    public void smallPanelKeepsTheSavedValueInsteadOfGettingBlurred() {
        assertEquals(1f, HighFpsRenderScale.resolveForSize(1f, true, 1280, 720), 0f);
        assertEquals(0.8f, HighFpsRenderScale.resolveForSize(0.8f, true, 1280, 720), 0f);
    }

    @Test
    public void profileNeverShrinksBelowTheQualityFloor() {
        // A 4K panel would ask for 800/2160 = 0.37, the floor keeps it readable.
        float scale = HighFpsRenderScale.resolveForSize(1f, true, 3840, 2160);
        assertEquals(HighFpsRenderScale.MIN_SCALE, scale, 0f);
    }

    @Test
    public void disabledProfileLeavesTheUserValueAlone() {
        assertEquals(1f, HighFpsRenderScale.resolveForSize(1f, false, 2400, 1080), 0f);
        assertEquals(0.75f, HighFpsRenderScale.resolve(0.75f, false), 0f);
    }

    @Test
    public void rendersFarMorePixelsThanTheOldThirtyPercentCap() {
        float oldScale = 0.30f;
        float newScale = HighFpsRenderScale.resolveForSize(1f, true, 2400, 1080);
        assertTrue("sharpness must not regress",
                HighFpsRenderScale.pixelWorkloadFraction(newScale)
                        > 3 * HighFpsRenderScale.pixelWorkloadFraction(oldScale));
    }

    @Test
    public void invalidInputFallsBackToNative() {
        assertEquals(1f, HighFpsRenderScale.resolve(Float.NaN, true), 0f);
        assertEquals(HighFpsRenderScale.TARGET_SHORT_SIDE / 1080f,
                HighFpsRenderScale.resolveForSize(0f, true, 1920, 1080), 0.01f);
    }
}
