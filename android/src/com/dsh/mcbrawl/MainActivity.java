package com.dsh.mcbrawl;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.os.Build;
import android.os.Bundle;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowInsets;
import android.webkit.GeolocationPermissions;
import android.webkit.JsPromptResult;
import android.webkit.JsResult;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.TextView;

import java.io.IOException;
import java.io.InputStream;
import java.util.Locale;

/**
 * 方块猜拳战场 · 手机壳（WebView + assets/www）
 *
 * 兼容性要点（都是真机踩出来的）：
 *  · 目标 SDK 压到 34：Android 15/16 只对 target=35+ 的 App 强制 edge-to-edge，
 *    否则状态栏/手势条会盖住游戏界面。
 *  · 仍然手动处理 WindowInsets，把系统栏、刘海、输入法的高度让出来（兜底）。
 *  · 深色窗口背景 + 启动占位，避免启动时白屏闪一下。
 *  · 关闭系统"强制深色 / 算法深色"，否则 iQOO/OriginOS 会把配色改掉。
 *  · setTextZoom(100)：系统字体放大不再把游戏文字撑变形。
 */
public class MainActivity extends Activity {

    private static final String ORIGIN = "https://mcbrawl.local";
    private WebView web;
    private FrameLayout root;
    private View splash;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        /* 窗口底色先铺满，避免启动白屏 */
        Window w = getWindow();
        w.setBackgroundDrawable(new ColorDrawable(0xFF0E1116));
        if (Build.VERSION.SDK_INT >= 21) {
            w.setStatusBarColor(0xFF0E1116);
            w.setNavigationBarColor(0xFF0E1116);
        }

