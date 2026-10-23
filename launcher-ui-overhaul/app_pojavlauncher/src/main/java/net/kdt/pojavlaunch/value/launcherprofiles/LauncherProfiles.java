package net.kdt.pojavlaunch.value.launcherprofiles;

import android.util.Log;

import androidx.annotation.NonNull;

import net.kdt.pojavlaunch.Tools;
import net.kdt.pojavlaunch.instances.InstanceManager;
import net.kdt.pojavlaunch.instances.InstancePathResolver;
import net.kdt.pojavlaunch.prefs.LauncherPreferences;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

public class LauncherProfiles {
    public static volatile MinecraftLauncherProfiles mainProfileJson;

    public static final java.util.List<Runnable> sProfileUpdateListeners = new CopyOnWriteArrayList<>();

    private static File getLauncherProfilesFile() {
        return new File(Tools.DIR_GAME_NEW, "launcher_profiles.json");
    }

    public static void addUpdateListener(Runnable listener) {
        if (!sProfileUpdateListeners.contains(listener)) {
            sProfileUpdateListeners.add(listener);
        }
    }

    public static void removeUpdateListener(Runnable listener) {
        sProfileUpdateListeners.remove(listener);
    }

    /** Reload the profile from the file, creating a default one if necessary.
     *  Does NOT auto-scan version directories — that only happens on explicit
     *  {@link #rescanProfiles()} calls, to prevent deleted profiles from
     *  being recreated behind the user's back. */
    public static synchronized void load(){
        File launcherProfilesFile = getLauncherProfilesFile();
        MinecraftLauncherProfiles loaded = null;
        if (launcherProfilesFile.exists()) {
            try {
                loaded = Tools.GLOBAL_GSON.fromJson(Tools.read(launcherProfilesFile.getAbsolutePath()), MinecraftLauncherProfiles.class);
            } catch (Throwable e) {
                Log.e(LauncherProfiles.class.toString(), "Failed to load launcher_profiles.json, falling back to default: ", e);
            }
        }

        // Fill with default and wrap map in ConcurrentHashMap so UI reads never CME
        if (loaded == null) loaded = new MinecraftLauncherProfiles();
        ConcurrentHashMap<String, MinecraftProfile> safeProfiles = new ConcurrentHashMap<>();
        if (loaded.profiles != null) {
            for (Map.Entry<String, MinecraftProfile> entry : loaded.profiles.entrySet()) {
                if (entry.getKey() != null && entry.getValue() != null) {
                    safeProfiles.put(entry.getKey(), entry.getValue());
                }
            }
        }
        loaded.profiles = safeProfiles;
        mainProfileJson = loaded;

        boolean dirty = purgeInvalidProfiles();

        if (mainProfileJson.profiles.isEmpty()) {
            MinecraftProfile defaultProfile = MinecraftProfile.getDefaultProfile();
            defaultProfile.isDefault = true;
            String defaultKey = UUID.randomUUID().toString();
            mainProfileJson.profiles.put(defaultKey, defaultProfile);
            mainProfileJson.selectedProfile = defaultKey;
            dirty = true;
        }

        // Normalize non-UUID profile keys (e.g. "(Default)" from assets/launcher_profiles.json) BEFORE migration
        if (normalizeProfileIds(mainProfileJson)) {
            dirty = true;
        }

        // Preserve a stable marker for the original profile
        if (markDefaultProfileIfNeeded()) {
            dirty = true;
        }

        // Migrate legacy profiles using copy-only semantics. Their old directories remain intact.
        if (migrateLegacyProfiles()) {
            dirty = true;
        }

        // Self-heal PREF_KEY_CURRENT_PROFILE and selectedProfile so fresh installs never point to ""
        if (ensureSelectedProfileKey()) {
            dirty = true;
        }

        if (dirty) {
            persistSilently(launcherProfilesFile);
        }

        // Notify listeners when profiles are reloaded
        notifyUpdateListeners();
    }

    private static void persistSilently(File launcherProfilesFile) {
        if (mainProfileJson == null) return;
        try {
            File parent = launcherProfilesFile.getParentFile();
            if (parent != null && !parent.exists()) {
                //noinspection ResultOfMethodCallIgnored
                parent.mkdirs();
            }
            Tools.write(launcherProfilesFile.getAbsolutePath(), mainProfileJson.toJson());
        } catch (Throwable e) {
            Log.e(LauncherProfiles.class.toString(), "Failed to persist migrated profile metadata", e);
        }
    }

