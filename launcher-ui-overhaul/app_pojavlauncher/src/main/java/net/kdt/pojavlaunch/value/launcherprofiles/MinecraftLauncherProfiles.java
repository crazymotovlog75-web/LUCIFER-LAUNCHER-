package net.kdt.pojavlaunch.value.launcherprofiles;
import androidx.annotation.Keep;

import java.util.*;
import net.kdt.pojavlaunch.*;

@Keep
public class MinecraftLauncherProfiles {
	public Map<String, MinecraftProfile> profiles = new HashMap<>();
	public boolean profilesWereMigrated;
	public String clientToken;
	public Map<String, MinecraftAuthenticationDatabase> authenticationDatabase;
	// public Map launcherVersion;
	public MinecraftLauncherSettings settings;
	// public Map analyticsToken;
	public int analyticsFailcount;
	public MinecraftSelectedUser selectedUser;
	/**
	 * Key of the last selected profile, mirrored from SharedPreferences.
	 * Present in vanilla launcher_profiles.json (and in the bundled asset template) but was
	 * previously not mapped here, which meant fresh installs had no fallback selection and
	 * crashed in getCurrentProfile() with "The current profile stopped existing :(".
	 */
	public String selectedProfile;

    public String toJson() {
        return Tools.GLOBAL_GSON.toJson(this);
    }
}
