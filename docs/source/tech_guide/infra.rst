Infrastructure
^^^^^^^^^^^^^^

Portunus largely consists of two parts; infrastructure management and RBAC.

This guide addresses: how does Portunus manage infrastructure?

AccessDomain
------------

AccessDomains exist and function under both Infrastructure and RBAC enforcement.
This document will consider the former (Infrastructre).

Each AccessDomain will contain at leaat one AccessHost (digital endpoints) which
is associated with a single Agent.
However, AccessHosts in a particular AccessDomain do not need to use the same Agent.
I.e. They may consist of two subsets of AccessHosts which are reachable from two
different Agents (especially in the case of DR).

The AccessDomain has a few important settings, discussed below:

AgentInterface
    This defines the Interface that should be used by ANY Agent when interacting
    with an AccessHost under this AccessDomain
Properties
    This is a JSON object which can store arbitrary parameters - usually to
    support evolving (but not critical) functionality.
    These are also often used to store data which can be used to tailor how
    AgentInterfaces function.
user_source_authority
    This boolean defines if a collection of the AccessDomain can create a User from
    each collected access-account. When True, **user_account_mapping** is used to
    determine how ther username should be extracted from each account name.
user_account_mapping
    A string definining a pattern so that **username** can be extracted from account name.
    The template must contain ``{username}`` (e.g. ``u_{username}`` would get 'dan' from 'u_dan')

Available Properties
~~~~~~~~~~~~~~~~~~~~

Here are a list of properties that can be set under an AccessDomain and what they are for.

.. code-block:: json

    {
        "collection_create_access_accounts": true,
        "collection_create_access_items": true,
        "account_user_upsert_properties": {}
    }

collection_create_access_accounts
    Determine if Accounts are created in Portunus from the data collected
    in an AccessDomain
collection_create_access_items
    Determine if Access-Items are created from the data collected in an AccessDomain
account_user_upsert_properties
    A dict of ``'key': 'property.path'`` that sets ``key`` in the User
    properties using the value retrieved in ``property.path`` of the Account

    IOU: An example that makes sense of that

AccessHost
----------

An AccessHost represents a unique combination of an AccessDomain, a particular Agent, and a digital host (often a server).

AccessHosts are discovered using a HostScanDefinition assigned to an Agent.
The HostScanDefinition simply defines a network range (reachable from the Agent)
and a list of ports that must be open (or `listening`) for the Agent to consider the Host as alive.

The AccessDomain specifies some important properties including which AgentInterface to use when reaching the Host.

A Host (or server) may be represented by more than one AccessHost.

If the AccessHost is Writeable, provisioning instructions will be sent to the AccessHost by Portunus.
Otherwise, it is considered read-only; provisioning instructions will not be sent, but changes to Access are expected to occur (i.e. in the case of DR replicated systems).

How is Access-data collected?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Data collection is a core requirement of Access Management.
If you can't collect and verify Access is set up appropriately, Access can't be reliably enforced.

Agent
------------

Agents are the pieces of Portunus that talk to external infrastructure.
So they are very important, but also very simple to set-up.

How to set-up a new Agent?
~~~~~~~~~~~~~~~~~~~~~~~~~~

0. Start up a new Agent and set a unique Queue name for it to run with
1. In the Administrator dashboard, go to Id_infra > Agents, and add a new Agent
2. Be sure to carefully set the following:
    a. Agent Name (this should match the Queue name ideally)
    b. If the Queue name is different, set the Queue name override appropriately
3. Finally, in the Agent List view in Admin, select any Agents you want to **Link**,
and run the 'Link Agent to Portunus' command.
4. If they were connected successfully, they should be marked as Active and have an updated Link-Date
