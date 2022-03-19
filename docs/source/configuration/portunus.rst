Portunus Config
================

Portunus can be configured in a few ways

CONSTANCE
---------

A few settings can be updated in the Admin dashboard. They are shown below with a brief description

MAP_COORDINATES
    Map coordinates for the platform, agents, and access domains can be set as follows where {pk} is a placeholder from Primary Key of the object.

    .. code-block:: json

        {
            "PORTUNUS": [lon, lat],
            "AGENT_{pk}": [lon, lat],
            "ACCESS_DOMAIN_{pk}": [lon, lat]
        }


BIRTHRIGHT_ACCESS
    "Birthright" Access defines Access-Roles that are granted to users based on user attributes.
    It is configured as a dictionary like below

    .. code-block:: json

        {
            "Access-Role Name": [
                {required_attributes},
                {alternative_attributes}
            ]
        }
