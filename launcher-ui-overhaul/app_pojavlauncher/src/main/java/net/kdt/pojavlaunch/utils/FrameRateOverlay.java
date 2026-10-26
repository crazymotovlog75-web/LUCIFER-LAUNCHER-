package net.kdt.pojavlaunch.utils;

import android.annotation.SuppressLint;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.os.Handler;
import android.os.Looper;
import android.util.TypedValue;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;

import net.kdt.pojavlaunch.prefs.LauncherPreferences;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.Locale;

/**
 * In-game FPS read-out that shows the <em>measured</em> frame rate, not a guess.
 *
 * <p>The number comes from {@code org.lwjgl.glfw.FrameStats} inside the game's JVM: it hooks
 * {@code glfwSwapBuffers}, so every counted frame is a frame the game really presented. That class
 * writes a small text record to {@code <cache>/lucifer-fps.txt} twice a second and this view only
 * renders what it wrote. If the file is missing or stale the overlay says so instead of inventing a
 * number — an FPS display that lies is worse than no display at all.
 *
 * <p>The badge is always on top of the game, and it can be dragged anywhere; the position is stored
 * as a fraction of the parent so it survives rotation and different screen sizes.
 */
@SuppressLint("ViewConstructor")
public class FrameRateOverlay extends View {

    /** File written by {@code FrameStats} inside the game process. */
    public static final String FPS_FILE_NAME = "lucifer-fps.txt";

    private static final String PREF_X = "fpsOverlayX";
    private static final String PREF_Y = "fpsOverlayY";
    private static final long POLL_INTERVAL_MS = 400L;
    /** Older than this and the readout is no longer describing the present. */
    private static final long STALE_MS = 2500L;

    private final Paint mBackgroundPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint mLabelPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint mValuePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint mDetailPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF mBounds = new RectF();
    private final Handler mHandler = new Handler(Looper.getMainLooper());
    private final File mFile;
    private final int mPadH;
    private final int mPadV;

    private int mFps = -1;              // -1 = no measurement yet
    private int mFrameMillis = 0;
    private long mLastRecordAt = 0L;
    private boolean mWaiting = true;    // true until the first real record arrives

    private String mContext = null;   // e.g. "MOBILEGLUES · 1.21.11", from the launcher itself

    private float mDownX, mDownY;
    private float mStartX, mStartY;
    private boolean mDragging;
    private final float mTouchSlop;

    private final Runnable mPoll = new Runnable() {
        @Override public void run() {
            readStats();
            invalidate();
            mHandler.postDelayed(this, POLL_INTERVAL_MS);
        }
    };

    public FrameRateOverlay(Context context) {
        super(context);
        mFile = new File(context.getCacheDir(), FPS_FILE_NAME);
        mTouchSlop = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 8,
                context.getResources().getDisplayMetrics());
        float density = context.getResources().getDisplayMetrics().density;

        mBackgroundPaint.setColor(Color.argb(148, 4, 18, 26));
        mBackgroundPaint.setStyle(Paint.Style.FILL);

        mLabelPaint.setColor(Color.parseColor("#7FE9FF"));
        mLabelPaint.setTextSize(9f * density);
        mLabelPaint.setTypeface(Typeface.create(Typeface.MONOSPACE, Typeface.BOLD));
        mLabelPaint.setLetterSpacing(0.16f);

        mValuePaint.setColor(Color.parseColor("#EAFCFF"));
        mValuePaint.setTextSize(21f * density);
        mValuePaint.setTypeface(Typeface.create(Typeface.MONOSPACE, Typeface.BOLD));

        mDetailPaint.setColor(Color.parseColor("#9FE6F4"));
        mDetailPaint.setTextSize(10f * density);
        mDetailPaint.setTypeface(Typeface.create(Typeface.MONOSPACE, Typeface.NORMAL));

