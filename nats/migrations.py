import asyncio
import nats

from datetime import timedelta

from nats.js import JetStreamManager
from nats.js.api import StreamConfig, RetentionPolicy, StorageType, DiscardPolicy

async def create_stream():
    nc = await nats.connect("nats://admin:securepassword@localhost:4222")
    js = nc.jetstream()

    try:
        await js.add_stream(
        config=StreamConfig(
            name="mailing",
            subjects=[
                "mailing.*.send.*.logs",
                "mailing.*.over",
                "mailing.*.load",
                "mailing.*.send.*"
            ],
            retention=RetentionPolicy.LIMITS,  
            storage=StorageType.FILE,
            max_msgs=10_000,
            discard=DiscardPolicy.NEW,
            num_replicas=1,
            max_bytes=10_485_760,
            max_msgs_per_subject=1,
            max_age=timedelta(days=14).seconds
        )
    )
        print("Stream 'mailing' создан!")
    except Exception as e:
        print(f"Ошибка: {e}")

    await nc.close()

if __name__ == "__main__":
    asyncio.run(create_stream())