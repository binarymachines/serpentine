
import repoze.who
import repoze.what

from repoze.what.plugins.sql import SqlGroupsAdapter
from your_model import User, Group, DBSession

groups = SqlGroupsAdapter(Group, User, DBSession)


def add_auth(app):
    """
    Add authentication and authorization middleware to the ``app``.

    :param app: The WSGI application.
    :return: The same WSGI application, with authentication and
        authorization middleware.

    People will login using HTTP Authentication and their credentials are
    kept in an ``Htpasswd`` file. For authorization through repoze.what,
    we load our groups stored in an ``Htgroups`` file and our permissions
    stored in an ``.ini`` file.

    """

    from repoze.who.plugins.basicauth import BasicAuthPlugin
    #from repoze.who.plugins.htpasswd import HTPasswdPlugin, crypt_check

    from repoze.what.middleware import setup_auth
    from repoze.what.plugins.sql import SQLPermissionsAdapter
    

    # Defining the group adapters; you may add as much as you need:
    groups = {'all_groups': SqlGroupsAdapter(Group, User, DBSession)}

    # Defining the permission adapters; you may add as much as you need:
    permissions = {'all_perms': SqlPermissionsAdapter(Permission, Group, DBSession)}

    # repoze.who identifiers; you may add as much as you need:
    basicauth = BasicAuthPlugin('Private web site')
    identifiers = [('basicauth', basicauth)]

    # repoze.who authenticators; you may add as much as you need:
    htpasswd_auth = HTPasswdPlugin('/path/to/users.htpasswd', crypt_check)
    authenticators = [('htpasswd', htpasswd_auth)]

    # repoze.who challengers; you may add as much as you need:
    challengers = [('basicauth', basicauth)]

    app_with_auth = setup_auth(
        app,
        groups,
        permissions,
        identifiers=identifiers,
        authenticators=authenticators,
        challengers=challengers)
    return app_with_auth
