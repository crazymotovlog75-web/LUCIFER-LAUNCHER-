package net.kdt.pojavlaunch.ui;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorMatrix;
import android.graphics.ColorMatrixColorFilter;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.graphics.drawable.Drawable;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/**
 * Liquid crystal clear rendering for the launcher UI.
 *
 * <p>The wallpaper painted behind the launcher is captured once, shrunk and box-blurred. Every
 * glass pane then draws the part of that blurred wallpaper that sits behind itself (slightly
 * magnified, like a lens), a white veil, a bottom scrim, a specular sweep and the three rim
 * hairlines. That is the same stack the iOS liquid-glass material uses, and it keeps a pane
 * readable on any wallpaper instead of faking the look with a flat translucent box.</p>
 *
 * <p>Everything is bitmap blits and gradients, so a screen full of panes costs one textured quad
 * each - no RenderScript, no per-frame blur, no extra full-screen pass.</p>
 */
public final class LiquidGlass {

    private static final int MAX_BACKDROP_EDGE = 320;
    private static final float BRIGHTNESS = 1.04f;
    private static final float SATURATION = 1.12f;

    private static final List<WeakReference<View>> PANES = new ArrayList<>();
    private static final int[] ROOT_LOCATION = new int[2];
    private static final Paint BACKDROP_PAINT = new Paint(Paint.FILTER_BITMAP_FLAG | Paint.DITHER_FLAG);

    @Nullable
    private static Bitmap sBackdrop;
    private static int sRootWidth = 1;
    private static int sRootHeight = 1;

    private LiquidGlass() {}

    /** Captures the activity backdrop once it has been laid out. Safe to call repeatedly. */
    public static void install(@NonNull final View root) {
        root.post(new Runnable() {
            @Override
            public void run() {
                capture(root);
            }
        });
    }

    /** Re-captures the backdrop, e.g. after the wallpaper or theme changed. */
    public static void refresh(@NonNull View root) {
        capture(root);
        invalidatePanes();
    }

    private static void capture(@NonNull View root) {
        int width = root.getWidth();
        int height = root.getHeight();
        if (width <= 0 || height <= 0) return;

        int thumbW = Math.max(24, Math.min(MAX_BACKDROP_EDGE, width / 6));
        int thumbH = Math.max(24, Math.round(thumbW * (height / (float) width)));

        Bitmap base;
        try {
            base = Bitmap.createBitmap(thumbW, thumbH, Bitmap.Config.ARGB_8888);
        } catch (OutOfMemoryError error) {
            return;
        }

        Canvas canvas = new Canvas(base);
        canvas.scale(thumbW / (float) width, thumbH / (float) height);
        Drawable background = root.getBackground();
        if (background != null) {
            background.setBounds(0, 0, width, height);
            try {
                background.draw(canvas);
            } catch (RuntimeException ignored) {
                canvas.drawColor(0xFF0B2330);
            }
        } else {
            canvas.drawColor(0xFF0B2330);
        }

        // Box blur on a tiny bitmap: ~19k pixels, three passes, done once per layout.
        boxBlur(base, 3);
        base.setHasAlpha(false);

        ColorMatrix matrix = new ColorMatrix();
        matrix.setSaturation(SATURATION);
        ColorMatrix brighten = new ColorMatrix(new float[]{
                BRIGHTNESS, 0f, 0f, 0f, 6f,
                0f, BRIGHTNESS, 0f, 0f, 6f,
                0f, 0f, BRIGHTNESS, 0f, 6f,
                0f, 0f, 0f, 1f, 0f
        });
        matrix.postConcat(brighten);
        BACKDROP_PAINT.setColorFilter(new ColorMatrixColorFilter(matrix));

        Bitmap previous = sBackdrop;
        sBackdrop = base;
        sRootWidth = Math.max(1, width);
        sRootHeight = Math.max(1, height);
        root.getLocationInWindow(ROOT_LOCATION);
        if (previous != null && !previous.isRecycled()) previous.recycle();
        invalidatePanes();
    }

    public static void register(@NonNull View pane) {
        synchronized (PANES) {
            Iterator<WeakReference<View>> iterator = PANES.iterator();
            while (iterator.hasNext()) {
                View view = iterator.next().get();
                if (view == null) {
                    iterator.remove();
                } else if (view == pane) {
                    return;
                }
            }
            PANES.add(new WeakReference<>(pane));
        }
    }

