# Remote Calls
We are using a GRPC server to structure RPC calls to our program.
Protobuf is a great industry standard for serializing data. This also obviates rolling our own TCP server and parsing bytes of the line. If ya got an issue with this contact Josh. 

## Setup 
* this should already be covered by installing `pip3 install requirements.txt` within your venv but: `python -m pip install grpcio-tools` is explicitly the package we want
* from top level Makefile you can run `make gen_grpc` to get build artifacts needed for runtime