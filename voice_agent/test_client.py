import asyncio, wave, websockets

async def main():
    w = wave.open("test8k.wav")
    assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (8000, 1, 2)
    pcm = w.readframes(w.getnframes())

    async with websockets.connect("ws://localhost:8765/ws") as ws:
        async def recv():
            async for msg in ws:
                print("connected") 
                print("got", type(msg).__name__, len(msg))
        r = asyncio.create_task(recv())

        await asyncio.sleep(2)                    # let the pipeline finish starting
        for i in range(0, len(pcm), 320):         # 20 ms chunks, real-time pace
            await ws.send(pcm[i:i + 320])
            await asyncio.sleep(0.02)
        for _ in range(100):                      # 2 s silence so VAD ends the turn
            await ws.send(bytes(320))
            await asyncio.sleep(0.02)

        await asyncio.sleep(10)                   # wait for the reply
        print("closed:", ws.close_code)
        r.cancel()
asyncio.run(main())