        root = new FrameLayout(this);
        root.setBackgroundColor(0xFF0E1116);
        root.setFitsSystemWindows(false);

        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#0e1116"));
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);
        web.setLayerType(View.LAYER_TYPE_HARDWARE, null);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setUseWideViewPort(false);      /* 布局宽度 = 屏幕宽度，走移动端 CSS */
        s.setLoadWithOverviewMode(false);
        s.setTextZoom(100);               /* 系统字体放大不影响游戏排版 */
        s.setJavaScriptCanOpenWindowsAutomatically(false);
        s.setSupportMultipleWindows(false);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        if (Build.VERSION.SDK_INT >= 21) {
            s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }
        /* 不要让系统把深色配色反转（OriginOS / MIUI 的"强制深色"） */
        try{
            if (Build.VERSION.SDK_INT >= 29) {
                s.setForceDark(WebSettings.FORCE_DARK_OFF);
            }
        }catch(Throwable ignored){}
        try{
            if (Build.VERSION.SDK_INT >= 33) {
                s.setAlgorithmicDarkeningAllowed(false);
            }
        }catch(Throwable ignored){}

        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                try {
                    String url = request.getUrl().toString();
                    if (url.startsWith(ORIGIN + "/")) {
                        String path = url.substring(ORIGIN.length() + 1);
                        int q = path.indexOf('?');
                        if (q >= 0) path = path.substring(0, q);
                        int h = path.indexOf('#');
                        if (h >= 0) path = path.substring(0, h);
                        if (path.isEmpty()) path = "index.html";
                        InputStream in = getAssets().open("www/" + path);
                        return new WebResourceResponse(mimeOf(path), null, in);
                    }
                } catch (IOException e) {
                    /* 落到默认处理（等价 404） */
                }
                return null;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                if (splash != null) {
                    splash.setVisibility(View.GONE);
                }
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onJsAlert(WebView v, String url, String message, final JsResult result) {
                new AlertDialog.Builder(MainActivity.this)
                        .setMessage(message)
                        .setPositiveButton("好", new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface d, int w2) { result.confirm(); }
                        })
                        .setOnCancelListener(new DialogInterface.OnCancelListener() {
                            public void onCancel(DialogInterface d) { result.cancel(); }
                        })
                        .show();
                return true;
            }

            @Override
            public boolean onJsConfirm(WebView v, String url, String message, final JsResult result) {
                new AlertDialog.Builder(MainActivity.this)
                        .setMessage(message)
                        .setPositiveButton("确定", new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface d, int w2) { result.confirm(); }
                        })
                        .setNegativeButton("取消", new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface d, int w2) { result.cancel(); }
                        })
                        .setOnCancelListener(new DialogInterface.OnCancelListener() {
                            public void onCancel(DialogInterface d) { result.cancel(); }
                        })
                        .show();
                return true;
            }

            @Override
            public boolean onJsPrompt(WebView v, String url, String message, String defaultValue,
                                      final JsPromptResult result) {
                final EditText input = new EditText(MainActivity.this);
                input.setText(defaultValue == null ? "" : defaultValue);
                input.setSelection(input.getText().length());
                new AlertDialog.Builder(MainActivity.this)
                        .setMessage(message)
                        .setView(input)
                        .setPositiveButton("确定", new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface d, int w2) {
                                result.confirm(input.getText().toString());
                            }
                        })
                        .setNegativeButton("取消", new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface d, int w2) { result.cancel(); }
                        })
                        .setOnCancelListener(new DialogInterface.OnCancelListener() {
                            public void onCancel(DialogInterface d) { result.cancel(); }
                        })
                        .show();
                return true;
            }

            @Override
            public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback cb) {
                cb.invoke(origin, false, false);
            }
        });

        /* 启动占位：深色底 + 一行字，页面加载完就撤掉 */
        splash = buildSplash();
        root.addView(web, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        root.addView(splash, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(root);

        /* 系统栏 / 刘海 / 输入法内边距：内容和状态栏、手势条永远不重叠 */
        root.setOnApplyWindowInsetsListener(new View.OnApplyWindowInsetsListener() {
            @Override
            public WindowInsets onApplyWindowInsets(View v, WindowInsets insets) {
                int l = 0, t = 0, r = 0, b = 0;
                if (Build.VERSION.SDK_INT >= 20) {
                    l = insets.getSystemWindowInsetLeft();
                    t = insets.getSystemWindowInsetTop();
                    r = insets.getSystemWindowInsetRight();
                    b = insets.getSystemWindowInsetBottom();
                }
                if (Build.VERSION.SDK_INT >= 28 && insets.getDisplayCutout() != null) {
                    t = Math.max(t, insets.getDisplayCutout().getSafeInsetTop());
                    b = Math.max(b, insets.getDisplayCutout().getSafeInsetBottom());
                    l = Math.max(l, insets.getDisplayCutout().getSafeInsetLeft());
                    r = Math.max(r, insets.getDisplayCutout().getSafeInsetRight());
                }
                web.setPadding(l, t, r, b);
                if (splash != null) splash.setPadding(l, t, r, b);
                return insets;
            }
        });

        /* 方便真机排查：Chrome 打开 chrome://inspect 就能看到这个 WebView */
        try{ WebView.setWebContentsDebuggingEnabled(true); }catch(Throwable ignored){}

        web.loadUrl(ORIGIN + "/index.html");
    }

    private View buildSplash() {
        FrameLayout box = new FrameLayout(this);
        box.setBackgroundColor(0xFF0E1116);
        TextView tv = new TextView(this);
        tv.setText("方块猜拳战场");
        tv.setTextColor(0xFF6EE7A8);
        tv.setTextSize(TypedValue.COMPLEX_UNIT_SP, 20);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.gravity = Gravity.CENTER;
        box.addView(tv, lp);
        return box;
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            if (web != null && web.canGoBack()) { web.goBack(); return true; }
            finish();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (web != null) web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
    }

    @Override
    protected void onDestroy() {
        try{
            if (web != null) {
                web.loadUrl("about:blank");
                web.destroy();
                web = null;
            }
        }catch(Throwable ignored){}
        super.onDestroy();
    }

    private static String mimeOf(String path) {
        String p = path.toLowerCase(Locale.ROOT);
        if (p.endsWith(".html") || p.endsWith(".htm")) return "text/html";
        if (p.endsWith(".js")) return "text/javascript";
        if (p.endsWith(".css")) return "text/css";
        if (p.endsWith(".json")) return "application/json";
        if (p.endsWith(".webmanifest")) return "application/manifest+json";
        if (p.endsWith(".png")) return "image/png";
        if (p.endsWith(".jpg") || p.endsWith(".jpeg")) return "image/jpeg";
        if (p.endsWith(".gif")) return "image/gif";
        if (p.endsWith(".svg")) return "image/svg+xml";
        if (p.endsWith(".ico")) return "image/x-icon";
        if (p.endsWith(".woff2")) return "font/woff2";
        return "application/octet-stream";
    }
}
