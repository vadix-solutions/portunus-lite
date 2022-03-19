Agent interfaces
================

Agent-Interfaces are used by the Agents of Portunus to communicate with Hosts. For instance, a built-in Unix interface is provided for communicating with Unix hosts.

It is the responsibility of the Interface to determine the 'Access' on remote Hosts (e.g. what an Account, Access-Item, and Membership represents).

Interfaces can be deployed to Agents via Portunus, or they can be hosted directly on the Agents.
However, it is important to note that if Agent-Interfaces are deployed inconsistently (i.e. different versions on different Agents), it will likely cause issues.
