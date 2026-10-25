package net.kdt.pojavlaunch.utils;

import net.kdt.pojavlaunch.JMinecraftVersionList;
import net.kdt.pojavlaunch.Tools;
import net.kdt.pojavlaunch.compat.MinecraftCompat;
import net.kdt.pojavlaunch.extra.ExtraConstants;
import net.kdt.pojavlaunch.extra.ExtraCore;

import java.text.ParseException;
import java.util.Date;

/** Class here to help with various stuff to help run lower versions smoothly */
public class OldVersionsUtils {
    /** Lower minecraft versions fare better with opengl 1
     * @param version The version about to be launched
     */
    public static void selectOpenGlVersion(JMinecraftVersionList.Version version){
        // Modern versions (1.21.11+) changed the render pipeline: it needs a real OpenGL 3.3+ core
        // context with buffer storage. Answering them with a GLES2 context leaves the world black
        // while the game keeps running, which is exactly the "black screen" symptom.
        if (version != null && MinecraftCompat.requiresModernGl(version.id)) {
            ExtraCore.setValue(ExtraConstants.OPEN_GL_VERSION, "3");
            return;
        }

        // 1309989600 is 2011-07-07  2011-07-07T22:00:00+00:00
        String creationTime = version == null ? null : version.time;
        if(!Tools.isValidString(creationTime)){
            ExtraCore.setValue(ExtraConstants.OPEN_GL_VERSION, "2");
            return;
        }

        try {
           Date creationDate = DateUtils.parseReleaseDate(creationTime);
            if(creationDate == null){
                ExtraCore.setValue(ExtraConstants.OPEN_GL_VERSION, "2");
                return;
            }
            String openGlVersion =  DateUtils.dateBefore(creationDate, 2011, 6, 8) ? "1" : "2";
            ExtraCore.setValue(ExtraConstants.OPEN_GL_VERSION, openGlVersion);
        }catch (ParseException exception){
            ExtraCore.setValue(ExtraConstants.OPEN_GL_VERSION, "2");
        }
    }
}
