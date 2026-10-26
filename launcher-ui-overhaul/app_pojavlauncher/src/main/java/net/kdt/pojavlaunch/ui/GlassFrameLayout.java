package net.kdt.pojavlaunch.ui;

import android.content.Context;
import android.graphics.Canvas;
import android.util.AttributeSet;
import android.widget.FrameLayout;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

/**
 * A {@link FrameLayout} that paints the liquid-glass material behind its children.
 *
 * Use it exactly like a FrameLayout; the material is drawn in {@code dispatchDraw()} so it stays
 * above the wallpaper and below the content, and it follows the pane's own size, radius and
 * selected state.
 */
public class GlassFrameLayout extends FrameLayout {

    private final GlassStyle mStyle = new GlassStyle();

    public GlassFrameLayout(@NonNull Context context) {
        this(context, null);
    }

    public GlassFrameLayout(@NonNull Context context, @Nullable AttributeSet attrs) {
        this(context, attrs, 0);
    }

    public GlassFrameLayout(@NonNull Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        mStyle.read(context, attrs);
        setWillNotDraw(false);
    }

    @Override
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        LiquidGlass.register(this);
    }

    @Override
    protected void onDetachedFromWindow() {
        LiquidGlass.unregister(this);
        super.onDetachedFromWindow();
    }

    @Override
    protected void onSizeChanged(int width, int height, int oldWidth, int oldHeight) {
        super.onSizeChanged(width, height, oldWidth, oldHeight);
        invalidate();
    }

    @Override
    public void setSelected(boolean selected) {
        super.setSelected(selected);
        invalidate();
    }

    @Override
    protected void dispatchDraw(Canvas canvas) {
        LiquidGlass.drawPane(canvas, this, mStyle);
        super.dispatchDraw(canvas);
    }
}
