import asyncio
import websockets

async def test_ws():
    uri = "ws://localhost:8000/api/voice/stream"
    try:
        async with websockets.connect(uri) as websocket:
            # Receive greeting
            greeting = await websocket.recv()
            print(f"Received: {greeting}")
            
            # Send message
            await websocket.send("Hello")
            print("Sent: Hello")
            
            # Receive response
            response = await websocket.recv()
            print(f"Received: {response}")
    except Exception as e:
        print(f"Connection failed: {e}")

asyncio.run(test_ws())
