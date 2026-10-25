package net.kdt.pojavlaunch;

import android.content.*;
import android.os.*;
import android.view.WindowManager;
import androidx.appcompat.app.*;
import net.kdt.pojavlaunch.utils.*;

import static net.kdt.pojavlaunch.prefs.LauncherPreferences.PREF_IGNORE_NOTCH;

public abstract class BaseActivity extends AppCompatActivity {

    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleUtils.setLocale(newBase));
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setTheme(net.kdt.pojavlaunch.theme.ThemeManager.getSavedTheme());
        LocaleUtils.setLocale(this);
        Tools.setFullscreen(this, setFullscreen());
        Tools.updateWindowSize(this);
    }

    /** @return Whether the activity should be set as a fullscreen one */
    public boolean setFullscreen(){
        return true;
    }


    @Override
    public void startActivity(Intent i) {
        super.startActivity(i);
        //new Throwable("StartActivity").printStackTrace();
    }

    @Override
    protected void onResume() {
        super.onResume();
        Tools.checkStorageInteractive(this);
    }

    @Override
    protected void onPostResume() {
        super.onPostResume();
        Tools.setFullscreen(this, setFullscreen());
        Tools.ignoreNotch(shouldIgnoreNotch(),this);
        applyCutoutMode();
    }

    /**
     * Lets the window extend into the camera cutout area.
     *
     * <p>{@code LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES} (what the engine uses) does nothing for a
     * punch-hole on a <b>long</b> edge, which is exactly where it sits once the phone is rotated to
     * landscape. The window then gets inset by the cutout and the game shows a black strip down one
     * side. {@code ALWAYS} (API 30+) and {@code DEFAULT} for older releases both let the surface cover
     * the whole display; the small area behind the camera is not something the player needs.
     */
    private void applyCutoutMode() {
        // Only fullscreen, notch-ignoring screens (i.e. the in-game one) draw behind the cutout.
        if (!setFullscreen() || !shouldIgnoreNotch()) return;
        try {
            WindowManager.LayoutParams attributes = getWindow().getAttributes();
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                attributes.layoutInDisplayCutoutMode =
                        WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_ALWAYS;
            } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                attributes.layoutInDisplayCutoutMode =
                        WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
            } else {
                return;
            }
            getWindow().setAttributes(attributes);
            getWindow().addFlags(WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN);
        } catch (Throwable ignored) {
            // Never let a window-manager quirk take the activity down.
        }
    }

    /** @return Whether or not the notch should be ignored */
    protected boolean shouldIgnoreNotch(){
        return PREF_IGNORE_NOTCH;
    }
}
