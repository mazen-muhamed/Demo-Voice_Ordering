import asyncio
from types import SimpleNamespace

from pipecat.frames.frames import OutputAudioRawFrame
from serializer import FreeSwitchFrameSerializer


async def main():
    s = FreeSwitchFrameSerializer()
    await s.setup(SimpleNamespace(audio_in_sample_rate=16000))

    # 20 ms of 8 kHz silence (320 bytes) -> roughly double at 16 kHz
    frame = await s.deserialize(bytes(320))
    print("in :", frame.sample_rate, len(frame.audio), "bytes")

    # 20 ms of 16 kHz silence (640 bytes) -> roughly half at 8 kHz
    out = await s.serialize(
        OutputAudioRawFrame(audio=bytes(640), sample_rate=16000, num_channels=1)
    )
    print("out:", len(out), "bytes")


asyncio.run(main())