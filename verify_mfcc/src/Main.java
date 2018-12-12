import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOError;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.text.SimpleDateFormat;
import java.util.Date;

import be.tarsos.dsp.AudioDispatcher;
import be.tarsos.dsp.AudioEvent;
import be.tarsos.dsp.AudioProcessor;
import be.tarsos.dsp.mfcc.MFCC;
import be.tarsos.dsp.io.TarsosDSPAudioFormat;
import be.tarsos.dsp.io.UniversalAudioInputStream;

public class Main {

    public static void main(String[] args) throws IOException {
        new Main().run(args[0]);
    }

    void run(String wavFile) throws IOException {

        final int SAMPLE_RATE = 22050;
        final int N_MFCC = 40;
        final int FREQUENCY_MIN = 0;
        final int FREQUENCY_MAX = SAMPLE_RATE/2;
        final int samplesPerFrame = SAMPLE_RATE / 25;
        final int framesOverlap = samplesPerFrame / 2;
        final int n_mels = 128;

        final float[] mfcc_avg = new float[N_MFCC];

        final MFCC mfcc = new MFCC(
                samplesPerFrame,
                SAMPLE_RATE,
                N_MFCC,
                n_mels,
                FREQUENCY_MIN,
                FREQUENCY_MAX);

        for(int i = 0; i < N_MFCC; i++) {
            mfcc_avg[i] = 0;
        }
        System.out.println("processing wavFile: " + wavFile);

        InputStream inStream = new FileInputStream(wavFile);
        TarsosDSPAudioFormat tarsosDSPAudioFormat = new TarsosDSPAudioFormat(
                SAMPLE_RATE, 16, 1, true, false);
        UniversalAudioInputStream tarsosAudioInputStream = new UniversalAudioInputStream(
                inStream, tarsosDSPAudioFormat);
        tarsosAudioInputStream.skip(44); // skip the size of wav header

        AudioDispatcher dispatcher = new AudioDispatcher(
                tarsosAudioInputStream, samplesPerFrame, framesOverlap);

        final int[] iFrames = new int[1];
        iFrames[0] = 0;
        dispatcher.addAudioProcessor(new AudioProcessor() {
            @Override
            public boolean process(AudioEvent audioEvent) {
                mfcc.process(audioEvent);
                float[] xx = mfcc.getMFCC();
                if (iFrames[0] < 10) {
                    System.out.print("deebug: mfcc at iFrame=" + iFrames[0]);
                    for (int i = 0; i < 3; i++) {
                        System.out.print(" " + xx[i]);
                    }
                    System.out.println();
                }
                for(int i = 0; i < N_MFCC; i++) {
                    mfcc_avg[i] += xx[i];
                }
                iFrames[0]++;
                return true;
            }

            @Override
            public void processingFinished() {
                for (int i = 0; i < N_MFCC; i++) {
                    mfcc_avg[i] /= iFrames[0];
                }
            }
        });
        //System.out.println("before iframes=" + iFrames[0]);
        dispatcher.run();
        //System.out.println("iframes=" + iFrames[0]);
    }
}
