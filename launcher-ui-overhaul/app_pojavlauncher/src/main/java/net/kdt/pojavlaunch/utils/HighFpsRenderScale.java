package net.kdt.pojavlaunch.utils;

/**
 * Resolution budget used by the high-FPS profile.
 *
 * <p>Older builds capped the render surface at a flat 30% per axis, which on a 1080p phone means
 * 576x324 — the game looked badly blurred. This version budgets by <b>pixels of short side</b>
 * instead of by percentage, so the surface stays sharp on small screens, never exceeds the saved
 * user value, and still cannot explode on a 1440p panel.
 *
 * <p>The cost model is unchanged: {@code scale * scale} of the pixels of the full-resolution frame.
 */
public final class HighFpsRenderScale {
    /**
     * Target short side (in pixels) of the render surface while high-FPS mode is on. 800 px keeps
     * text and block edges readable on 1080p-class panels (about 1778x800 instead of 720x324)
     * while still leaving the GPU a lot of headroom compared to native resolution.
     */
    public static final int TARGET_SHORT_SIDE = 800;

    /** Never shrink below this: below it the upscale becomes visibly mushy again. */
    public static final float MIN_SCALE = 0.45f;

    /** Hard ceiling for the profile, so a tiny panel cannot end up rendering above native. */
    public static final float MAX_SCALE = 1.0f;

    private HighFpsRenderScale() { }

    /**
     * Scale for the given view dimensions.
     *
     * @param savedScale     the resolution slider value the user picked (1f = native)
     * @param highFpsEnabled whether the high-FPS profile is active
     * @param widthPx        width of the view that will hold the game surface
     * @param heightPx       height of the view that will hold the game surface
     */
    public static float resolveForSize(float savedScale, boolean highFpsEnabled,
                                       int widthPx, int heightPx) {
        float saved = sanitize(savedScale);
        if (!highFpsEnabled) return saved;
        if (widthPx <= 0 || heightPx <= 0) return clamp(saved, MIN_SCALE, MAX_SCALE);

        int shortSide = Math.min(widthPx, heightPx);
        if (shortSide <= TARGET_SHORT_SIDE) {
            // Panel is already at or below the budget: rendering lower than the user asked for
            // would only add blur without buying any frames.
            return clamp(saved, MIN_SCALE, MAX_SCALE);
        }
        float budgeted = (float) TARGET_SHORT_SIDE / (float) shortSide;
        return clamp(Math.min(saved, budgeted), MIN_SCALE, MAX_SCALE);
    }

    /**
     * Version without view dimensions: applies the quality floor/ceiling only. Used where the exact
     * surface size is not known yet; {@link #resolveForSize} is preferred whenever it is.
     */
    public static float resolve(float savedScale, boolean highFpsEnabled) {
        float saved = sanitize(savedScale);
        if (!highFpsEnabled) return saved;
        return clamp(saved, MIN_SCALE, MAX_SCALE);
    }

    public static float pixelWorkloadFraction(float scale) {
        return scale * scale;
    }

    private static float sanitize(float scale) {
        if (Float.isNaN(scale) || Float.isInfinite(scale) || scale <= 0f) return 1f;
        return scale;
    }

    private static float clamp(float value, float min, float max) {
        return Math.max(min, Math.min(max, value));
    }
}
