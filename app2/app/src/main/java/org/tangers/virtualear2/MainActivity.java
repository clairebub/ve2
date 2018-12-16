package org.tangers.virtualear2;

import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.support.annotation.NonNull;
import android.support.design.widget.BottomNavigationView;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v7.app.AppCompatActivity;
import android.util.Log;
import android.view.MenuItem;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class MainActivity extends AppCompatActivity
        implements ActivityCompat.OnRequestPermissionsResultCallback{

    private static final String TAG = "deebug";
    private static final int PERMISSIONS_REQUEST_CODE = 1;

    private TextView mTextMessage;
    private SoundListener mSoundListener;
    private SoundClassifier mSoundClassifier;

    private BottomNavigationView.OnNavigationItemSelectedListener mOnNavigationItemSelectedListener
            = new BottomNavigationView.OnNavigationItemSelectedListener() {

        @Override
        public boolean onNavigationItemSelected(@NonNull MenuItem item) {
            switch (item.getItemId()) {
                case R.id.navigation_start:
                    startSoundListener();
                    return true;
                case R.id.navigation_stop:
                    stopSoundListener();
                    return true;
                case R.id.navigation_settings:
                    mTextMessage.setText(R.string.title_settings);
                    return true;
            }
            return false;
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        mTextMessage = (TextView) findViewById(R.id.message);
        BottomNavigationView navigation = (BottomNavigationView) findViewById(R.id.navigation);
        navigation.setOnNavigationItemSelectedListener(mOnNavigationItemSelectedListener);

        mSoundClassifier = new SoundClassifier();
        startSoundListener();
    }

    private void startSoundListener() {
        if (mSoundListener != null) {
            showStatusText("Sound listener is already running.");
            return;
        }

        List<String> missingPermissions = getMissingPermissions();
        if (!getMissingPermissions().isEmpty()) {
            String[] permissionsToRequest = new String[missingPermissions.size()];
            missingPermissions.toArray(permissionsToRequest);
            ActivityCompat.requestPermissions(
                    this,
                    permissionsToRequest,
                    PERMISSIONS_REQUEST_CODE);
            return;
        }
        mSoundListener = new SoundListener();
        mSoundListener.start(new SoundListener.Callback() {
            @Override
            public void onSound(byte[] data, int len) {
                String label = mSoundClassifier.classifySound(data, 0, len);
                showSoundLabel(label);
            }

            @Override
            public void onSoundClassified(String label) {
                showStatusText(label);
            }
        });
        showStatusText("Sound Listener started.");
    }

    private void stopSoundListener() {
        if (mSoundListener != null) {
            mSoundListener.stop();
            mSoundListener = null;
            showStatusText("Sound Listener stopped.");
        } else {
            showStatusText("Sound Listener is already stopped.");
        }
    }

    private List<String> getMissingPermissions() {
        String[] requiredPermissions = new String[0];
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), PackageManager.GET_PERMISSIONS);
            if (info.requestedPermissions != null) {
                requiredPermissions = info.requestedPermissions;
            }
        } catch (Exception e) {
            Log.e(TAG, e.toString());
        }

        List<String> missingPermissions = new ArrayList<>();
        for (String permission : requiredPermissions) {
            if (ContextCompat.checkSelfPermission(this, permission)
                    != PackageManager.PERMISSION_GRANTED) {
                missingPermissions.add(permission);
            }
        }
        return missingPermissions;
    }

    private void showSoundLabel(final String label) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                mTextMessage.setText(label);
            }
        });
    }

    @Override
    public void onRequestPermissionsResult(
            int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
    }

    private void showStatusText(final String text) {
        runOnUiThread(
                new Runnable() {
                    @Override
                    public void run() {
                        mTextMessage.setText(text);
                    }
                });
    }

}