        mPadH = Math.round(10f * density);
        mPadV = Math.round(5f * density);
        setClickable(true);
    }

    /** Adds the overlay on top of everything in {@code parent}, restoring the saved position. */
    public static FrameRateOverlay attach(ViewGroup parent, Context context) {
        return attach(parent, context, null);
    }

    /**
     * @param context line describing the renderer + instance the frames come from, shown under the
     *                number so it is always obvious what the measurement belongs to
     */
    public static FrameRateOverlay attach(ViewGroup parent, Context context, String contextLine) {
        FrameRateOverlay overlay = new FrameRateOverlay(context);
        overlay.mContext = contextLine;
        ViewGroup.LayoutParams params = new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        parent.addView(overlay, params);

        SharedPreferences pref = LauncherPreferences.DEFAULT_PREF;
        float fx = pref == null ? 0.98f : pref.getFloat(PREF_X, 0.98f);
        float fy = pref == null ? 0.04f : pref.getFloat(PREF_Y, 0.04f);
        overlay.setTag(new float[]{fx, fy});
        return overlay;
    }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        mHandler.post(mPoll);
    }

    @Override protected void onDetachedFromWindow() {
        mHandler.removeCallbacks(mPoll);
        super.onDetachedFromWindow();
    }

    /** Reads whatever the game last wrote. Never fabricates a value. */
    private void readStats() {
        if (!mFile.isFile()) {
            mWaiting = true;
            return;
        }
        long stamp = mFile.lastModified();
        if (stamp <= 0L) return;
        try (BufferedReader reader = new BufferedReader(new FileReader(mFile))) {
            String line = reader.readLine();
            if (line == null) return;
            String[] parts = line.trim().split("\\s+");
            if (parts.length < 2) return;
            int fps = Integer.parseInt(parts[0]);
            int millis = Integer.parseInt(parts[1]);
            if (fps < 0) return;
            mFps = fps;
            mFrameMillis = millis;
            mLastRecordAt = stamp;
            mWaiting = false;
        } catch (Exception ignored) {
            // Torn read or the writer is mid-rename: keep the previous real sample.
        }
    }

    @Override protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        String value = mWaiting ? "--" : String.valueOf(mFps);
        String detail = mWaiting
                ? "measuring"
                : String.format(Locale.ROOT, "%d ms", mFrameMillis);
        float width = Math.max(mValuePaint.measureText(value), mDetailPaint.measureText(detail));
        width = Math.max(width, mLabelPaint.measureText("FPS"));
        if (mContext != null) width = Math.max(width, mLabelPaint.measureText(mContext));
        int w = Math.round(width) + mPadH * 2;
        int h = Math.round(mValuePaint.getTextSize() + mDetailPaint.getTextSize()
                + mLabelPaint.getTextSize()) + mPadV * 2 + Math.round(2 * getResources().getDisplayMetrics().density);
        if (mContext != null) h += Math.round(mLabelPaint.getTextSize() * 1.3f);
        setMeasuredDimension(w, h);
    }

    @Override protected void onDraw(Canvas canvas) {
        float radius = 14f * getResources().getDisplayMetrics().density;
        mBounds.set(0f, 0f, getWidth(), getHeight());
        canvas.drawRoundRect(mBounds, radius, radius, mBackgroundPaint);

        boolean stale = mLastRecordAt > 0L && System.currentTimeMillis() - mLastRecordAt > STALE_MS;
        if (stale) mValuePaint.setColor(Color.parseColor("#FFC46B"));
        else mValuePaint.setColor(Color.parseColor("#EAFCFF"));

        float x = mPadH;
        float y = mPadV + mLabelPaint.getTextSize();
        canvas.drawText("FPS", x, y, mLabelPaint);

        String value = mWaiting ? "--" : String.valueOf(mFps);
        y += mValuePaint.getTextSize();
        canvas.drawText(value, x, y, mValuePaint);

        String detail = mWaiting
                ? "measuring"
                : (stale ? "stalled" : String.format(Locale.ROOT, "%d ms", mFrameMillis));
        y += mDetailPaint.getTextSize() + 1f;
        canvas.drawText(detail, x, y, mDetailPaint);

        if (mContext != null) {
            y += mLabelPaint.getTextSize() * 1.25f;
            canvas.drawText(mContext, x, y, mLabelPaint);
        }
    }

    @Override protected void onLayout(boolean changed, int l, int t, int r, int b) {
        super.onLayout(changed, l, t, r, b);
        if (!changed || !(getTag() instanceof float[])) return;
        float[] fraction = (float[]) getTag();
        View parent = (View) getParent();
        if (parent == null) return;
        int pw = parent.getWidth();
        int ph = parent.getHeight();
        if (pw <= 0 || ph <= 0) return;
        int left = Math.round(fraction[0] * pw);
        int top = Math.round(fraction[1] * ph);
        left = Math.max(0, Math.min(left, pw - getWidth()));
        top = Math.max(0, Math.min(top, ph - getHeight()));
        setX(left);
        setY(top);
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                mDownX = event.getRawX();
                mDownY = event.getRawY();
                mStartX = getX();
                mStartY = getY();
                mDragging = false;
                return true;
            case MotionEvent.ACTION_MOVE: {
                float dx = event.getRawX() - mDownX;
                float dy = event.getRawY() - mDownY;
                if (!mDragging && Math.hypot(dx, dy) > mTouchSlop) mDragging = true;
                if (!mDragging) return true;
                View parent = (View) getParent();
                if (parent == null) return true;
                float nx = clamp(mStartX + dx, 0f, parent.getWidth() - getWidth());
                float ny = clamp(mStartY + dy, 0f, parent.getHeight() - getHeight());
                setX(nx);
                setY(ny);
                return true;
            }
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL: {
                View parent = (View) getParent();
                if (mDragging && parent != null && parent.getWidth() > 0 && parent.getHeight() > 0) {
                    float fx = getX() / parent.getWidth();
                    float fy = getY() / parent.getHeight();
                    setTag(new float[]{fx, fy});
                    SharedPreferences pref = LauncherPreferences.DEFAULT_PREF;
                    if (pref != null) {
                        pref.edit().putFloat(PREF_X, fx).putFloat(PREF_Y, fy).apply();
                    }
                }
                mDragging = false;
                return true;
            }
            default:
                return super.onTouchEvent(event);
        }
    }

    private static float clamp(float value, float min, float max) {
        if (max < min) return min;
        return Math.max(min, Math.min(value, max));
    }
}
