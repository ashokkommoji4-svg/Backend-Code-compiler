import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://127.0.0.1:8000/ws/compiler/execute/"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            run_data = {
                "action": "run",
                "language": "java",
                "code": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello from Java Simulation\");\n    }\n}"
            }
            await websocket.send(json.dumps(run_data))
            print("Sent run data")
            
            accumulated_output = ""
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    # print(f"Received: {data}")
                    if data['type'] == 'output':
                        accumulated_output += data['data']
                        print(data['data'], end='', flush=True)
                        if 'Name: ' in accumulated_output:
                            print("\nSaw prompt, sending input...")
                            await websocket.send(json.dumps({"action": "input", "data": "Antigravity\r"}))
                            accumulated_output = "" # Clear to avoid double trigger
                    if data['type'] == 'exit':
                        print(f"\nProcess exited with code {data['data']}")
                        break
                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_ws())
