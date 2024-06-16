import os
import logging, verboselogs
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
from threading import Thread
from queue import Queue

load_dotenv()

is_finals = []
last_utter = ""


class interupt():
    def __init__(self):
        API_KEY = os.getenv("DEEPGRAM_API_KEY")
        config = DeepgramClientOptions(options={"keepalive": "true"})
        deepgram = DeepgramClient(API_KEY, config)
        self.dg_connection = deepgram.listen.live.v("1")
        self.options = LiveOptions(
            model="nova-2-drivethru",
            language="en",
            encoding="linear16",
            sample_rate=16000,
            channels=1,
            interim_results=True,
            utterance_end_ms="1000",
            endpointing=100,
        )

        addons = {
            "no_delay": "true"
        }

        # Initialize
        self.initialize()
        self.dg_connection.start(self.options, addons=addons)
        self.speech_final = ""
        self.vad_indicate = 0
        self.buffer_queue = Queue()

        # Start a thread to process buffer data
        self.buffer_thread = Thread(target=self.process_buffer)
        self.buffer_thread.daemon = True
        self.buffer_thread.start()

    def initialize(self):
        self.dg_connection.on(LiveTranscriptionEvents.Transcript, self.on_message)



    def on_message(self, it, result, **kwargs):
        global is_finals, last_utter
        sentence = result.channel.alternatives[0].transcript
        if len(sentence) == 0:
            return
        if result.is_final:
            is_finals.append(sentence)
            if result.speech_final:
                utterance = " ".join(is_finals)
                last_utter = utterance
                is_finals = []
            else:
                pass
        else:
            if self.vad_indicate == 0:
                self.vad_indicate = 1
                print("***interupted***")

    def streaming_data(self, buffer):
        self.buffer_queue.put(buffer)
        return self.speech_final

    def process_buffer(self):
        while True:
            buffer = self.buffer_queue.get()
            if buffer is None:
                break
            self.dg_connection.send(buffer)
            self.buffer_queue.task_done()

    def close_connection(self):
        self.buffer_queue.put(None)
        self.buffer_thread.join()
        self.dg_connection.finish()

