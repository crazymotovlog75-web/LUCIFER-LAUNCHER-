package net.kdt.pojavlaunch.utils;

/**
 * Resolution budget used by the FPS profile.
 *
 * <p>The budget is expressed in <b>pixels of the short side</b> instead of a percentage, because a
 * percentage means wildly different things on different panels: 30% of a 1080p phone is 324 px tall
 * (unreadable), while 30% of a 720p phone is 216 px. Each Minecraft era asks for a different target
 * through {@link net.kdt.pojavlaunch.compat.VersionTuning}, since a 1.8.9 frame is far cheaper than
 * a 1.21.11 one.
 *
 * <p>The cost model is unchanged: {@code scale * scale} of the pixels of the full-resolution frame.
 */
public final class HighFpsRenderScale {
    /** Default target short side; the era table overrides this. */
    public static final int TARGET_SHORT_SIDE = 800;

    /** Default floor: below it the upscale becomes visibly mushy. */
    public static final float MIN_SCALE = 0.45f;

    /** Hard ceiling, so a tiny panel can never end up rendering above native. */
    public static final float MAX_SCALE = 1.0f;

    private HighFpsRenderScale() { }

    /** Era-aware entry point. */
    public static float resolveForSize(float savedScale, boolean highFpsEnabled,
                                       int widthPx, int heightPx,
                                       int targetShortSide, float minScale) {
        float saved = sanitize(savedScale);
        float floor = clamp(minScale, 0.1f, MAX_SCALE);
        int target = targetShortSide <= 0 ? TARGET_SHORT_SIDE : targetShortSide;
        if (!highFpsEnabled) return saved;
        if (widthPx <= 0 || heightPx <= 0) return clamp(saved, floor, MAX_SCALE);

        int shortSide = Math.min(widthPx, heightPx);
        if (shortSide <= target) {
            // The panel is already at or below the budget: rendering lower than the user asked for
            // would only add blur without buying frames.
            return clamp(saved, floor, MAX_SCALE);
        }
        float budgeted = (float) target / (float) shortSide;
        return clamp(Math.min(saved, budgeted), floor, MAX_SCALE);
    }

    /** Default-budget variant, kept for callers that do not know the instance era yet. */
    public static float resolveForSize(float savedScale, boolean highFpsEnabled,
                                       int widthPx, int heightPx) {
        return resolveForSize(savedScale, highFpsEnabled, widthPx, heightPx,
                TARGET_SHORT_SIDE, MIN_SCALE);
    }

    /** Version without view dimensions: applies the quality floor/ceiling only. */
    public static float resolve(float savedScale, boolean highFpsEnabled) {
        float saved = sanitize(savedScale);
        if (!highFpsEnabled) return saved;
        return clamp(saved, MIN_SCALE, MAX_SCALE);
    }

    /** Number of pixels actually shaded, relative to a native-resolution frame. */
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
