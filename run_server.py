# import uvicorn
# import socket


# def get_local_ip():
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     try:
#         # doesn't even have to be reachable
#         s.connect(('10.255.255.255', 1))
#         IP = s.getsockname()[0]
#     except Exception:
#         IP = '127.0.0.1'
#     finally:
#         s.close()
#     return IP


# if __name__ == "__main__":
#     host = get_local_ip()
#     print(f"Starting server on: http://{host}:8000")
#     uvicorn.run("main:app", host=host, port=8000, reload=True)


import socket

import uvicorn


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == "__main__":
    host = get_local_ip()
    print(f"Starting server on: http://{host}:8000")
    
    uvicorn.run("main:app", host=host, port=8000, reload=True,)


# 2. **Trigger the Breakpoint**: Perform the action that will trigger the `update_record` function. When the code execution reaches `pdb.set_trace()`, it will pause, and you will see a `(Pdb)` prompt in your terminal.

# 3. **Interact with the Debugger**: At the `(Pdb)` prompt, you can use various commands to inspect variables and control the execution flow. Some useful commands include:
#    - `n` (next): Execute the next line of code.
#    - `c` (continue): Continue execution until the next breakpoint.
#    - `q` (quit): Exit the debugger.
#    - `p variable_name`: Print the value of a variable.
