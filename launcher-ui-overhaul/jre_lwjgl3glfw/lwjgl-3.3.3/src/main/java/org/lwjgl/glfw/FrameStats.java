package org.lwjgl.glfw;

import java.io.File;
import java.io.RandomAccessFile;
import java.nio.charset.StandardCharsets;

/**
 * Real frame accounting for the in-game FPS overlay.
 *
 * <p>This class is fed by {@link GLFW#glfwSwapBuffers(long)}, which the game calls exactly once per
 * presented frame. That means the number it reports is not an estimate, not a smoothed guess and not
 * a target: it is the number of buffers the game actually swapped inside the last measurement
 * window.
 *
 * <p>The overlay lives in the Android process, this class lives in the game's JVM class loader, so
 * the two cannot share a static field. They talk through a tiny file instead
 * ({@code -Dlucifer.fps.file=...}): a fixed-width record is written twice per second into a temp
 * file and then atomically renamed over the real one, so the reader can never observe a half-written
 * line.
 *
 * <p>Cost per frame is two integer increments. The file write happens once every
 * {@link #WINDOW_NS} and is a few dozen bytes, so it cannot influence the frame rate it measures.
 */
public final class FrameStats {

    /** Refresh window. 500 ms keeps the readout responsive without averaging the lag away. */
    private static final long WINDOW_NS = 500_000_000L;

    private static volatile long sFrames;          // frames in the current window
    private static volatile long sWindowStart;     // System.nanoTime() of window start
    private static volatile int sLastFps;          // last completed window, real value
    private static volatile int sLastFrameMillis;  // last completed window, average frame time
    private static volatile long sTotalFrames;     // since process start
    private static volatile long sTotalNanos;      // since process start, for the lifetime average

    private static volatile String sFpsPath;       // null = writer disabled
    private static volatile boolean sPathResolved;
    private static volatile boolean sBroken;       // IO failed once; stop retrying

    private FrameStats() { }

    /**
     * Called from {@code glfwSwapBuffers} on the game's render thread. Two increments in the common
     * case; the measurement/write only happens when the window closes.
     */
    public static void onSwap() {
        if (sBroken) return;
        long now = System.nanoTime();
        long start = sWindowStart;
        if (start == 0L) {
            sWindowStart = now;
            start = now;
        }
        sFrames++;
        long elapsed = now - start;
        if (elapsed >= WINDOW_NS) publish(now, elapsed);
    }

    private static void publish(long now, long elapsedNanos) {
        long frames = sFrames;
        sFrames = 0L;
        sWindowStart = now;
        sTotalFrames += frames;
        sTotalNanos += elapsedNanos;

        // Integer maths on purpose: frames*1e9/elapsed is the exact measured rate, no float tricks.
        int fps = (int) ((frames * 1_000_000_000L) / Math.max(1L, elapsedNanos));
        int frameMillis = frames > 0 ? (int) ((elapsedNanos / 1_000_000L) / frames) : 0;
        sLastFps = fps;
        sLastFrameMillis = frameMillis;

        String path = fpsPath();
        if (path == null) return;
        writeRecord(path, fps, frameMillis, frames, sTotalFrames);
    }

    /** @return frames swapped per second in the last completed window, or 0 before the first one. */
    public static int getFps() {
        return sLastFps;
    }

    /** @return average frame time in milliseconds of the last completed window. */
    public static int getFrameMillis() {
        return sLastFrameMillis;
    }

    /** @return frames presented since the game started. */
    public static long getTotalFrames() {
        return sTotalFrames;
    }

    private static String fpsPath() {
        if (!sPathResolved) {
            String path = null;
            try {
                path = System.getProperty("lucifer.fps.file");
            } catch (Throwable ignored) {
                // a security manager or a stripped property table: stay silent
            }
            sFpsPath = path;
            sPathResolved = true;
        }
        return sFpsPath;
    }

    private static void writeRecord(String path, int fps, int frameMillis, long windowFrames,
                                    long totalFrames) {
        try {
            File target = new File(path);
            File parent = target.getParentFile();
            if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
                sBroken = true;
                return;
            }
            String line = String.format(java.util.Locale.ROOT, "%-6d %-5d %-6d %-10d%n",
                    fps, frameMillis, windowFrames, totalFrames);
            byte[] bytes = line.getBytes(StandardCharsets.US_ASCII);
            File temp = new File(target.getPath() + ".tmp");
            RandomAccessFile raf = new RandomAccessFile(temp, "rw");
            try {
                raf.setLength(0L);
                raf.write(bytes);
            } finally {
                raf.close();
            }
            if (!temp.renameTo(target)) {
                // Filesystems that refuse rename-over write in place; the reader retries on a bad line.
                RandomAccessFile direct = new RandomAccessFile(target, "rw");
                try {
                    direct.setLength(0L);
                    direct.write(bytes);
                } finally {
                    direct.close();
                }
                if (!temp.delete()) temp.deleteOnExit();
            }
        } catch (Throwable e) {
            // Never let telemetry break the game: one failure disables the writer for this session.
            sBroken = true;
        }
    }
}