    public static void unregister(@NonNull View pane) {
        synchronized (PANES) {
            Iterator<WeakReference<View>> iterator = PANES.iterator();
            while (iterator.hasNext()) {
                View view = iterator.next().get();
                if (view == null || view == pane) iterator.remove();
            }
        }
    }

    public static void invalidatePanes() {
        synchronized (PANES) {
            for (WeakReference<View> reference : PANES) {
                View view = reference.get();
                if (view != null) view.invalidate();
            }
        }
    }

    /**
     * Paints one pane. Called from {@code dispatchDraw()} so the glass lands above the activity
     * wallpaper and below the pane's own children.
     */
    public static void drawPane(@NonNull Canvas canvas, @NonNull View view, @NonNull GlassStyle style) {
        int width = view.getWidth();
        int height = view.getHeight();
        if (width <= 0 || height <= 0) return;

        float radius = style.radiusPx;
        if (radius < 0f) radius = Math.min(width, height) * 0.18f;
        radius = Math.min(radius, Math.min(width, height) * 0.5f);

        style.box.set(0f, 0f, width, height);
        style.path.reset();
        style.path.addRoundRect(style.box, radius, radius, android.graphics.Path.Direction.CW);

        int checkpoint = canvas.save();
        int save = canvas.save();
        canvas.clipPath(style.path);

        // 1. the wallpaper behind the pane, magnified a hair so the rim bends it like a lens
        boolean hasBackdrop = false;
        Bitmap backdrop = sBackdrop;
        if (backdrop != null && !backdrop.isRecycled()) {
            view.getLocationInWindow(style.location);
            float scaleX = backdrop.getWidth() / (float) sRootWidth;
            float scaleY = backdrop.getHeight() / (float) sRootHeight;
            float left = (style.location[0] - ROOT_LOCATION[0]) * scaleX;
            float top = (style.location[1] - ROOT_LOCATION[1]) * scaleY;
            float right = left + width * scaleX;
            float bottom = top + height * scaleY;
            float bleedX = (right - left) * style.refraction * 0.5f;
            float bleedY = (bottom - top) * style.refraction * 0.5f;
            style.src.set(
                    Math.round(left - bleedX),
                    Math.round(top - bleedY),
                    Math.round(right + bleedX),
                    Math.round(bottom + bleedY));
            style.dst.set(0f, 0f, width, height);
            canvas.drawBitmap(backdrop, style.src, style.dst, BACKDROP_PAINT);
            hasBackdrop = true;
        }
        if (!hasBackdrop) {
            style.tintPaint.setShader(new LinearGradient(0f, 0f, 0f, height,
                    Color.argb(Math.min(255, style.tint + 70), 233, 245, 250),
                    Color.argb(Math.min(255, style.tint + 30), 150, 196, 216),
                    Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, width, height, style.tintPaint);
            style.tintPaint.setShader(null);
        }

        // 2. white veil: strong at the top edge, thin at the bottom
        if (style.tint > 0) {
            style.tintPaint.setShader(new LinearGradient(0f, 0f, 0f, height,
                    Color.argb(style.tint, 255, 255, 255),
                    Color.argb(Math.round(style.tint * 0.34f), 255, 255, 255),
                    Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, width, height, style.tintPaint);
            style.tintPaint.setShader(null);
        }

        // 3. a whisper of navy, then the bottom scrim that keeps white type readable
        canvas.drawColor(Color.argb(14, 12, 24, 38));
        if (style.scrim > 0) {
            style.scrimPaint.setShader(new LinearGradient(0f, height * 0.22f, 0f, height,
                    Color.argb(0, 8, 22, 34),
                    Color.argb(style.scrim, 8, 22, 34),
                    Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, width, height, style.scrimPaint);
            style.scrimPaint.setShader(null);
        }

        // 4. specular sweep across the top third
        style.sheenPaint.setShader(new LinearGradient(0f, 0f, 0f, height * 0.32f,
                Color.argb(46, 255, 255, 255),
                Color.argb(0, 255, 255, 255),
                Shader.TileMode.CLAMP));
        canvas.drawRect(0f, 0f, width, height * 0.32f, style.sheenPaint);
        style.sheenPaint.setShader(null);

        canvas.restoreToCount(save);

        // 5. lens rim: one bright hairline outside, two softer inside, plus the thick bottom edge
        if (style.rim) {
            float density = view.getResources().getDisplayMetrics().density;
            style.rimPaint.setShader(null);
            style.rimPaint.setColor(Color.argb(236, 255, 255, 255));
            style.rimPaint.setStrokeWidth(Math.max(1f, 1.1f * density));
            canvas.drawPath(style.path, style.rimPaint);

            float inset = Math.max(1f, 1.2f * density);
            style.box.set(inset, inset, width - inset, height - inset);
            style.path.reset();
            style.path.addRoundRect(style.box, Math.max(1f, radius - inset), Math.max(1f, radius - inset),
                    android.graphics.Path.Direction.CW);
            style.rimPaint.setColor(Color.argb(96, 255, 255, 255));
            style.rimPaint.setStrokeWidth(Math.max(1f, 0.9f * density));
            canvas.drawPath(style.path, style.rimPaint);

            // thickness of the glass along the bottom curve
            style.rimPaint.setShader(new LinearGradient(0f, height * 0.78f, 0f, height,
                    Color.argb(0, 255, 255, 255), Color.argb(64, 255, 255, 255),
                    Shader.TileMode.CLAMP));
            style.rimPaint.setColor(Color.WHITE);
            style.rimPaint.setStrokeWidth(Math.max(1f, 1.6f * density));
            canvas.drawPath(style.path, style.rimPaint);
            style.rimPaint.setShader(null);
        }

        // 6. selected: the accent runs round the rim and lights the top edge
        if (view.isSelected()) {
            float density = view.getResources().getDisplayMetrics().density;
            style.box.set(0f, 0f, width, height);
            style.path.reset();
            style.path.addRoundRect(style.box, radius, radius, android.graphics.Path.Direction.CW);
            style.accentPaint.setColor(0xFF2FE9FF);
            style.accentPaint.setStrokeWidth(Math.max(1.4f, 1.6f * density));
            canvas.drawPath(style.path, style.accentPaint);

            style.accentPaint.setShader(new LinearGradient(0f, 0f, width, 0f,
                    Color.argb(150, 47, 233, 255), Color.argb(30, 47, 233, 255),
                    Shader.TileMode.CLAMP));
            style.accentPaint.setStrokeWidth(Math.max(2f, 2.4f * density));
            canvas.drawPath(style.path, style.accentPaint);
            style.accentPaint.setShader(null);
        } else {
            // corner glint, so a pane still reads as glass when nothing is selected
            style.tintPaint.setShader(new RadialGradient(
                    width * 0.26f, height * 0.06f, Math.max(width, height) * 0.40f,
                    new int[]{Color.argb(40, 255, 255, 255), Color.argb(0, 255, 255, 255)},
                    null, Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, width, height * 0.34f, style.tintPaint);
            style.tintPaint.setShader(null);
        }

        canvas.restoreToCount(checkpoint);
    }

    /** Separable box blur, three passes: enough to read as frosted glass on a small bitmap. */
    private static void boxBlur(@NonNull Bitmap bitmap, int radius) {
        int width = bitmap.getWidth();
        int height = bitmap.getHeight();
        if (width < 4 || height < 4 || radius < 1) return;

        int[] pixels = new int[width * height];
        int[] scratch = new int[width * height];
        bitmap.getPixels(pixels, 0, width, 0, 0, width, height);

        for (int pass = 0; pass < 3; pass++) {
            blurPass(pixels, scratch, width, height, radius, true);
            blurPass(scratch, pixels, width, height, radius, false);
        }
        bitmap.setPixels(pixels, 0, width, 0, 0, width, height);
    }

    private static void blurPass(int[] in, int[] out, int width, int height, int radius,
                                 boolean horizontal) {
        int outer = horizontal ? height : width;
        int inner = horizontal ? width : height;
        int taps = radius * 2 + 1;

        for (int o = 0; o < outer; o++) {
            for (int i = 0; i < inner; i++) {
                int a = 0, r = 0, g = 0, b = 0;
                for (int k = -radius; k <= radius; k++) {
                    int sample = i + k;
                    if (sample < 0) sample = 0;
                    if (sample >= inner) sample = inner - 1;
                    int color = horizontal ? in[o * width + sample] : in[sample * width + o];
                    a += (color >>> 24) & 0xFF;
                    r += (color >> 16) & 0xFF;
                    g += (color >> 8) & 0xFF;
                    b += color & 0xFF;
                }
                int packed = ((a / taps) << 24) | ((r / taps) << 16) | ((g / taps) << 8) | (b / taps);
                out[horizontal ? o * width + i : i * width + o] = packed;
            }
        }
    }
}
