package net.kdt.pojavlaunch.utils;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class HighFpsRenderScaleTest {

    @Test
    public void largePanelIsBudgetedToTheRequestedShortSide() {
        float scale = HighFpsRenderScale.resolveForSize(1f, true, 2400, 1080, 800, 0.45f);
        assertEquals(800f, 1080 * scale, 2f);
    }

    @Test
    public void smallPanelKeepsTheSavedValueInsteadOfGettingBlurred() {
        assertEquals(1f, HighFpsRenderScale.resolveForSize(1f, true, 1280, 720, 800, 0.45f), 0f);
        assertEquals(0.8f, HighFpsRenderScale.resolveForSize(0.8f, true, 1280, 720, 800, 0.45f), 0f);
    }

    @Test
    public void profileNeverShrinksBelowTheQualityFloor() {
        float scale = HighFpsRenderScale.resolveForSize(1f, true, 3840, 2160, 800, 0.45f);
        assertEquals(0.45f, scale, 0f);
    }

    @Test
    public void disabledProfileLeavesTheUserValueAlone() {
        assertEquals(1f, HighFpsRenderScale.resolveForSize(1f, false, 2400, 1080, 800, 0.45f), 0f);
        assertEquals(0.75f, HighFpsRenderScale.resolve(0.75f, false), 0f);
    }

    @Test
    public void sharperThanTheOldThirtyPercentCap() {
        float oldScale = 0.30f;
        float newScale = HighFpsRenderScale.resolveForSize(1f, true, 2400, 1080, 800, 0.45f);
        assertTrue("sharpness must not regress",
                HighFpsRenderScale.pixelWorkloadFraction(newScale)
                        > 3 * HighFpsRenderScale.pixelWorkloadFraction(oldScale));
    }

    @Test
    public void invalidInputFallsBackToNative() {
        assertEquals(1f, HighFpsRenderScale.resolve(Float.NaN, true), 0f);
        assertEquals(800f / 1080f,
                HighFpsRenderScale.resolveForSize(0f, true, 1920, 1080, 800, 0.45f), 0.01f);
    }

    @Test
    public void degenerateSizesDoNotProduceZeroOrNegativeScales() {
        float scale = HighFpsRenderScale.resolveForSize(1f, true, 0, 0, 800, 0.45f);
        assertTrue(scale > 0f);
        assertTrue(scale <= 1f);
    }
}
