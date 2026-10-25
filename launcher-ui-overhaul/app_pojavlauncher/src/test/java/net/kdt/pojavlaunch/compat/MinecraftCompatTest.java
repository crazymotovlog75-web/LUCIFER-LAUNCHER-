package net.kdt.pojavlaunch.compat;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.util.Arrays;
import java.util.Collections;

/** Version rules for the 1.21.11+ render pipeline (the black-screen profile). */
public class MinecraftCompatTest {

    @Test
    public void parsesPlainAndLoaderVersionIds() {
        assertArrayEquals(new int[]{1, 21, 11}, MinecraftCompat.parseVersion("1.21.11"));
        assertArrayEquals(new int[]{1, 21, 10}, MinecraftCompat.parseVersion("1.21.10"));
        // Loader versions (0.x) must be skipped, the Minecraft version comes last.
        assertArrayEquals(new int[]{1, 21, 11},
                MinecraftCompat.parseVersion("fabric-loader-0.16.9-1.21.11"));
        assertArrayEquals(new int[]{1, 21, 10},
                MinecraftCompat.parseVersion("forge-1.21.10-52.0.12"));
        assertArrayEquals(new int[]{1, 21, 11}, MinecraftCompat.parseVersion("1.21.11-pre2"));
    }

    @Test
    public void snapshotsAndJunkDoNotLookLikeModernReleases() {
        assertNull(MinecraftCompat.parseVersion("25w31a"));
        assertNull(MinecraftCompat.parseVersion(""));
        assertNull(MinecraftCompat.parseVersion(null));
        assertFalse(MinecraftCompat.requiresModernGl("25w31a"));
    }

    @Test
    public void modernPipelineStartsAtOneTwentyOneEleven() {
        assertFalse(MinecraftCompat.requiresModernGl("1.21.10"));
        assertFalse(MinecraftCompat.requiresModernGl("1.21.9"));
        assertFalse(MinecraftCompat.requiresModernGl("1.20.1"));
        assertTrue(MinecraftCompat.requiresModernGl("1.21.11"));
        assertTrue(MinecraftCompat.requiresModernGl("1.21.12"));
        assertTrue(MinecraftCompat.requiresModernGl("1.22"));
        assertTrue(MinecraftCompat.requiresModernGl("1.22.1"));
        // Modded instances inherit the same rule.
        assertTrue(MinecraftCompat.requiresModernGl("fabric-loader-0.16.9-1.21.11"));
    }

    @Test
    public void gl4esIsNotGoodEnoughForTheModernPipeline() {
        assertFalse(MinecraftCompat.isModernCapable("opengles2"));
        assertFalse(MinecraftCompat.isModernCapable(null));
        assertFalse(MinecraftCompat.isModernCapable(""));
        assertTrue(MinecraftCompat.isModernCapable("opengles3_desktopgl_zink"));
        assertTrue(MinecraftCompat.isModernCapable("opengles_mobileglues"));
        assertTrue(MinecraftCompat.isModernCapable("opengles3_ltw"));
        assertTrue(MinecraftCompat.isModernCapable("opengles3_KW"));
    }

    @Test
    public void rendererIsSwappedOnlyWhenTheDeviceCanRunTheReplacement() {
        assertEquals(MinecraftCompat.RENDERER_ZINK, MinecraftCompat.pickModernRenderer(
                "opengles2",
                Arrays.asList("opengles2", "opengles3_desktopgl_zink", "opengles3_ltw")));
        assertEquals(MinecraftCompat.RENDERER_MOBILEGLUES, MinecraftCompat.pickModernRenderer(
                "opengles2", Arrays.asList("opengles2", "opengles_mobileglues")));
        assertNull("nothing compatible means keep what works",
                MinecraftCompat.pickModernRenderer("opengles2",
                        Collections.singletonList("opengles2")));
        assertNull("an already capable renderer is left alone",
                MinecraftCompat.pickModernRenderer("opengles3_desktopgl_zink",
                        Arrays.asList("opengles2", "opengles3_desktopgl_zink")));
    }

    @Test
    public void modernInstancesPreferTheZeroCopySurface() {
        assertTrue(MinecraftCompat.prefersSurfaceView("1.21.11"));
        assertFalse(MinecraftCompat.prefersSurfaceView("1.21.10"));
    }
}
