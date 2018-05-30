OpenNMS
=========

## NOTE: This readme is currently meant to provide BASIC understanding of the role.  It needs to be rewritten "properly".

Installs/configures/updates OpenNMS on RedHad/CentOS.

This role will perform a complete clean installation of the latest version of OpenNMS on an enterprise linux server.  Additionally, this role will perform customizations and updates on an existing instance.

This role is built in such a way that you can run it via the playbook included at the root of the role.  When running at the command line you can execute the playbook along with `--extra-vars 'variable_host=<inventory-hostname>`

Requirements
------------

You must have the OpenNMS repo already installed on the system.  You also need to have a repo that contains PostgreSQL (either Centos-Base or a PostgreSQL specific repo).

Role Variables
--------------

Some of the variables are listed/explained are listed below.  See `defaults/main` to see the complete list.

    mode: ''

Define "mode" either in the playbook or on the command line (--extra-vars) along with 1 of the 4 mode options (install | upgrade | restart_opennms | restart_all).  By default the role will only update the opennms config files and the postgres users/passwords.  Running with "install" adds a complete install of OpenNMS/PostgreSQL.  Running with "update" will shut down OpenNMS before installing software.  Running with "restart_opennms" bypasses software install but will restart OpenNMS.  Running with "restart_all" restarts OpenNMS and PostgreSQL.

    opennms_package_version: ''

By default the role will install the latest version of OpenNMS in the installed package repository.  Specifying "opennms_package_version" along with a hyphen and package version number (i.e. "-21.0.2-1") will install that particular version of OpenNMS.

    opennms_java_path_method: runjava

By default the role will run `bin/runjava -s` to setup your java environment.  If deisred, you can set the variable "opennms_java_path" to something specific and then set opennms_java_path_method" to "custom" and the role will write a custom "java.conf".

When you have 

Dependencies
------------

None.

Example Playbook
----------------

. . . todo . . .

License
-------

MIT / BSD

Author Information
------------------

This role was created in 2018 by Bill Nelson