    private static void notifyUpdateListeners() {
        for (Runnable listener : new java.util.ArrayList<>(sProfileUpdateListeners)) {
            if (listener != null) Tools.runOnUiThread(listener);
        }
    }

    private static boolean migrateLegacyProfiles() {
        if (mainProfileJson == null || mainProfileJson.profiles == null) return false;
        InstanceManager manager = Tools.getInstanceManager();
        InstancePathResolver paths = manager.paths();
        boolean changed = false;
        for (Map.Entry<String, MinecraftProfile> entry : mainProfileJson.profiles.entrySet()) {
            MinecraftProfile profile = entry.getValue();
            if (profile == null) continue;
            String originalGameDir = profile.gameDir;
            String instanceId = profile.instanceId;
            if (instanceId == null || instanceId.trim().isEmpty()) {
                instanceId = InstancePathResolver.instanceIdForProfileKey(entry.getKey());
                File legacySource = paths.resolveLegacyGameDirectory(originalGameDir);
                try {
                    manager.importLegacyInstance(instanceId, entry.getKey(), profile.name,
                            profile.lastVersionId, legacySource);
                    profile.instanceId = instanceId;
                    if (originalGameDir != null && originalGameDir.contains("custom_instances/")) {
                        profile.legacySourcePath = originalGameDir;
                    }
                    profile.gameDir = InstancePathResolver.gameDirectoryValue(instanceId);
                    changed = true;
                    Log.i("LauncherProfiles", "Copied legacy profile '" + profile.name +
                            "' into isolated instance " + instanceId + " (source retained)");
                } catch (IOException | IllegalArgumentException error) {
                    // Keep the old profile usable and retry the copy on a later load.
                    profile.instanceId = null;
                    profile.gameDir = originalGameDir;
                    Log.e("LauncherProfiles", "Could not migrate profile '" + profile.name +
                            "'; retaining its legacy game directory", error);
                }
            } else {
                try {
                    manager.initializeInstance(instanceId, entry.getKey(), profile.name, profile.lastVersionId);
                    manager.updateMetadata(instanceId, entry.getKey(), profile.name, profile.lastVersionId);
                    String canonicalGameDir = InstancePathResolver.gameDirectoryValue(instanceId);
                    if (!canonicalGameDir.equals(profile.gameDir)) {
                        profile.gameDir = canonicalGameDir;
                        changed = true;
                    }
                } catch (IOException | IllegalArgumentException error) {
                    Log.e("LauncherProfiles", "Could not initialize instance " + instanceId, error);
                }
            }
        }
        return changed;
    }

    private static boolean markDefaultProfileIfNeeded() {
        if (mainProfileJson == null || mainProfileJson.profiles == null) return false;
        for (MinecraftProfile profile : mainProfileJson.profiles.values()) {
            if (profile != null && profile.isDefault) return false;
        }

        Map.Entry<String, MinecraftProfile> candidate = null;
        for (Map.Entry<String, MinecraftProfile> entry : mainProfileJson.profiles.entrySet()) {
            MinecraftProfile profile = entry.getValue();
            if (profile != null && profile.name != null &&
                    ("Default".equalsIgnoreCase(profile.name.trim()) ||
                     "(Default)".equalsIgnoreCase(profile.name.trim()))) {
                candidate = entry;
                break;
            }
        }

        // Older builds allowed the default profile to be renamed. On first migration, the
        // selected profile is the best available signal for which existing entry was the original.
        if (candidate == null && LauncherPreferences.DEFAULT_PREF != null) {
            String selectedKey = LauncherPreferences.DEFAULT_PREF.getString(
                    LauncherPreferences.PREF_KEY_CURRENT_PROFILE, "");
            MinecraftProfile selected = mainProfileJson.profiles.get(selectedKey);
            if (selected != null) candidate = new java.util.AbstractMap.SimpleEntry<>(selectedKey, selected);
        }
        if (candidate == null && mainProfileJson.profiles.size() == 1) {
            Map.Entry<String, MinecraftProfile> onlyEntry = mainProfileJson.profiles.entrySet().iterator().next();
            if (onlyEntry.getValue() != null) candidate = onlyEntry;
        }
        if (candidate == null || candidate.getValue() == null) return false;
        candidate.getValue().isDefault = true;
        return true;
    }

