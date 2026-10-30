# Build and install the Android app

## GitHub Actions

1. Open the repository's Actions tab.
2. Select the latest successful **NEXUS Remote CI** run for `nexus-development`.
3. Download the `nexus-remote-debug-apk` artifact.
4. Extract `app-debug.apk` and install it on your Android phone.
5. Allow camera access when prompted.

## Local build

Requirements: Android Studio, JDK 17, Android SDK Platform 35, and Gradle 8.7.

```bash
gradle -p android assembleDebug
```

APK output:

`android/app/build/outputs/apk/debug/app-debug.apk`

## First use

The app opens the QR scanner immediately. On the laptop, launch the NEXUS Remote desktop app; its QR appears automatically. Scan that QR with the phone. The QR contains a short-lived pairing token and secure signaling URL, so no manual credentials are required.

The QR expires after 3 minutes. Generate a new one in the laptop app if it expires. A successful APK build is not proof that signaling/TURN has been deployed or that a physical device connection has passed testing.
