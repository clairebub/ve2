package org.tangers.virtualear2;

import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.Environment;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;

public class SoundListener {

    interface Callback {
        // called when the listener captures the sound
        void onSound(byte[] data, int len);

        void onSoundClassified(String label);
    }

    private static final String TAG = "deebug";
    private static final int SAMPLE_RATE = 22050;
    private static final int AUDIO_LENGTH_IN_SECONDS = 2;
    private static final int AUDIO_CHANNEL = AudioFormat.CHANNEL_IN_MONO;
    private static final int AUDIO_ENCODING = AudioFormat.ENCODING_PCM_16BIT;

    private Thread mThread;

    void start(Callback callback) {
        if (mThread != null) {
            throw new IllegalStateException();
        }
        mThread = new Thread(new SoundListenerRunnable(callback), "SoundListenerRunnable");
        mThread.start();
    }

    void stop() {
        if (mThread != null) {
            mThread.interrupt();
        }
        mThread = null;
    }

    private class SoundListenerRunnable implements Runnable {
        private final Callback mCallback;
        private final AudioRecord mAudioRecord;
        private final int mBytesPerRead;
        private final byte[] mBuffer;
        private int mBufferPos;
        private long mLastBufferFlushTimeMillis;

        public SoundListenerRunnable(Callback callback) {
            mCallback = callback;
            mBytesPerRead = AudioRecord.getMinBufferSize(
                    SAMPLE_RATE,
                    AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT);
            Log.d(TAG, String.format("AudioRecord.getMinBufferSize() is %d", mBytesPerRead));
            int bufferSize = SAMPLE_RATE * AUDIO_LENGTH_IN_SECONDS;
            if (mBytesPerRead > bufferSize) {
                bufferSize = mBytesPerRead;
                Log.w(TAG, String.format("BufferSize increased to match minBufferSize %d", bufferSize));
            }
            mBuffer = new byte[bufferSize];
            mBufferPos = 0;
            mAudioRecord = new AudioRecord(
                    MediaRecorder.AudioSource.MIC,
                    SAMPLE_RATE,
                    AUDIO_CHANNEL,
                    AUDIO_ENCODING,
                    mBuffer.length);
            if (mAudioRecord.getState() != AudioRecord.STATE_INITIALIZED) {
                mAudioRecord.release();
                throw new IllegalStateException();
            }
            mAudioRecord.startRecording();
            mLastBufferFlushTimeMillis = System.currentTimeMillis();
        }

        // flushing the sound buffer every AUDIO_LENGTH_IN_SECONDS or whenever the buffer is full
        public void run() {
            while (true) {
                if (Thread.currentThread().isInterrupted()) {
                    Log.d(TAG, String.format("Thread %s interrupted.", Thread.currentThread().getName()));
                    break;
                }
                final long now = System.currentTimeMillis();
                /*
                if (now >= mLastBufferFlushTimeMillis + AUDIO_LENGTH_IN_SECONDS * 1000) {
                    flushAudioBuffer();
                    mLastBufferFlushTimeMillis = now;
                } */
                int bytesToRead = mBuffer.length - mBufferPos;
                if (bytesToRead > mBytesPerRead) {
                    bytesToRead = mBytesPerRead;
                }
//                Log.d("deebug", String.format("To read %d bytes, mBufferPos=%d", bytesToRead, mBufferPos));
                final int bytesRead = mAudioRecord.read(mBuffer, mBufferPos, bytesToRead);
//                Log.d("deebug", String.format("got %d bytes", bytesRead));
                if (isHearingSound(mBuffer, mBufferPos, bytesRead)) {
                    mBufferPos += bytesRead;
//                    Log.d("deebug", String.format("got %d bytes, mBufferPos=%d", bytesRead, mBufferPos));
                }
                if (mBufferPos > mBuffer.length) {
                    throw new IllegalStateException("buffer overflow");
                }
                if (mBufferPos == mBuffer.length) {
                    flushAudioBuffer();
                }
            }
            end();
        }

        private void end() {
            mAudioRecord.stop();
            mAudioRecord.release();
        }

        private void flushAudioBuffer() {
            try {
                // write to an external wav file if we have enough samples
                int numSamples = mBufferPos / 2;
                if (numSamples >= SAMPLE_RATE) {
                    writeWavFile();
                    // but always reset the buffer and run classifer on the signals collected in the buffer
                    classifySound();
                    mBufferPos = 0;
                } else  {
                    mCallback.onSoundClassified(String.format(
                            "Timestamp %s: Not enough audio signal samples [%d]",
                            new SimpleDateFormat("HH:mm:ss").format(new Date()),
                            numSamples));
                }
            } catch(IOException ex) {
                Log.e(TAG, ex.toString());
            }
        }

        private void classifySound() {

        }

        private void writeWavFile() throws IOException {
            int numSamples = mBufferPos / 2;
            String externalRootDir = Environment.getExternalStorageDirectory().getPath();
            if (!externalRootDir.endsWith("/")) {
                externalRootDir += "/";
            }
            File parentDir = new File(externalRootDir + "VirtualEar/");
            parentDir.mkdirs();
            String fileName =
                    new SimpleDateFormat("yyyyMMddHHmmss'.wav'").format(new Date());
            File wavFile = new File(parentDir, fileName);
            Log.d(TAG, String.format("Writing to wave file: %s", wavFile.getCanonicalPath()));
            FileOutputStream outputStream = new FileOutputStream(wavFile);

            int numChannels = 1;
            outputStream.write(WavFileHeader.getHeader(SAMPLE_RATE, numChannels, numSamples));
            Log.d(TAG, "writing Wav file with " + numSamples + " samples");
            outputStream.write(mBuffer, 0, mBufferPos);
            outputStream.close();

            //
            mCallback.onSoundClassified(fileName);
        }

        private boolean isHearingSound(byte[] buffer, int start, int len) {
            final int AMPLITUDE_THRESHOLD = 1500;
            for (int i = start; i < start + len - 1; i += 2) {
                // The buffer has LINEAR16 in little endian.
                int s = buffer[i + 1];
//                Log.d("deebug", String.format("isHearingSound %d %d %d", i, s, buffer[i]));
                if (s < 0) s *= -1;
                s <<= 8;
                s += Math.abs(buffer[i]);
                if (s > AMPLITUDE_THRESHOLD) {
                    return true;
                }
            }
            return false;
        }
    }
}
