package net.kdt.pojavlaunch.ui;

import android.content.Context;
import android.graphics.Canvas;
import android.util.AttributeSet;
import android.widget.LinearLayout;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

/**
 * A {@link LinearLayout} that paints the liquid-glass material behind its children.
 *
 * Used for the side rail, its items, the header pill and the quick-launch chips: same layout
 * behaviour as a normal LinearLayout, with the glass drawn underneath the content.
 */
public class GlassLinearLayout extends LinearLayout {

    private final GlassStyle mStyle = new GlassStyle();

    public GlassLinearLayout(@NonNull Context context) {
        this(context, null);
    }

    public GlassLinearLayout(@NonNull Context context, @Nullable AttributeSet attrs) {
        this(context, attrs, 0);
    }

    public GlassLinearLayout(@NonNull Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
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
