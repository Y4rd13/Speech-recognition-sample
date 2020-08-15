import os
import time
import logging
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks
from pydub.silence import split_on_silence
import multiprocessing
import pdb


confidence_value = float


def chunks_speech_recognition(filename='audio.wav', format='wav',
                              min_silence_len=500, silence_tresh=-16, duration=10,
                              adjust_ambient_noise=False):

    accumulative = []

    if format == 'wav':
        myaudio = AudioSegment.from_wav(filename)
    else:
        myaudio = AudioSegment.from_file(filename, format=format)

    start_making_chunks = time.time()
    print('Making chunks...')
    # Make chunks of one sec
    # pydub calculates in millisec

    #chunks = make_chunks(myaudio, chunk_length=4000)
    chunks = split_on_silence(audio_segment=myaudio,
                              # must be silent for at least 0.5 seconds
                              # or 500 ms. adjust this value based on user
                              # requirement. if the speaker stays silent for
                              # longer, increase this value. else, decrease
                              min_silence_len=min_silence_len,

                              # consider it silent if quieter than -16 dBFS
                              # adjust this per requirement
                              silence_thresh=silence_tresh
                              )

    elapsed_making_chunks = time.time() - start_making_chunks
    print('Elapsed time making chunks: {0}'.format(elapsed_making_chunks))
    print(chunks)

    # Handle Errors and update response with try Error
    response = {
        'success': True,
        'error': None,
        'transcription': None
    }

    limit, MULT = 1, 5
    for i, chunk in enumerate(chunks):
        # Silence chunk: duration specified in milliseconds
        chunk_silent = AudioSegment.silent(duration=duration)

        # add silence beginning & end of audio chunk
        # it doesn't seem abruptly sliced
        # less chunck_silent could improve the speed, but decrease the accuracy
        audio_chunk = chunk_silent + chunk + chunk_silent
        chunk_name = 'chunk{0}.wav'.format(i)
        print('exporting', chunk_name)

        audio_chunk.export(out_f=chunk_name,
                           bitrate='192k', format=format)
        filename = ('chunk' + str(i) + '.wav')

        print('Processing chunk: ' + str(i))

        r = sr.Recognizer()
        with sr.AudioFile(filename) as source:
            # could increase accuracy, but decrease speed and accuracy in some parts
            if adjust_ambient_noise:
                r.adjust_for_ambient_noise(source)
            audio = r.listen(source)
        try:
            if i == limit * MULT:
                with open('result.txt', 'a') as f:
                    f.write('\n')
                limit += 1
            else:
                msg = r.recognize_google(
                    audio_data=audio, language='en-US', show_all=False)
                with open('result.txt', 'a') as f:
                    f.write(' ' + msg)

                response['transcription'] = msg

                # Confidence will be just to test purposes, delete for decrease elapsed time
                confidence = r.recognize_google(
                    audio_data=audio, language='en-US', show_all=True)
                with open('confidence.txt', 'a') as fh:
                    fh.write(str(confidence))
                    fh.write('\n')
        except sr.UnknownValueError:
            response['error'] = logging.debug(
                'Speech recognition could not understand the audio')
        except sr.RequestError as e:
            response['success'] = False
            response['error'] = logging.debug(
                'API is unreachable. Coult not request results from Speech Recognition service: {0}'.format(e))
        os.remove(path=chunk_name)
        print(response)

        # accumulative confidence values
        accumulative.append(confidence_values(confidence=confidence))
        aux_average_confidence = sum(accumulative) / len(accumulative)
        print('\t\tAverage confidence: {0}'.format(aux_average_confidence))

    # Average confidence value
    total_confidence = sum(accumulative) / len(accumulative)
    print(total_confidence)
    with open('confidence.txt', 'a') as fc:
        fc.write('\n')
        fc.write(str(total_confidence))


def confidence_values(confidence):
    global confidence_value
    confidence = [i for i in (list(confidence.values())) if type(i) != bool]
    for j in confidence:
        for k in j:
            lst = list(k.values())
            if len(lst) >= 2:
                confidence_value = lst[1] * 100
    return float("%.2f" % confidence_value)


if __name__ == "__main__":
    start_time = time.time()

    # 91.99% of accuracy
    chunks_speech_recognition(silence_tresh=-60,
                              min_silence_len=1000)

    elapsed_time = time.time() - start_time
    print('\nElapsed time: {0}'.format(elapsed_time))
    with open('confidence.txt', 'a') as f:
        f.write(str(elapsed_time))
