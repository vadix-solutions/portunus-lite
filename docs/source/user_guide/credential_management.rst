Credential Management
^^^^^^^^^^^^^^^^^^^^^

All credentials in Portunus are safely stored using Hashicorp Vault. Portunus is deployed with a Vault, but can easily use an existing Vault if available.

Password Policies
-----------------

// Policies can be defined in the vault and used for automatic password rotation

Portunus leverages the agent component to manage passwords across many of the AccessDomains with which it is associated. It can enforce password policies 
specified for the AccessDomain, which can include requirements for length, complexity, and other internal requirements.To manage passwords across AccessDomain, 
you must configure both Portunus and the applications on which you are going to manage passwords. Password management is further governed by the capabilities 
of the interface in use for each Access domain as some specific applications/hosts may have a complex set of requirements.

Account password rotation
-------------------------

Accounts managed by Portunus can opt-in for password rotation. This is different from the built-in password rotation service offered by Vault as it uses the
agents and interfaces defined by Portunus, thereby extending that functionality for absolutely all Hosts and endpoints (even globally distributed legacy mainframes).
