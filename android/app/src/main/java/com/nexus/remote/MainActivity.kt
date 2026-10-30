package com.nexus.remote

import android.app.Activity
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.webkit.WebViewAssetLoader
import com.google.zxing.integration.android.IntentResult
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import org.json.JSONObject

class MainActivity : Activity() {
    private lateinit var webView: WebView
    private lateinit var assetLoader: WebViewAssetLoader

    private val qrScanner = registerForActivityResult(ScanContract()) { result ->
        val contents = result.contents
        if (contents.isNullOrBlank()) {
            showScanPrompt()
        } else {
            openViewer(contents)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        startQrScan()
    }

    private fun startQrScan() {
        val options = ScanOptions()
            .setDesiredBarcodeFormats(ScanOptions.QR_CODE)
            .setPrompt("Scan the QR code shown on your laptop")
            .setBeepEnabled(false)
            .setOrientationLocked(false)
        qrScanner.launch(options)
    }

    private fun showScanPrompt() {
        val background = GradientDrawable().apply {
            setColor(Color.rgb(9, 11, 18))
        }
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(32, 32, 32, 32)
            this.background = background
        }
        val title = TextView(this).apply {
            text = "NEXUS REMOTE"
            setTextColor(Color.WHITE)
            textSize = 24f
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
        }
        val message = TextView(this).apply {
            text = "Scan the QR code shown on your laptop to connect."
            setTextColor(Color.LTGRAY)
            textSize = 15f
            gravity = Gravity.CENTER
            setPadding(12, 18, 12, 24)
        }
        val scanButton = Button(this).apply {
            text = "SCAN QR CODE"
            setOnClickListener { startQrScan() }
        }
        layout.addView(title)
        layout.addView(message)
        layout.addView(scanButton)
        setContentView(layout)
    }

    private fun openViewer(rawPayload: String) {
        val payload = try {
            JSONObject(rawPayload).also { qr ->
                val wsUrl = qr.optString("ws_url")
                if (qr.optString("app") != "nexus-remote" || qr.optInt("v") != 1 ||
                    !wsUrl.startsWith("wss://") ||
                    qr.optString("room").isBlank() || qr.optString("token").isBlank()
                ) {
                    throw IllegalArgumentException("This is not a valid NEXUS pairing QR.")
                }
                val expiresAt = qr.optLong("expires_at", 0L)
                if (expiresAt > 0L && System.currentTimeMillis() / 1000L >= expiresAt) {
                    throw IllegalArgumentException("This pairing QR has expired. Generate a new one on the laptop.")
                }
            }
        } catch (error: Exception) {
            Toast.makeText(this, error.message ?: "Invalid pairing QR", Toast.LENGTH_LONG).show()
            showScanPrompt()
            return
        }

        assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        webView = WebView(this)
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            mediaPlaybackRequiresUserGesture = false
            javaScriptCanOpenWindowsAutomatically = false
            setSupportMultipleWindows(false)
        }
        webView.addJavascriptInterface(object {
            @JavascriptInterface
            fun scanAgain() {
                runOnUiThread { startQrScan() }
            }
        }, "NexusNative")
        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest
            ): WebResourceResponse? = assetLoader.shouldInterceptRequest(request.url)
        }
        webView.webChromeClient = WebChromeClient()
        webView.overScrollMode = View.OVER_SCROLL_NEVER
        setContentView(webView)
        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest
            ): WebResourceResponse? = assetLoader.shouldInterceptRequest(request.url)

            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                val safeJsonString = JSONObject.quote(rawPayload)
                view.evaluateJavascript("window.NEXUS_REMOTE && window.NEXUS_REMOTE.startFromQr($safeJsonString);", null)
            }
        }
        webView.loadUrl("https://appassets.androidplatform.net/assets/index.html")
    }

    override fun onDestroy() {
        if (::webView.isInitialized) {
            webView.stopLoading()
            webView.destroy()
        }
        super.onDestroy()
    }
}