    /**
     * Returns profiles in a stable display order: the original default first, followed by the
     * oldest-created instances. Legacy entries without creation timestamps remain ahead of newly
     * created entries and use name/key as deterministic tie breakers.
     */
    @NonNull
    public static synchronized List<Map.Entry<String, MinecraftProfile>> getProfilesInDisplayOrder() {
        ArrayList<Map.Entry<String, MinecraftProfile>> entries = new ArrayList<>();
        if (mainProfileJson == null || mainProfileJson.profiles == null) return entries;
        entries.addAll(mainProfileJson.profiles.entrySet());
        Collections.sort(entries, (left, right) -> {
            MinecraftProfile leftProfile = left.getValue();
            MinecraftProfile rightProfile = right.getValue();
            boolean leftDefault = isDefaultProfile(leftProfile);
            boolean rightDefault = isDefaultProfile(rightProfile);
            if (leftDefault != rightDefault) return leftDefault ? -1 : 1;

            String leftCreated = leftProfile != null && leftProfile.created != null
                    ? leftProfile.created : "";
            String rightCreated = rightProfile != null && rightProfile.created != null
                    ? rightProfile.created : "";
            int createdOrder;
            if (leftCreated.isEmpty() != rightCreated.isEmpty()) {
                createdOrder = leftCreated.isEmpty() ? -1 : 1;
            } else {
                createdOrder = leftCreated.compareTo(rightCreated);
            }
            if (createdOrder != 0) return createdOrder;

            String leftName = leftProfile != null && leftProfile.name != null
                    ? leftProfile.name : "";
            String rightName = rightProfile != null && rightProfile.name != null
                    ? rightProfile.name : "";
            int nameOrder = leftName.compareToIgnoreCase(rightName);
            if (nameOrder != 0) return nameOrder;
            String leftKey = left.getKey() != null ? left.getKey() : "";
            String rightKey = right.getKey() != null ? right.getKey() : "";
            return leftKey.compareTo(rightKey);
        });
        return entries;
    }

    public static boolean isDefaultProfile(@androidx.annotation.Nullable MinecraftProfile profile) {
        if (profile == null) return false;
        if (mainProfileJson != null && mainProfileJson.profiles != null) {
            for (MinecraftProfile candidate : mainProfileJson.profiles.values()) {
                if (candidate != null && candidate.isDefault) return profile.isDefault;
            }
        }
        return profile.name != null && "Default".equalsIgnoreCase(profile.name.trim());
    }

    /**
     * Remove profiles with null keys, null/empty names, or otherwise corrupted data.
     * This prevents ghost entries from showing up in the UI.
     * @return true if any profiles were removed
     */
    private static boolean purgeInvalidProfiles() {
        if (mainProfileJson == null || mainProfileJson.profiles == null) return false;
        java.util.ArrayList<String> invalidKeys = new java.util.ArrayList<>();
        for (java.util.Map.Entry<String, MinecraftProfile> entry : mainProfileJson.profiles.entrySet()) {
            String key = entry.getKey();
            MinecraftProfile profile = entry.getValue();
            if (key == null || key.isEmpty()) {
                invalidKeys.add(key);
                continue;
            }
            if (profile == null) {
                invalidKeys.add(key);
                continue;
            }
            if (profile.name == null || profile.name.trim().isEmpty()) {
                invalidKeys.add(key);
                continue;
            }
        }
        for (String k : invalidKeys) {
            mainProfileJson.profiles.remove(k);
        }
        if (!invalidKeys.isEmpty()) {
            Log.w("LauncherProfiles", "Purged " + invalidKeys.size() + " invalid profiles");
            return true;
        }
        return false;
    }

    /**
     * Explicitly re-scan version directories and custom instances, creating
     * profiles for any that don't have a matching entry yet.
     * Safe to call when the user explicitly asks to discover new versions.
     */
    public static synchronized void rescanProfiles() {
        if (mainProfileJson == null) {
            load();
            return;
        }
        // autoScanProfiles persists only when it actually discovers a new entry.
        autoScanProfiles();
    }

    /**
     * Load profiles on a background thread, then run the callback on the UI thread.
     * Use this instead of {@link #load()} when called from the UI thread to avoid
     * blocking on file I/O and version directory scanning.
     * @param onComplete Runnable to execute on the UI thread after loading completes. May be null.
     */
    public static void loadAsync(@androidx.annotation.Nullable Runnable onComplete) {
        net.kdt.pojavlaunch.PojavApplication.sExecutorService.execute(() -> {
            load();
            if (onComplete != null) {
                net.kdt.pojavlaunch.Tools.runOnUiThread(onComplete);
            }
        });
    }

