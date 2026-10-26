#include <EGL/egl.h>
#include <android/native_window.h>
#include <android/native_window_jni.h>
#include <string.h>
#include <malloc.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <stdbool.h>
#include <environ/environ.h>
#include "gl_bridge.h"
#include "egl_loader.h"

#define TAG __FILE_NAME__
#include <unistd.h>
#include <log.h>

//
// Created by maks on 17.09.2022.
//

static __thread gl_render_window_t* currentBundle;
static EGLDisplay g_EglDisplay;

bool gl_init() {
    if(!dlsym_EGL()) return false;
    g_EglDisplay = eglGetDisplay_p(EGL_DEFAULT_DISPLAY);
    if (g_EglDisplay == EGL_NO_DISPLAY) {
        LOGE("%s", "eglGetDisplay_p(EGL_DEFAULT_DISPLAY) returned EGL_NO_DISPLAY");
        return false;
    }
    if (eglInitialize_p(g_EglDisplay, 0, 0) != EGL_TRUE) {
        LOGE("eglInitialize_p() failed: %04x", eglGetError_p());
        return false;
    }
    return true;
}

gl_render_window_t* gl_get_current() {
    return currentBundle;
}

static void gl4esi_get_display_dimensions(int* width, int* height) {
    if(currentBundle == NULL) goto zero;
    EGLSurface surface = currentBundle->surface;
    // Fetch dimensions from the EGL surface - the most reliable way
    EGLBoolean result_width = eglQuerySurface_p(g_EglDisplay, surface, EGL_WIDTH, width);
    EGLBoolean result_height = eglQuerySurface_p(g_EglDisplay, surface, EGL_HEIGHT, height);
    if(!result_width || !result_height) goto zero;
    return;

    zero:
    // No idea what to do, but feeding gl4es incorrect or non-initialized dimensions may be
    // a bad idea. Set to zero in case of errors.
    *width = 0;
    *height = 0;
}

gl_render_window_t* gl_init_context(gl_render_window_t *share) {
    gl_render_window_t* bundle = malloc(sizeof(gl_render_window_t));
    memset(bundle, 0, sizeof(gl_render_window_t));
    /*
     * Lucifer: the window config used to ask for an ES2-only, stencil-less framebuffer.
     *
     *  - EGL_STENCIL_SIZE 8: Minecraft opens its window with stencil bits and the 1.21.11 render
     *    pipeline really uses the stencil buffer. Getting a config without one makes those passes
     *    write into whatever the depth buffer happened to hold, which is how fully opaque geometry
     *    ends up drawn as the black / see-through slabs reported by users.
     *  - EGL_OPENGL_ES3_BIT_KHR: when the chosen renderer runs on a GLES3 context, only configs
     *    that can actually back ES3 may be picked. ES2-only configs make eglCreateContext(3) fail,
     *    which is the "renderer refuses to launch on 1.21.11" symptom.
     *  - EGL_SAMPLE_BUFFERS 0: never get handed a multisampled default framebuffer by accident; the
     *    resolve pass is pure fillrate cost and we do not use MSAA.
     */
#ifndef EGL_OPENGL_ES3_BIT_KHR
#define EGL_OPENGL_ES3_BIT_KHR 0x0040
#endif
    EGLint requested_es = strtol(getenv("LIBGL_ES"), NULL, 0);
    if (requested_es < 2 || requested_es > 3) requested_es = 2;
    EGLint renderable_type = EGL_OPENGL_ES2_BIT;
    if (requested_es >= 3) renderable_type |= EGL_OPENGL_ES3_BIT_KHR;
    EGLint egl_attributes[] = { EGL_BLUE_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_RED_SIZE, 8, EGL_ALPHA_SIZE, 8,
                                EGL_DEPTH_SIZE, 24, EGL_STENCIL_SIZE, 8, EGL_SAMPLE_BUFFERS, 0,
                                EGL_SURFACE_TYPE, EGL_WINDOW_BIT|EGL_PBUFFER_BIT,
                                EGL_RENDERABLE_TYPE, 0 /* filled from renderable_type below */,
                                EGL_NONE };
    // Patch by symbol, not by a hardcoded offset, so the list above can never desync from it.
    for (size_t i = 0; i + 1 < sizeof(egl_attributes) / sizeof(egl_attributes[0]); i++) {
        if (egl_attributes[i] == EGL_RENDERABLE_TYPE) {
            egl_attributes[i + 1] = renderable_type;
            break;
        }
    }
    /*
     * Some older drivers simply have no stencil-capable window config, and a few report no
     * ES3-capable config at all. Never trade a launch failure for a nicer config: the plain
     * ES2 / depth-only request the bridge used before is kept as the fallback.
     */
    EGLint fallback_attributes[] = { EGL_BLUE_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_RED_SIZE, 8,
                                     EGL_ALPHA_SIZE, 8, EGL_DEPTH_SIZE, 24,
                                     EGL_SURFACE_TYPE, EGL_WINDOW_BIT|EGL_PBUFFER_BIT,
                                     EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT, EGL_NONE };
    EGLint *chosen_attributes = egl_attributes;
    EGLint num_configs = 0;

    if (eglChooseConfig_p(g_EglDisplay, chosen_attributes, NULL, 0, &num_configs) != EGL_TRUE
            || num_configs == 0) {
        LOGW("No stencil/ES%ld window config (err %04x), retrying with the legacy config",
             (long) requested_es, eglGetError_p());
        chosen_attributes = fallback_attributes;
        requested_es = 2;
        num_configs = 0;
        if (eglChooseConfig_p(g_EglDisplay, chosen_attributes, NULL, 0, &num_configs) != EGL_TRUE) {
            LOGE("eglChooseConfig_p() failed: %04x", eglGetError_p());
            free(bundle);
            return NULL;
        }
        if (num_configs == 0) {
            LOGE("%s", "eglChooseConfig_p() found no matching config");
            free(bundle);
            return NULL;
        }
    }

    // Get the first matching config
    eglChooseConfig_p(g_EglDisplay, chosen_attributes, &bundle->config, 1, &num_configs);
    eglGetConfigAttrib_p(g_EglDisplay, bundle->config, EGL_NATIVE_VISUAL_ID, &bundle->format);

    {
        EGLBoolean bindResult;
        const char *amethyst_renderer = getenv("AMETHYST_RENDERER");
        // getenv() may return NULL; strncmp on it is a crash before the game even starts.
        if (amethyst_renderer != NULL && strncmp(amethyst_renderer, "opengles3_desktopgl", 19) == 0) {
            printf("EGLBridge: Binding to desktop OpenGL\n");
            bindResult = eglBindAPI_p(EGL_OPENGL_API);
        } else {
            printf("EGLBridge: Binding to OpenGL ES\n");
            bindResult = eglBindAPI_p(EGL_OPENGL_ES_API);
        }
        if (!bindResult) printf("EGLBridge: bind failed: %p\n", eglGetError_p());
    }

    int libgl_es = requested_es;
    const EGLint egl_context_attributes[] = { EGL_CONTEXT_CLIENT_VERSION, libgl_es, EGL_NONE };
    bundle->context = eglCreateContext_p(g_EglDisplay, bundle->config, share == NULL ? EGL_NO_CONTEXT : share->context, egl_context_attributes);

    if (bundle->context == EGL_NO_CONTEXT) {
        LOGE("eglCreateContext_p() finished with error: %04x", eglGetError_p());
        free(bundle);
        return NULL;
    }
    return bundle;
}

