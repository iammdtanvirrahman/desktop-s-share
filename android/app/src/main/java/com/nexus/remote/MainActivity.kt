package com.nexus.remote

import android.app.Activity
import android.os.Bundle
import android.view.ViewGroup
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.TextView

/**
 * Initial Android client shell.
 * The native WebRTC viewer and pairing UI will replace the placeholder in the next milestone.
 */
class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val message = TextView(this).apply {
            text = "NEXUS REMOTE\n\nAndroid client scaffold is installed.\nSecure pairing and live WebRTC viewing are the next milestone."
            textSize = 18f
            setPadding(32, 48, 32, 32)
        }
        setContentView(message, ViewGroup.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.MATCH_PARENT
        ))
    }
}