    public static synchronized void autoScanProfiles() {
        if (mainProfileJson == null || mainProfileJson.profiles == null) return;
        boolean changed = false;

        // Helper: check if a version ID looks like a loader version (not a raw MC version)
        java.util.regex.Pattern loaderPattern = java.util.regex.Pattern.compile(
                "(?i)(fabric|forge|neoforge|quilt|optifine|liteloader)");

        // 1. Scan versions directory
        File versionsDir = new File(Tools.DIR_GAME_NEW, "versions");
        if (versionsDir.exists() && versionsDir.isDirectory()) {
            File[] files = versionsDir.listFiles(File::isDirectory);
            if (files != null) {
                for (File dir : files) {
                    String versionId = dir.getName();
                    if (!new File(dir, versionId + ".json").isFile()) continue;
                    String lower = versionId.toLowerCase();

                    // FABRIC/LOADER REWORK: Skip auto-creating profiles for loader versions.
                    // Fabric, Forge, NeoForge, Quilt, OptiFine etc. are loaders, not standalone
                    // game versions. They should already be handled by the installer which updates
                    // an existing profile. If there's no corresponding profile, check if any
                    // existing profile's resolved MC version matches.
                    boolean isLoaderVersion = loaderPattern.matcher(lower).find();

                    // Check if any profile already uses this lastVersionId
                    boolean exists = false;
                    for (MinecraftProfile p : mainProfileJson.profiles.values()) {
                        if (versionId.equals(p.lastVersionId)) {
                            exists = true;
                            break;
                        }
                    }

                    if (isLoaderVersion) {
                        // For loader versions, check if the underlying MC version already has a profile
                        String mcVersion = net.kdt.pojavlaunch.utils.ProfileDetection.extractMcFromVersionId(versionId);
                        boolean hasMcProfile = false;
                        if (mcVersion != null && !mcVersion.isEmpty()) {
                            for (MinecraftProfile p : mainProfileJson.profiles.values()) {
                                String resolved = net.kdt.pojavlaunch.utils.ProfileDetection.getMcVersion(p);
                                if (mcVersion.equals(resolved) || mcVersion.equals(p.lastVersionId)) {
                                    hasMcProfile = true;
                                    break;
                                }
                            }
                        }
                        if (hasMcProfile && !exists) {
                            // There's already a profile for this MC version, skip auto-creation
                            continue;
                        }
                    }

                    if (!exists) {
                        // Create a profile for this version
                        MinecraftProfile profile = new MinecraftProfile();
                        profile.lastVersionId = versionId;
                        long installedAt = dir.lastModified();
                        profile.created = installedAt > 0
                                ? MinecraftProfile.timestampFrom(installedAt)
                                : MinecraftProfile.currentTimestamp();

                        // BRANDING: Show clean "Minecraft X.Y.Z" names, never expose internal
                        // loader version strings like "fabric-loader-0.19.3-1.21.10" to users.
                        // Extract the MC version for a clean display name.
                        String mcVer = net.kdt.pojavlaunch.utils.ProfileDetection.extractMcFromVersionId(versionId);
                        if (mcVer == null || mcVer.isEmpty()) mcVer = versionId;

                        if (lower.contains("neoforge")) {
                            profile.name = "Minecraft " + mcVer + " (NeoForge)";
                            profile.icon = "Forge";
                            profile.type = "custom";
                        } else if (lower.contains("forge")) {
                            profile.name = "Minecraft " + mcVer + " (Forge)";
                            profile.icon = "Forge";
                            profile.type = "custom";
                        } else if (lower.contains("fabric")) {
                            profile.name = "Minecraft " + mcVer;
                            profile.icon = "Fabric";
                            profile.type = "custom";
                        } else if (lower.contains("optifine")) {
                            profile.name = "Minecraft " + mcVer + " (OptiFine)";
                            profile.icon = "OptiFine";
                            profile.type = "custom";
                        } else if (lower.contains("quilt")) {
                            profile.name = "Minecraft " + mcVer + " (Quilt)";
                            profile.icon = "Fabric";
                            profile.type = "custom";
                        } else if (lower.contains("liteloader")) {
                            profile.name = "Minecraft " + mcVer + " (LiteLoader)";
                            profile.icon = "Grass";
                            profile.type = "custom";
                        } else {
                            profile.name = "Minecraft " + mcVer;
                            profile.icon = "Grass";
                            profile.type = "custom";
                        }

                        String profileKey = getFreeProfileKey();
                        String instanceId = InstancePathResolver.instanceIdForProfileKey(profileKey);
                        profile.instanceId = instanceId;
                        profile.gameDir = InstancePathResolver.gameDirectoryValue(instanceId);
                        try {
                            InstanceManager manager = Tools.getInstanceManager();
                            manager.importLegacyInstance(instanceId, profileKey, profile.name,
                                    profile.lastVersionId, manager.paths().getLegacyMinecraftRoot());
                            mainProfileJson.profiles.put(profileKey, profile);
                            changed = true;
                        } catch (IOException | IllegalArgumentException error) {
                            Log.e("LauncherProfiles", "Could not import legacy version " + versionId, error);
                        }
                    }
                }
            }
        }

        // 2. Scan custom_instances directory
        File instancesDir = new File(Tools.DIR_GAME_NEW, "custom_instances");
        if (instancesDir.exists() && instancesDir.isDirectory()) {
            File[] files = instancesDir.listFiles(File::isDirectory);
            if (files != null) {
                for (File dir : files) {
                    String instName = dir.getName();
                    String relativePath = "./custom_instances/" + instName;
                    // Check if any profile uses this gameDir
                    boolean exists = false;
                    for (MinecraftProfile p : mainProfileJson.profiles.values()) {
                        if ((p.legacySourcePath != null && p.legacySourcePath.equals(relativePath)) ||
                                p.gameDir != null && (p.gameDir.equals(relativePath) || p.gameDir.toLowerCase().contains(instName.toLowerCase()))) {
                            exists = true;
                            break;
                        }
                    }
                    if (!exists) {
                        // Create profile for this custom instance
                        MinecraftProfile profile = new MinecraftProfile();
                        profile.legacySourcePath = relativePath;
                        profile.type = "modpack";
                        long installedAt = dir.lastModified();
                        profile.created = installedAt > 0
                                ? MinecraftProfile.timestampFrom(installedAt)
                                : MinecraftProfile.currentTimestamp();

                        profile.name = "Modpack " + instName;
                        profile.icon = "Grass";
                        profile.lastVersionId = findBestVersionForInstance(null);

                        String profileKey = getFreeProfileKey();
                        String instanceId = InstancePathResolver.instanceIdForProfileKey(profileKey);
                        profile.instanceId = instanceId;
                        profile.gameDir = InstancePathResolver.gameDirectoryValue(instanceId);
                        try {
                            Tools.getInstanceManager().importLegacyInstance(instanceId, profileKey,
                                    profile.name, profile.lastVersionId, dir);
                            mainProfileJson.profiles.put(profileKey, profile);
                            changed = true;
                        } catch (IOException | IllegalArgumentException error) {
                            Log.e("LauncherProfiles", "Could not copy legacy custom instance " + instName, error);
                        }
                    }
                }
            }
        }

        // GUI installers such as Forge may add their version JSON under the currently selected
        // managed instance. Turn any newly discovered loader into a separate isolated profile.
        InstanceManager instanceManager = Tools.getInstanceManager();
        for (File sourceInstance : instanceManager.listManagedInstances()) {
            File versions = new File(sourceInstance, "versions");
            File[] installed = versions.listFiles(File::isDirectory);
            if (installed == null) continue;
            for (File directory : installed) {
                String versionId = directory.getName();
                if (!new File(directory, versionId + ".json").isFile() ||
                        !loaderPattern.matcher(versionId).find()) continue;
                boolean alreadyProfiled = false;
                for (MinecraftProfile profile : mainProfileJson.profiles.values()) {
                    if (profile != null && versionId.equals(profile.lastVersionId)) {
                        alreadyProfiled = true;
                        break;
                    }
                }
                if (alreadyProfiled) continue;

                String mcVersion = net.kdt.pojavlaunch.utils.ProfileDetection
                        .extractMcFromVersionId(versionId);
                if (mcVersion == null || mcVersion.isEmpty()) mcVersion = versionId;
                String lower = versionId.toLowerCase(java.util.Locale.ROOT);
                MinecraftProfile profile = new MinecraftProfile();
                profile.lastVersionId = versionId;
                profile.name = "Minecraft " + mcVersion + (lower.contains("neoforge") ? " (NeoForge)"
                        : lower.contains("forge") ? " (Forge)"
                        : lower.contains("optifine") ? " (OptiFine)" : "");
                profile.icon = lower.contains("forge") ? "Forge"
                        : lower.contains("optifine") ? "OptiFine" : "Fabric";
                profile.type = "custom";
                long installedAt = directory.lastModified();
                profile.created = installedAt > 0 ? MinecraftProfile.timestampFrom(installedAt)
                        : MinecraftProfile.currentTimestamp();
                String profileKey = getFreeProfileKey();
                String instanceId = InstancePathResolver.instanceIdForProfileKey(profileKey);
                profile.instanceId = instanceId;
                profile.gameDir = InstancePathResolver.gameDirectoryValue(instanceId);
                try {
                    instanceManager.duplicateInstance(sourceInstance.getName(), instanceId,
                            profileKey, profile.name, versionId);
                    mainProfileJson.profiles.put(profileKey, profile);
                    changed = true;
                } catch (IOException | IllegalArgumentException error) {
                    Log.e("LauncherProfiles", "Could not isolate installed loader version " + versionId, error);
                }
            }
        }

        if (changed) {
            write();
        }
    }

