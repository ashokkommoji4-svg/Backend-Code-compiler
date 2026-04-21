import asyncio
import websockets
import json

async def test_compiler():
    uri = "ws://127.0.0.1:8000/ws/compiler/execute/"
    print(f"Connecting to {uri}...", flush=True)
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket", flush=True)
            
            # Send run action
            code = 'name = input("Name? "); print(f"Hello {name}")'
            print(f"Sending code: {code}", flush=True)
            await websocket.send(json.dumps({
                "action": "run",
                "language": "python",
                "code": code
            }))
            
            buffer = ""
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    char = data.get('data')
                    print(f"Received char: {repr(char)}", flush=True)
                    
                    if data.get("type") == "output":
                        buffer += char
                        if "Name?" in buffer:
                            print(f"Prompt detected in buffer: {repr(buffer)}", flush=True)
                            print("Sending input: Antigravity", flush=True)
                            await websocket.send(json.dumps({
                                "action": "input",
                                "data": "Antigravity\n"
                            }))
                            buffer = "" # Clear buffer after sending input
                    
                    if data.get("type") == "exit":
                        print(f"Process exited with code {data.get('data')}", flush=True)
                        break
                except websockets.ConnectionClosed:
                    print("Connection closed by server", flush=True)
                    break
    except Exception as e:
        print(f"Connection failed: {e}", flush=True)

if __name__ == "__main__":
    try:
        asyncio.run(test_compiler())
    except Exception as e:
        print(f"Error: {e}")
