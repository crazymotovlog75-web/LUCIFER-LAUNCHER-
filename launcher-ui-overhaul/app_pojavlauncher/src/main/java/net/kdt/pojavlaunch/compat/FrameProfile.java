package net.kdt.pojavlaunch.compat;

import android.content.SharedPreferences;
import android.util.Log;

import net.kdt.pojavlaunch.prefs.LauncherPreferences;
import net.kdt.pojavlaunch.value.launcherprofiles.LauncherProfiles;
import net.kdt.pojavlaunch.value.launcherprofiles.MinecraftProfile;

import java.util.Map;

/**
 * The 1.21+ FPS pack.
 *
 * <p>Minecraft 1.21 and newer do far more work per frame than the versions this hardware was built
 * for, which is why the same phone that runs 1.8.9 comfortably sits around 30 FPS on 1.21.11. The
 * pack targets exactly that gap with two structural levers instead of cosmetic guessing:
 *
 * <ol>
 *     <li><b>Zero-copy surface.</b> The engine only picks {@code SurfaceView} on "powerful" devices
 *     (over 4 GB RAM, 1080p, ...). On a 720p phone that silently leaves {@code TextureView}, which
 *     costs a full-screen GPU blit <em>every frame</em> — and is also the path that draws black
 *     geometry with the new pipeline. For 1.21+ the SurfaceView path is forced on.</li>
 *     <li><b>A moderate video profile</b> ({@link VersionTuning#modernFpsOptions(Map)}): clouds,
 *     entity shadows, fancy leaves, biome blend, view-bob nausea, portal distortion and excessive
 *     particles off; render/simulation distance lowered but never below what you already had.</li>
 * </ol>
 *
 * <p>Resolution, CPU affinity, clock modes, heap size and JVM flags are deliberately <b>not</b>
 * touched: those are the knobs that made the earlier "performance mode" slower than the defaults.
 * Everything here is reversible — the video changes go through the engine's snapshot/restore path,
 * and the switch in Video &amp; Graphics turns the whole pack off again.
 */
public final class FrameProfile {
    private static final String TAG = "FrameProfile";

    /** Preference: the user wants the 1.21+ pack (default on). */
    public static final String KEY_ENABLED = "modernFpsPack";

    private FrameProfile() { }

    private static SharedPreferences prefs() {
        return LauncherPreferences.DEFAULT_PREF;
    }

    /**
     * @return true when this version is 1.21 or newer, i.e. the pack has something to do. Broader
     *         than {@link MinecraftCompat#requiresModernGl(String)} on purpose: 1.21 - 1.21.10 are
     *         not black-screened, but they are just as slow.
     */
    public static boolean isTargetVersion(String versionId) {
        VersionEra era = VersionEra.of(versionId);
        return era == VersionEra.MODERN_21 || era == VersionEra.NEW_PIPELINE;
    }

    /** @return true when the pack is switched on by the user (default: on). */
    public static boolean isEnabled() {
        SharedPreferences pref = prefs();
        return pref == null || pref.getBoolean(KEY_ENABLED, true);
    }

    /** @return true when the pack should act on {@code versionId} right now. */
    public static boolean isActive(String versionId) {
        return isTargetVersion(versionId) && isEnabled();
    }

    public static void setEnabled(boolean enabled) {
        SharedPreferences pref = prefs();
        if (pref == null) return;
        pref.edit().putBoolean(KEY_ENABLED, enabled).apply();
        sync();
    }

    /** Applies the pack to the current instance; safe to call on every launch. */
    public static void sync() {
        sync(currentVersionId());
    }

    /**
     * Applies the pack to one instance.
     *
     * @return a short description of what changed, or {@code null} if nothing needed changing
     */
    public static String sync(String versionId) {
        if (!isActive(versionId)) return null;

        boolean changed = false;

        // 1.21.11+ only: the MobileGlues wrapper needs the safest multidraw path and a shader cache
        // big enough to keep the new pipeline from recompiling mid-frame. The values are applied in
        // LauncherPreferences.writeMGRendererSettings(), so the user's prefs stay untouched.
        if (VersionEra.of(versionId) == VersionEra.NEW_PIPELINE) {
            changed = writeMobileGluesConfig();
        }

        Log.i(TAG, "1.21+ pack synced for " + versionId + " (configWritten=" + changed + ")");
        return changed ? "1.21+ FPS pack" : null;
    }

    private static boolean writeMobileGluesConfig() {
        try {
            LauncherPreferences.writeMGRendererSettings();
            return true;
        } catch (Throwable e) {
            Log.w(TAG, "Could not write the MobileGlues config", e);
            return false;
        }
    }

    /** @return the version of the selected instance, or {@code null} when none can be read. */
    public static String currentVersionId() {
        try {
            MinecraftProfile profile = LauncherProfiles.getCurrentProfile();
            if (profile != null && profile.lastVersionId != null && !profile.lastVersionId.isEmpty()) {
                return profile.lastVersionId;
            }
        } catch (Throwable ignored) {
            // fall through: treat as "no instance"
        }
        return null;
    }

    /** Short HUD label. */
    public static String statusLabel() {
        String versionId = currentVersionId();
        if (!isTargetVersion(versionId)) return "GAME READY";
        return isEnabled() ? "1.21 PACK ON" : "PACK OFF";
    }

    /** Explanation shown in Video &amp; Graphics. */
    public static String summary() {
        return "1.21+ versions: zero-copy SurfaceView, clouds/entity shadows/fancy leaves off, "
                + "render 6 / simulation 5 chunks, unlimited FPS. Resolution aur CPU settings "
                + "chhui nahi jati.";
    }

    /** The video profile for this instance, given its current options. */
    public static Map<String, String> optionsFor(Map<String, String> current) {
        return VersionTuning.modernFpsOptions(current);
    }

    /**
     * @return true when the MobileGlues config must use the compatibility-oriented values
     *         (1.21.11 and newer draw through the new pipeline, which the wrapper only handles
     *         correctly when multidraw is fully emulated).
     */
    public static boolean needsWrapperCompat() {
        return isTargetVersion(currentVersionId()) && isEnabled();
    }

    /** Kept for callers that only have an era at hand. */
    public static boolean isTargetEra(VersionEra era) {
        return era == VersionEra.MODERN_21 || era == VersionEra.NEW_PIPELINE;
    }
}