    private static String findBestVersionForInstance(String keyword) {
        File versionsDir = new File(Tools.DIR_GAME_NEW, "versions");
        if (versionsDir.exists() && versionsDir.isDirectory()) {
            File[] files = versionsDir.listFiles(File::isDirectory);
            if (files != null && files.length > 0) {
                if (keyword != null) {
                    for (File dir : files) {
                        if (dir.getName().toLowerCase().contains(keyword)) {
                            return dir.getName();
                        }
                    }
                }
                return files[0].getName();
            }
        }
        return "1.21.10";
    }

    /** Apply the current configuration into a file */
    public static synchronized void write() {
        if (mainProfileJson == null) return;
        ensureSelectedProfileKey();
        persistSilently(getLauncherProfilesFile());
        notifyUpdateListeners();
    }

    public static synchronized @NonNull MinecraftProfile getCurrentProfile() {
        if (mainProfileJson == null || mainProfileJson.profiles == null || mainProfileJson.profiles.isEmpty()) {
            LauncherProfiles.load();
        }
        ensureSelectedProfileKey();

        String selectedKey = LauncherPreferences.DEFAULT_PREF == null ? null :
                LauncherPreferences.DEFAULT_PREF.getString(LauncherPreferences.PREF_KEY_CURRENT_PROFILE, "");
        MinecraftProfile profile = (selectedKey != null && mainProfileJson != null && mainProfileJson.profiles != null)
                ? mainProfileJson.profiles.get(selectedKey)
                : null;
        if (profile != null) {
            return profile;
        }

        if (mainProfileJson != null && mainProfileJson.profiles != null) {
            String fallbackKey = resolveSelectedProfileKey(
                    mainProfileJson.profiles,
                    mainProfileJson.selectedProfile
            );
            if (fallbackKey != null) {
                MinecraftProfile fallbackProfile = mainProfileJson.profiles.get(fallbackKey);
                if (fallbackProfile != null) {
                    saveSelectedProfileKey(fallbackKey);
                    return fallbackProfile;
                }
            }
        }

        // Emergency fallback so getCurrentProfile() NEVER crashes the launcher on fresh/corrupt state
        MinecraftProfile emergency = MinecraftProfile.getDefaultProfile();
        emergency.isDefault = true;
        String emergencyKey = UUID.randomUUID().toString();
        if (mainProfileJson == null) {
            mainProfileJson = new MinecraftLauncherProfiles();
        }
        if (mainProfileJson.profiles == null) {
            mainProfileJson.profiles = new ConcurrentHashMap<>();
        }
        mainProfileJson.profiles.put(emergencyKey, emergency);
        migrateLegacyProfiles();
        saveSelectedProfileKey(emergencyKey);
        persistSilently(getLauncherProfilesFile());
        return emergency;
    }