void gl_swap_surface(gl_render_window_t* bundle) {
    /*
     * In some cases (see MinecraftGLSurface.start(), android kills the surface automatically for
     * us, if we try to release/destroy it, we SIGSEGV. Check if we are -19x-19 or some other
     * invalid value and skip the release because Android decided to handle releasing it for us.
     * This goes against every piece of documentation I have ever seen but who actually reads those?
     *
     * Some drivers take forever to properly destroy the surface, they do it part at a time or
     * some other garbage while SIGSEGVing us if we try releasing while they're in the middle of
     * turning the surface dead. This makes the width and height make it look valid when it actually
     * isn't so we wait for them and hope there is no race condition of both us and Android trying
     * to release the surface. This seems driver dependent as AVD and Waydroid do not need 0.75s
     * to set the bloody height and width to their proper values. They just do it, instantly.
     */
    usleep(750000); // An overkill amount of time to wait for a surface to finish dying
    int32_t nativeWindowWidth = ANativeWindow_getWidth(pojav_environ->pojavWindow);
    int32_t nativeWindowHeight = ANativeWindow_getHeight(pojav_environ->pojavWindow);
    if ((nativeWindowWidth > 0) || (nativeWindowHeight > 0)) {
        LOGI("Native surface dimensions (%d x %d)\n",
             nativeWindowWidth, nativeWindowHeight);
        if (bundle->nativeSurface != NULL) {
            ANativeWindow_release(bundle->nativeSurface);
        }
        if (bundle->surface != NULL) eglDestroySurface_p(g_EglDisplay, bundle->surface);
    } else {
        LOGW("Native surface dimensions (%d x %d) are invalid! Assuming given nativeSurface is bad.\n",
             nativeWindowWidth, nativeWindowHeight);
    }
    if(bundle->newNativeSurface != NULL) {
        LOGI("Switching to new native surface");
        bundle->nativeSurface = bundle->newNativeSurface;
        bundle->newNativeSurface = NULL;
        ANativeWindow_acquire(bundle->nativeSurface);
        ANativeWindow_setBuffersGeometry(bundle->nativeSurface, 0, 0, bundle->format);
        bundle->surface = eglCreateWindowSurface_p(g_EglDisplay, bundle->config, bundle->nativeSurface, NULL);
    }else{
        LOGI("No new native surface, switching to 1x1 pbuffer");
        bundle->nativeSurface = NULL;
        const EGLint pbuffer_attrs[] = {EGL_WIDTH, 1 , EGL_HEIGHT, 1, EGL_NONE};
        bundle->surface = eglCreatePbufferSurface_p(g_EglDisplay, bundle->config, pbuffer_attrs);
    }
    //eglMakeCurrent_p(g_EglDisplay, bundle->surface, bundle->surface, bundle->context);
}

