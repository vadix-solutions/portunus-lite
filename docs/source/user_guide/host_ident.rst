Host Identification
^^^^^^^^^^^^^^^^^^^^^^^^

Host identification is the process used to scan a network from a particular Agent and determine what Hosts are reachable.

Hosts are any computer system that can listen on a network (so that the Agent can reach it).

Host identification involves scanning a Network range for computer systems which are listening on a particular set of ports (often just one).

Identification vs Discovery
---------------------------
Identification is purely the scanning and recording of Hosts. Portunus does not inspect or analyze Hosts to determine any further details (the OS for example).
Although arbitrary data (e.g. OS, OS-version, uptime, etc) can be collected through a Collection, this is the collection of specific details as opposed to
existing "Service Discovery" systems which will attempt to use a large number of built-in heuristics to discover and organize infrastructure.

For more information about collecting Host information, please refer to the Interface section :ref:`interface-capabilities`