    /**
     * Ensures that a valid profile key is selected in SharedPreferences and launcherProfiles.selectedProfile.
     * Returns true if launcherProfiles.selectedProfile was updated and should be persisted.
     */
    static synchronized boolean ensureSelectedProfileKey() {
        if (mainProfileJson == null || mainProfileJson.profiles == null || mainProfileJson.profiles.isEmpty()) {
            return false;
        }
        String prefKey = LauncherPreferences.DEFAULT_PREF == null ? null :
                LauncherPreferences.DEFAULT_PREF.getString(LauncherPreferences.PREF_KEY_CURRENT_PROFILE, "");
        String candidate = (prefKey != null && !prefKey.trim().isEmpty())
                ? prefKey
                : mainProfileJson.selectedProfile;
        String resolved = resolveSelectedProfileKey(mainProfileJson.profiles, candidate);
        if (resolved == null) {
            return false;
        }
        boolean jsonChanged = !resolved.equals(mainProfileJson.selectedProfile);
        saveSelectedProfileKey(resolved);
        return jsonChanged;
    }

    private static void saveSelectedProfileKey(@NonNull String resolvedKey) {
        if (mainProfileJson != null) {
            mainProfileJson.selectedProfile = resolvedKey;
        }
        if (LauncherPreferences.DEFAULT_PREF != null) {
            String current = LauncherPreferences.DEFAULT_PREF.getString(
                    LauncherPreferences.PREF_KEY_CURRENT_PROFILE, "");
            if (!resolvedKey.equals(current)) {
                LauncherPreferences.DEFAULT_PREF.edit()
                        .putString(LauncherPreferences.PREF_KEY_CURRENT_PROFILE, resolvedKey)
                        .apply();
            }
        }
    }

