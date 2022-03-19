Access Domains
^^^^^^^^^^^^^^^^^^^

Access Domains are groups of Hosts which have consistent Access (i.e. the same accounts, items and memberships).
This is an important part of how Portunus operates and reflects modern infrastructure which scales.

Access Collection
-----------------

Access-data is the data collected from Hosts which represent the Accounts/Access-Items/Memberships on remote systems.
Portunus uses this data to determine the state of access on remote systems.
Access-data Collection (or Access Collection) is where one or more Agents connect to all Hosts in an Access Domain, retrieve the Access-data, and have it ingested by Portunus.

When the data is collected from the hosts, the latest record is always stored in the 'AccessHost' managed by Portunus and can be queried/inspected as desired.

Once the data has been stored in Portunus, it is analyzed for consistency checks before the data is ingested;
this is where the various Accounts/Access-Items/Memberships are updated in Portunus using the collected data.

Users with the ``Access Manager`` authorization can trigger a **Data Collection**.

Consistency
~~~~~~~~~~~

Consistency of access data is measured across all Hosts in the Access Domain.
The consistency of account/item/membership data is measured by the ratio of hosts that are returning the exact same data.

Any attributes that are expected to vary among Hosts can be set under ``extended attributes`` in each AccessDomain, and are excluded from consistency checks.

Healing
~~~~~~~

When Access-data is collected, any Hosts which deviate from the common  hosts in an AccessDomain are identified, and the AccessObject (account, item or membership) can be "Healed",
where it is reprovisioned to be made consistent with other Hosts.
