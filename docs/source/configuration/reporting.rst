Reporting
================

Reports and Data exploration are built into Portunus and can be configured by an Operator with appropriate permissions.

Below are two sample SQL queries that can be used to retrieve data from the AccessHosts collected by a single AccessDomain in Portunus.

Sample Data Exploration SQL queries
-----------------------------------

.. code-block:: sql

    SELECT
    CONCAT(host.address, '/', entry->>'username') AS account_name,
    entry->'UID' as UID, entry->'GID' as GID, entry->'username' as uname
    FROM id_infra_AccessHost host
    left JOIN jsonb_each(host.collection_data->'accounts') as t(uid, entry) on true
    WHERE host.access_domain_id in (1)


.. code-block:: sql

    SELECT
    CONCAT(host.address, '/', entry->>'groupname') AS group_name,
    entry->'GID' as GID
    FROM id_infra_AccessHost host
    left JOIN jsonb_each(host.collection_data->'access_items') as t(ai_name, entry) on true
    WHERE host.access_domain_id in (1)
