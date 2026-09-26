"""Opt-in real-provider audio smoke test, not a benchmark evaluation.

LIVE_SMOKE=1 .venv/bin/python -m unittest discover -s tests -p test_voice.py
Uses synthetic customer audio and the same AgentSession as the microphone runner.
"""
import asyncio
import os
import unittest
import wave

from livekit.agents import utils
from livekit.agents.voice import io
from livekit.plugins import deepgram

from agent import build_agent
from config import Settings
from tracing import RunTrace


class QueueInput(io.AudioInput):
    def __init__(self):
        super().__init__(label="smoke-customer")
        self.queue = asyncio.Queue()

    async def __anext__(self):
        return await self.queue.get()


class FileOutput(io.AudioOutput):
    def __init__(self, path):
        super().__init__(label="smoke-recording", capabilities=io.AudioOutputCapabilities(pause=False),
                         sample_rate=24000)
        self.file = wave.open(str(path), "wb")
        self.file.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
        self.samples = 0
        self.segment_samples = 0
        self.finished = asyncio.Event()

    async def capture_frame(self, frame):
        await super().capture_frame(frame)
        self.file.writeframesraw(bytes(frame.data))
        self.samples += frame.samples_per_channel
        self.segment_samples += frame.samples_per_channel

    def flush(self):
        super().flush()
        if self.segment_samples:
            self.on_playback_finished(playback_position=self.segment_samples / 24000, interrupted=False)
            self.segment_samples = 0
            self.finished.set()

    def clear_buffer(self):
        if self.segment_samples:
            super().flush()
            self.on_playback_finished(playback_position=self.segment_samples / 24000, interrupted=True)
            self.segment_samples = 0


@unittest.skipUnless(os.getenv("LIVE_SMOKE") == "1", "Opt-in: consumes provider allowance")
class VoiceSmokeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await self.enterAsyncContext(utils.http_context.open())

    async def test_audio_to_tools_to_audio(self):
        settings = Settings.load()
        trace = RunTrace(settings.task_id)
        session, agent, benchmark = build_agent(settings, trace)
        source = QueueInput()
        output = FileOutput(trace.directory / "agent.wav")
        session.input.audio = source
        session.output.audio = output
        errors = []
        session.on("error", lambda event: errors.append(event))
        customer_tts = deepgram.TTS(model="aura-2-asteria-en", sample_rate=24000)
        text = ("Please look up my order W two three seven eight one five six. "
                "For authentication, my first name is spelled Y U S U F, "
                "my last name is spelled R O S S I, and my zip code is one nine one two two. "
                "Please tell me what items are in this order.")
        trace.save("smoke_input.json", {"text": text, "mode": "synthetic-audio-smoke", "is_evaluation": False})
        try:
            # Use the SDK's normal session pipeline with a test audio source and sink.
            await session.start(agent=agent, record=False)
            async with customer_tts.synthesize(text) as speech:
                frames = [event.frame async for event in speech]
            with wave.open(str(trace.directory / "customer.wav"), "wb") as f:
                f.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
                for frame in frames:
                    f.writeframesraw(bytes(frame.data))
            chunker = utils.audio.AudioByteStream(sample_rate=24000, num_channels=1, samples_per_channel=480)
            pcm = b"".join(bytes(frame.data) for frame in frames)
            # Leading/trailing silence lets the production VAD detect natural turn boundaries.
            pcm = bytes(24000) + pcm + bytes(24000 * 2 * 2)
            for frame in chunker.write(pcm) + chunker.flush():
                source.queue.put_nowait(frame)
                await asyncio.sleep(frame.samples_per_channel / frame.sample_rate)
            await asyncio.wait_for(output.finished.wait(), timeout=240)
            # Initial speech can precede tools. Wait for the entire tool/reply turn.
            speech = session.current_speech
            if speech is not None:
                await asyncio.wait_for(speech.wait_for_playout(), timeout=240)
            self.assertGreater(output.samples, 2400)
            self.assertFalse([e for e in errors if not getattr(e.error, "recoverable", False)],
                             "Unrecovered provider errors occurred; inspect the run events")
        finally:
            await session.aclose()
            for provider in (session.stt, session.llm, session.tts):
                await provider.aclose()
            await customer_tts.aclose()
            trace.finish(session, benchmark)
            output.file.close()
            print(f"Smoke evidence: {trace.directory}")
        import json
        events = [json.loads(line) for line in (trace.directory / "events.jsonl").read_text().splitlines()]
        self.assertTrue(any(e["type"] == "user_input_transcribed" and e["data"]["is_final"] for e in events))
        tool_results = [e for e in events if e["type"] == "tool_finished"]
        self.assertTrue(tool_results, "No official retail tool returned a result")
        self.assertTrue(any(
            e["type"] == "conversation_item_added"
            and e["data"]["item"].get("role") == "assistant"
            and e["time"] > tool_results[-1]["time"]
            for e in events
        ), "No assistant response after the tool result")
        # Tool errors are legitimate observations, not plumbing failures or task passes.
        trace.save("smoke_result.json", {
            "audio_roundtrip": True, "is_evaluation": False,
            "tool_results": [e["data"] for e in tool_results],
        })


if __name__ == "__main__":
    unittest.main()
