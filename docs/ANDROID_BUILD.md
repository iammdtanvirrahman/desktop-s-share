# Build the Android APK

## GitHub Actions (recommended)

1. Open the repository's Actions tab.
2. Select the latest **NEXUS Remote CI** run for `nexus-development`.
3. Wait for both the desktop-agent and Android jobs to complete successfully.
4. Download the `nexus-remote-debug-apk` artifact from the run's Artifacts section.
5. Transfer the APK to your Android phone and install it. Android may ask you to allow installation from the file manager you used.

A debug APK is for testing, not public distribution. It is not Play Store release-signed.

## Build locally

Requirements: Android Studio, JDK 17, Android SDK Platform 35, and Gradle 8.7.

From the repository root:

```bash
gradle -p android assembleDebug
```

APK:

`android/app/build/outputs/apk/debug/app-debug.apk`

## First connection

The app asks for:
- WSS signaling URL, for example `wss://your-domain.example/ws`
- Same private room configured on the laptop
- Same signaling token configured on the laptop
- TURN URL, username, and credential if your network needs a relay

Do not commit real credentials to GitHub. Keep the agent view-only until you explicitly opt in to remote input on the laptop.
