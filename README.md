# SMPX_RP3
- this program caters for multirotor drone serial problems
- the autopilot (skyfront) needs to prioritize silvus radio link, thus need to be connected to the serial of silvus radio when it is available
- also, as a backup / redundant link, it needs to connect to the MicroHard radio serial connection, when link of the silvus radio is not available
- the program, listen from the autopilot, and relay the message back using priority link