    /**
     * Pure selection resolver (also directly unit-tested on JVM without Android SharedPreferences).
     * Prefers preferredKey if valid, then any profile marked isDefault/Default, then deterministic name order.
     */
    static String resolveSelectedProfileKey(Map<String, MinecraftProfile> profiles, String preferredKey) {
        if (profiles == null || profiles.isEmpty()) {
            return null;
        }
        if (preferredKey != null) {
            String trimmed = preferredKey.trim();
            if (!trimmed.isEmpty() && profiles.get(trimmed) != null) {
                return trimmed;
            }
        }
        String defaultNamedKey = null;
        String firstKey = null;
        List<Map.Entry<String, MinecraftProfile>> entries = new ArrayList<>(profiles.entrySet());
        Collections.sort(entries, (left, right) -> {
            MinecraftProfile lp = left.getValue();
            MinecraftProfile rp = right.getValue();
            boolean ld = lp != null && (lp.isDefault || "(Default)".equalsIgnoreCase(lp.name) || "Default".equalsIgnoreCase(lp.name));
            boolean rd = rp != null && (rp.isDefault || "(Default)".equalsIgnoreCase(rp.name) || "Default".equalsIgnoreCase(rp.name));
            if (ld != rd) return ld ? -1 : 1;
            String ln = lp != null && lp.name != null ? lp.name : "";
            String rn = rp != null && rp.name != null ? rp.name : "";
            int cmp = ln.compareToIgnoreCase(rn);
            if (cmp != 0) return cmp;
            String lk = left.getKey() != null ? left.getKey() : "";
            String rk = right.getKey() != null ? right.getKey() : "";
            return lk.compareTo(rk);
        });
        for (Map.Entry<String, MinecraftProfile> entry : entries) {
            String key = entry.getKey();
            MinecraftProfile value = entry.getValue();
            if (key == null || key.trim().isEmpty() || value == null) continue;
            if (firstKey == null) firstKey = key;
            if (value.isDefault || "(Default)".equalsIgnoreCase(value.name) || "Default".equalsIgnoreCase(value.name)) {
                defaultNamedKey = key;
                break;
            }
        }
        return defaultNamedKey != null ? defaultNamedKey : firstKey;
    }

    /**
     * Insert a new profile into the profile map
     * @param minecraftProfile the profile to insert
     */
    public static synchronized void insertMinecraftProfile(MinecraftProfile minecraftProfile) {
        if (mainProfileJson == null) load();
        if (minecraftProfile.created == null || minecraftProfile.created.isEmpty()) {
            minecraftProfile.created = MinecraftProfile.currentTimestamp();
        }
        mainProfileJson.profiles.put(getFreeProfileKey(), minecraftProfile);
    }