void gl_make_current(gl_render_window_t* bundle) {

    if(bundle == NULL) {
        if(eglMakeCurrent_p(g_EglDisplay, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT)) {
            currentBundle = NULL;
        }
        return;
    }
    bool hasSetMainWindow = false;
    if(pojav_environ->mainWindowBundle == NULL) {
        pojav_environ->mainWindowBundle = (basic_render_window_t*)bundle;
        LOGI("Main window bundle is now %p", pojav_environ->mainWindowBundle);
        pojav_environ->mainWindowBundle->newNativeSurface = pojav_environ->pojavWindow;
        hasSetMainWindow = true;
    }
    LOGI("Making current, surface=%p, nativeSurface=%p, newNativeSurface=%p", bundle->surface, bundle->nativeSurface, bundle->newNativeSurface);
    if(bundle->surface == NULL) { //it likely will be on the first run
        gl_swap_surface(bundle);
    }
    if(eglMakeCurrent_p(g_EglDisplay, bundle->surface, bundle->surface, bundle->context)) {
        currentBundle = bundle;
    }else {
        if(hasSetMainWindow) {
            pojav_environ->mainWindowBundle->newNativeSurface = NULL;
            gl_swap_surface((gl_render_window_t*)pojav_environ->mainWindowBundle);
            pojav_environ->mainWindowBundle = NULL;
        }
        LOGE("eglMakeCurrent returned with error: %04x", eglGetError_p());
    }

}

void gl_swap_buffers() {
    if(currentBundle->state == STATE_RENDERER_NEW_WINDOW) {
        eglMakeCurrent_p(g_EglDisplay, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT); //detach everything to destroy the old EGLSurface
        gl_swap_surface(currentBundle);
        eglMakeCurrent_p(g_EglDisplay, currentBundle->surface, currentBundle->surface, currentBundle->context);
        currentBundle->state = STATE_RENDERER_ALIVE;
    }
    if(currentBundle->surface != NULL)
        if(!eglSwapBuffers_p(g_EglDisplay, currentBundle->surface) && eglGetError_p() == EGL_BAD_SURFACE) {
            eglMakeCurrent_p(g_EglDisplay, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
            currentBundle->newNativeSurface = NULL;
            gl_swap_surface(currentBundle);
            eglMakeCurrent_p(g_EglDisplay, currentBundle->surface, currentBundle->surface, currentBundle->context);
            LOGI("The window has died, awaiting window change");
    }

}

void gl_setup_window() {
    if(pojav_environ->mainWindowBundle != NULL) {
        LOGI("Main window bundle is not NULL, changing state");
        pojav_environ->mainWindowBundle->state = STATE_RENDERER_NEW_WINDOW;
        pojav_environ->mainWindowBundle->newNativeSurface = pojav_environ->pojavWindow;
    }
}

void gl_swap_interval(int swapInterval) {
    if(pojav_environ->force_vsync) swapInterval = 1;

    eglSwapInterval_p(g_EglDisplay, swapInterval);
}

JNIEXPORT void JNICALL
Java_org_lwjgl_opengl_PojavRendererInit_nativeInitGl4esInternals(JNIEnv *env, jclass clazz,
                                                            jobject function_provider) {
    LOGI("GL4ES internals initializing...");
    jclass funcProviderClass = (*env)->GetObjectClass(env, function_provider);
    jmethodID method_getFunctionAddress = (*env)->GetMethodID(env, funcProviderClass, "getFunctionAddress", "(Ljava/lang/CharSequence;)J");
#define GETSYM(N) ((*env)->CallLongMethod(env, function_provider, method_getFunctionAddress, (*env)->NewStringUTF(env, N)));

    void (*set_getmainfbsize)(void (*new_getMainFBSize)(int* width, int* height)) = (void*)GETSYM("set_getmainfbsize");
    if(set_getmainfbsize != NULL) {
        LOGI("GL4ES internals initialized dimension callback");
        set_getmainfbsize(gl4esi_get_display_dimensions);
    }

#undef GETSYM
}
