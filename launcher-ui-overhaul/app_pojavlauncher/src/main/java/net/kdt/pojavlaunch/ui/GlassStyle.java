package net.kdt.pojavlaunch.ui;

import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Rect;
import android.graphics.RectF;
import android.util.AttributeSet;

import net.kdt.pojavlaunch.R;

/**
 * Geometry + paint kit for a single liquid-glass pane.
 *
 * One instance lives in every {@link GlassFrameLayout} / {@link GlassLinearLayout}; it is only
 * mutated from the UI thread so the drawing path never allocates.
 */
final class GlassStyle {
    /** Radius in px, negative means "auto = 18% of the short side". */
    float radiusPx = -1f;
    /** White veil over the refracted wallpaper, 0..255. */
    int tint = 70;
    /** Extra darkening towards the bottom, 0..255. */
    int scrim = 118;
    /** Lens magnification, 0..0.2. */
    float refraction = 0.05f;
    /** Draw the lens rim hairlines. */
    boolean rim = true;

    final Path path = new Path();
    final RectF box = new RectF();
    final Rect src = new Rect();
    final RectF dst = new RectF();
    final int[] location = new int[2];

    final Paint bitmapPaint = new Paint(Paint.FILTER_BITMAP_FLAG | Paint.DITHER_FLAG);
    final Paint tintPaint = new Paint(Paint.DITHER_FLAG);
    final Paint scrimPaint = new Paint(Paint.DITHER_FLAG);
    final Paint sheenPaint = new Paint(Paint.DITHER_FLAG);
    final Paint rimPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    final Paint accentPaint = new Paint(Paint.ANTI_ALIAS_FLAG);

    private int cacheW, cacheH;
    private int cacheTint = -1;

    GlassStyle() {
        rimPaint.setStyle(Paint.Style.STROKE);
        accentPaint.setStyle(Paint.Style.STROKE);
    }

    void read(Context context, AttributeSet attrs) {
        if (attrs == null) return;
        TypedArray array = context.obtainStyledAttributes(attrs, R.styleable.LiquidGlassPane);
        try {
            radiusPx = array.getDimension(R.styleable.LiquidGlassPane_lgRadius, -1f);
            tint = array.getInt(R.styleable.LiquidGlassPane_lgTint, tint);
            scrim = array.getInt(R.styleable.LiquidGlassPane_lgScrim, scrim);
            refraction = array.getFloat(R.styleable.LiquidGlassPane_lgRefraction, refraction);
            rim = array.getBoolean(R.styleable.LiquidGlassPane_lgRim, rim);
        } finally {
            array.recycle();
        }
        if (tint < 0) tint = 0;
        if (tint > 255) tint = 255;
        if (scrim < 0) scrim = 0;
        if (scrim > 255) scrim = 255;
        if (refraction < 0f) refraction = 0f;
        if (refraction > 0.2f) refraction = 0.2f;
    }

    boolean shadersStale(int w, int h) {
        return cacheW != w || cacheH != h || cacheTint != tint;
    }

    void markShadersBuilt(int w, int h) {
        cacheW = w;
        cacheH = h;
        cacheTint = tint;
    }
}