    /**
     * Pick an unused normalized key to store a new profile with
     * @return an unused key
     */
    public static synchronized String getFreeProfileKey() {
        Map<String, MinecraftProfile> profileMap = mainProfileJson != null ? mainProfileJson.profiles : null;
        String freeKey = UUID.randomUUID().toString();
        while(profileMap != null && profileMap.get(freeKey) != null) freeKey = UUID.randomUUID().toString();
        return freeKey;
    }

    /**
     * For all keys to be UUIDs, effectively isolating profile created by installers
     * This avoids certain profiles to be erased by the installer
     * @return Whether some profiles have been normalized
     */
    static boolean normalizeProfileIds(MinecraftLauncherProfiles launcherProfiles){
        if (launcherProfiles == null || launcherProfiles.profiles == null) return false;
        String selectedKey = null;
        try {
            if (LauncherPreferences.DEFAULT_PREF != null) {
                selectedKey = LauncherPreferences.DEFAULT_PREF.getString(
                        LauncherPreferences.PREF_KEY_CURRENT_PROFILE, "");
            }
        } catch (Throwable ignored) {}
        NormalizeResult result = normalizeProfileIdsCore(launcherProfiles, selectedKey);
        if (result.replacementSelection != null) {
            try {
                if (LauncherPreferences.DEFAULT_PREF != null) {
                    LauncherPreferences.DEFAULT_PREF.edit()
                            .putString(LauncherPreferences.PREF_KEY_CURRENT_PROFILE, result.replacementSelection)
                            .apply();
                }
            } catch (Throwable ignored) {}
        }
        return result.changed;
    }

    /** Result of a profile-key normalization pass. */
    static final class NormalizeResult {
        final boolean changed;
        final String replacementSelection;
        NormalizeResult(boolean changed, String replacementSelection) {
            this.changed = changed;
            this.replacementSelection = replacementSelection;
        }
    }

    /**
     * Pure normalization core (no Android APIs) so the fresh-install selection repair can be
     * unit-tested on the JVM. Rewrites non-UUID keys (for example the "(Default)" key shipped in
     * assets/launcher_profiles.json) into UUIDs and keeps both the persisted selection and the
     * SharedPreferences selection pointing at a profile that actually exists.
     */
    static NormalizeResult normalizeProfileIdsCore(MinecraftLauncherProfiles launcherProfiles, String selectedKey) {
        if (launcherProfiles == null || launcherProfiles.profiles == null) {
            return new NormalizeResult(false, null);
        }
        boolean hasNormalized = false;
        ArrayList<String> keys = new ArrayList<>();

        // Detect denormalized keys
        for (String profileKey : launcherProfiles.profiles.keySet()) {
            try {
                if (!UUID.fromString(profileKey).toString().equals(profileKey)) keys.add(profileKey);
            } catch (IllegalArgumentException exception) {
                keys.add(profileKey);
                try {
                    Log.w(LauncherProfiles.class.toString(), "Illegal profile uuid: " + profileKey);
                } catch (Throwable ignored) {}
            }
        }

        String replacementSelection = null;
        // Swap the new keys while retaining the user's selected profile. A profile key is not its
        // instance ID, so changing it must never silently reset the selected instance.
        for (String profileKey : keys) {
            MinecraftProfile currentProfile = launcherProfiles.profiles.get(profileKey);
            if (currentProfile == null) continue;
            if (currentProfile.created == null || currentProfile.created.isEmpty()) {
                currentProfile.created = MinecraftProfile.currentTimestamp();
            }
            if ("(Default)".equalsIgnoreCase(profileKey) || "Default".equalsIgnoreCase(profileKey)) {
                currentProfile.isDefault = true;
            }
            String normalizedKey = UUID.randomUUID().toString();
            while (launcherProfiles.profiles.containsKey(normalizedKey)) {
                normalizedKey = UUID.randomUUID().toString();
            }
            launcherProfiles.profiles.put(normalizedKey, currentProfile);
            launcherProfiles.profiles.remove(profileKey);
            if (profileKey.equals(selectedKey)) {
                replacementSelection = normalizedKey;
            }
            if (profileKey.equals(launcherProfiles.selectedProfile)) {
                launcherProfiles.selectedProfile = normalizedKey;
                if (selectedKey == null || selectedKey.trim().isEmpty()) {
                    replacementSelection = normalizedKey;
                }
            }
            hasNormalized = true;
        }

        return new NormalizeResult(hasNormalized, replacementSelection);
    }
}
