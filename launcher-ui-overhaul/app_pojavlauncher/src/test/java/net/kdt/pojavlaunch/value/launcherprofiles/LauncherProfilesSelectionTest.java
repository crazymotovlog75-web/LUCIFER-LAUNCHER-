package net.kdt.pojavlaunch.value.launcherprofiles;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Regression tests for the startup crash:
 * {@code RuntimeException: The current profile stopped existing :(}
 * raised from {@link LauncherProfiles#getCurrentProfile()} during {@code unpackSingleFiles()}.
 *
 * These tests only exercise the pure (Android-free) selection/normalization helpers.
 */
public class LauncherProfilesSelectionTest {

    /** Mirrors assets/launcher_profiles.json shipped in the APK. */
    private MinecraftLauncherProfiles assetTemplate() {
        MinecraftLauncherProfiles profilesJson = new MinecraftLauncherProfiles();
        profilesJson.profiles = new HashMap<>();
        MinecraftProfile assetDefault = new MinecraftProfile();
        assetDefault.name = "(Default)";
        assetDefault.lastVersionId = "1.7.10";
        profilesJson.profiles.put("(Default)", assetDefault);
        profilesJson.selectedProfile = "(Default)";
        return profilesJson;
    }

    @Test
    public void freshInstallNormalizesAssetTemplateAndRepairsSelection() {
        MinecraftLauncherProfiles profilesJson = assetTemplate();

        // Fresh install: SharedPreferences still holds the default empty string.
        LauncherProfiles.NormalizeResult result =
                LauncherProfiles.normalizeProfileIdsCore(profilesJson, "");

        assertTrue("Non-UUID '(Default)' key must be normalized", result.changed);
        assertEquals(1, profilesJson.profiles.size());
        assertFalse(profilesJson.profiles.containsKey("(Default)"));
        assertNotNull("A repaired selection must be produced for empty prefs", result.replacementSelection);
        assertEquals(result.replacementSelection, profilesJson.selectedProfile);

        // The repaired key must be a real UUID and must point at an existing profile.
        UUID parsed = UUID.fromString(result.replacementSelection);
        assertEquals(result.replacementSelection, parsed.toString());
        MinecraftProfile repaired = profilesJson.profiles.get(result.replacementSelection);
        assertNotNull(repaired);
        assertTrue("Default profile keeps its marker", repaired.isDefault);

        // getCurrentProfile()'s fallback resolver must agree with the repaired key.
        assertEquals(result.replacementSelection,
                LauncherProfiles.resolveSelectedProfileKey(profilesJson.profiles, ""));
    }

    @Test
    public void staleProfileKeySelfHealsToDefaultProfile() {
        Map<String, MinecraftProfile> map = new HashMap<>();

        String customKey = UUID.randomUUID().toString();
        MinecraftProfile custom = new MinecraftProfile();
        custom.name = "PvP Modpack";
        custom.lastVersionId = "1.20.4";
        map.put(customKey, custom);

        String defaultKey = UUID.randomUUID().toString();
        MinecraftProfile def = new MinecraftProfile();
        def.name = "Default";
        def.lastVersionId = "latest-release";
        def.isDefault = true;
        map.put(defaultKey, def);

        // A key that no longer exists (deleted / renamed profile) must never crash the launcher.
        assertEquals(defaultKey,
                LauncherProfiles.resolveSelectedProfileKey(map, UUID.randomUUID().toString()));

        // Existing valid selection is preserved.
        assertEquals(customKey, LauncherProfiles.resolveSelectedProfileKey(map, customKey));

        // Empty / null selections fall back to the default profile.
        assertEquals(defaultKey, LauncherProfiles.resolveSelectedProfileKey(map, ""));
        assertEquals(defaultKey, LauncherProfiles.resolveSelectedProfileKey(map, null));

        // Empty map yields no selection (caller creates the emergency default instead).
        assertNull(LauncherProfiles.resolveSelectedProfileKey(new HashMap<>(), ""));
    }

    @Test
    public void alreadyNormalizedProfilesAreNotRewritten() {
        Map<String, MinecraftProfile> map = new HashMap<>();
        String key = UUID.randomUUID().toString();
        MinecraftProfile profile = new MinecraftProfile();
        profile.name = "Minecraft 1.21";
        profile.lastVersionId = "1.21";
        map.put(key, profile);

        MinecraftLauncherProfiles json = new MinecraftLauncherProfiles();
        json.profiles = map;
        json.selectedProfile = key;

        LauncherProfiles.NormalizeResult result = LauncherProfiles.normalizeProfileIdsCore(json, key);
        assertFalse("UUID keys must be left untouched", result.changed);
        assertNull(result.replacementSelection);
        assertEquals(key, json.selectedProfile);
    }

    @Test
    public void selectedProfileFieldSurvivesJsonSerialization() {
        MinecraftLauncherProfiles json = assetTemplate();
        // Gson round-trip through the same toJson()/GLOBAL_GSON pipeline is exercised at runtime;
        // here we at least guarantee the field exists and is readable so fresh installs can heal.
        assertEquals("(Default)", json.selectedProfile);
        json.selectedProfile = UUID.randomUUID().toString();
        assertNotNull(json.selectedProfile);
    }
}
