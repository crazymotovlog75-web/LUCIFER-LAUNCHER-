package net.kdt.pojavlaunch.performance;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

/** Plain JVM tests for the Performance Mode numbers and JVM-argument handling. */
public class PerformanceBudgetTest {

    @Test
    public void heapFloorScalesWithDeviceRam() {
        assertEquals(1024, PerformanceBudget.recommendedRamMbForTotal(2048));
        assertEquals(1536, PerformanceBudget.recommendedRamMbForTotal(4096));
        assertEquals(2560, PerformanceBudget.recommendedRamMbForTotal(6144));
        assertEquals(3072, PerformanceBudget.recommendedRamMbForTotal(8192));
        assertEquals(4096, PerformanceBudget.recommendedRamMbForTotal(16384));
    }

    @Test
    public void unknownRamStillGetsAWorkableHeap() {
        assertEquals(2048, PerformanceBudget.recommendedRamMbForTotal(0));
        assertEquals(2048, PerformanceBudget.recommendedRamMbForTotal(-1));
    }

    @Test
    public void heapFloorIsMonotonic() {
        int previous = 0;
        for (long ram = 1024; ram <= 16384; ram += 512) {
            int current = PerformanceBudget.recommendedRamMbForTotal(ram);
            assertTrue("heap must not shrink as RAM grows (" + ram + " MB)", current >= previous);
            previous = current;
        }
    }

    @Test
    public void addingPerfFlagsKeepsUserArguments() {
        String updated = PerformanceBudget.addPerfFlags("-XX:+UseG1GC -Xss1M");
        assertTrue(updated.startsWith("-XX:+UseG1GC -Xss1M"));
        assertTrue(updated.contains("-XX:+DisableExplicitGC"));
        assertTrue(updated.contains("-XX:MaxGCPauseMillis=20"));
    }

    @Test
    public void addingPerfFlagsTwiceDoesNotDuplicateThem() {
        String once = PerformanceBudget.addPerfFlags("");
        String twice = PerformanceBudget.addPerfFlags(once);
        assertEquals(once, twice);
    }

    @Test
    public void removingPerfFlagsRestoresTheUserArguments() {
        String user = "-Xss1M";
        assertEquals(user, PerformanceBudget.removePerfFlags(PerformanceBudget.addPerfFlags(user)));
    }

    @Test
    public void trackedRemovalKeepsACollectorTheUserWrote() {
        String user = "-XX:+UseSerialGC -Xss1M";
        String[] added = PerformanceBudget.flagsToAdd(user);
        String withProfile = PerformanceBudget.applyFlags(user, added);
        assertEquals(user, PerformanceBudget.removeFlags(withProfile, added));
    }

    @Test
    public void untrackedRemovalStillKeepsTheUsersCollector() {
        String user = "-XX:+UseSerialGC";
        String withProfile = PerformanceBudget.applyFlags(user, PerformanceBudget.PERF_JVM_FLAGS);
        String cleaned = PerformanceBudget.removeFlags(withProfile,
                PerformanceBudget.flagsToRemoveWithoutUserCollector(withProfile));
        assertTrue(cleaned.contains("-XX:+UseSerialGC"));
        assertFalse(cleaned.contains("-XX:+DisableExplicitGC"));
    }

    @Test
    public void aUserChosenCollectorIsNeverOverridden() {
        String serial = PerformanceBudget.addPerfFlags("-XX:+UseSerialGC");
        assertTrue("user collector must stay", serial.contains("-XX:+UseSerialGC"));
        assertFalse("second collector must not be added", serial.contains("-XX:+UseG1GC"));
        assertTrue("the rest of the profile still applies", serial.contains("-XX:+DisableExplicitGC"));
    }

    @Test
    public void removeIsSafeWithNoFlagsPresent() {
        assertEquals("-Xss2M", PerformanceBudget.removePerfFlags("  -Xss2M  "));
        assertEquals("", PerformanceBudget.removePerfFlags(null));
        assertFalse(PerformanceBudget.addPerfFlags(null).isEmpty());
    }
}
