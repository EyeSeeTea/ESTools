#!/usr/bin/env python

"""
Clone a dhis2 installation from another server.
"""

import sys
import os
import time
import json
import requests
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import dhis2api
import process

TIME = time.strftime('%Y-%m-%d_%H:%M')


def main():
    cfg = get_config()
    war_path = '%s/webapps/%s' % (cfg['server_dir'], cfg['war'])
    api_config = cfg["api_local"]
    api = dhis2api.Dhis2Api(api_config["url"], api_config["username"], api_config["password"])

    stop_tomcat(cfg['server_dir'])
    backup_db(backups_dir=cfg['backups_dir'], db_local=cfg['db_local'])
    backup_war(backups_dir=cfg['backups_dir'], war_path=war_path)
    get_war(war_path)
    get_db(db_local=cfg['db_local'], db_remote=cfg['db_remote'])
    start_tomcat(cfg['server_dir'])
    wait_for_server(api)
    postprocess(api, cfg["postprocess"])


def wait_for_server(api, timeout=300):
    start_time = time.time()
    print('Check active API: %s' % api.api_url)

    while True:
        try:
            api.get("/me")
        except requests.exceptions.ConnectionError:
            if time.time() - start_time > timeout:
                raise RuntimeError("Timeout: could not connect to the API")
            time.sleep(1)
        else:
            break

def postprocess(api, postprocess_config):
    enable_users_config = postprocess_config.get("enableUsers", {})
    add_users_config = postprocess_config.get("addUserRoles", [])

    process.enable_users(api,
        usernames=enable_users_config.get("usernames", []),
        user_group_names=enable_users_config.get("userGroups", []))

    process.add_user_roles(api, add_users_config)

def get_config():
    "Return dict with the options read from configuration file"
    args = get_args()
    print('Reading from config file %s ...' % args.config)
    with open(args.config) as fd:
        config = json.load(fd)
    check_config(config)
    return config


def get_args():
    "Return arguments"
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    parser.add_argument('--config', default='dhis2_clone.json',
                        help='file with configuration')
    # We may have more fancy stuff in the future. For the moment it's
    # just the config file (and a nice "-h" option).
    return parser.parse_args()


def check_config(cfg):
    "Assert all the options in configuration exist and have reasonable values"
    for option in ['backups_dir', 'server_dir', 'db_local', 'db_remote', 'war', 'api_local', 'postprocess']:
        assert option in cfg, 'Missing option "%s"' % option
    for path in ['backups_dir', 'server_dir']:
        assert os.path.isdir(cfg[path]), \
            '%s is not a directory: %s' % (path, cfg[path])
    assert (os.path.isfile(cfg['server_dir'] + '/bin/startup.sh') and
            os.path.isfile(cfg['server_dir'] + '/bin/shutdown.sh')), \
            ('%s should be a directory with start/stop scripts in bin: %s' %
             ('server_dir', cfg['server_dir']))
    for uri in ['db_local', 'db_remote']:
        assert is_good_db_uri(cfg[uri]), 'bad %s uri: %s' % (uri, cfg[uri])
    assert cfg['war'].endswith('.war'), \
        'war file does not end with .war: %s' % cfg['war']


def is_good_db_uri(uri):
    return uri.startswith('postgresql://')  # we could be way more sophisticated


def run(cmd):
    print(magenta(cmd))
    ret = os.system(cmd)
    if ret != 0:
        sys.exit(ret)


def magenta(txt):
    return '\x1b[35m%s\x1b[0m' % txt


def start_tomcat(server_path):
    run('%s/bin/startup.sh' % server_path)


def stop_tomcat(server_path):
    run('%s/bin/shutdown.sh' % server_path)


def backup_db(backups_dir, db_local):
    backup_file = '%s/dhisntd_%s.dump' % (backups_dir, TIME)
    run("pg_dump --file %s --format custom --clean '%s'" % (backup_file,
                                                            db_local))


def backup_war(backups_dir, war_path):
    backup_file = '%s/dhis2_%s.war' % (backups_dir, TIME)
    run('cp %s %s' % (war_path, backup_file))


def get_war(war_path):
    run('scp prod:%s %s' % (war_path, war_path))


def get_db(db_local, db_remote):
    empty_db(db_local)

    exclude = ("--exclude-table 'aggregated*' --exclude-table 'analytics*' "
                  "--exclude-table 'completeness*' --exclude-schema sys")
    dump = "pg_dump -d '%s' --format custom --clean %s" % (db_remote, exclude)
    user = db_local[len('postgresql://'):].split(':')[0]
    run("ssh prod %s | pg_restore -d '%s' --no-owner --role %s" %
        (dump, db_local, user))


def empty_db(db):
    # TODO.

    # If we had permissions, it would be as simple as a
    #   DROP DATABASE db
    #   CREATE DATABASE db
    # but we may not have, in which case we need something like the
    # following:
    #
    #   user = ...
    #   sql_query = ("SELECT tablename FROM pg_tables "
    #                "WHERE tableowner='%s' AND schemaname='public'" % user)
    #   run("echo %s | psql -d '%s' --tuples-only > %s" %
    #       (sql_query, db, tmpfile))
    #   for line in open(tmpfile):
    #       table = line.strip()
    #       sql_cmd = "DROP TABLE IF EXISTS %s CASCADE" % table
    #       run("echo %s | psql -d '%s'" % (sql_cmd, db))
    #
    # with obvious improvements using psycopg2 instead

    pass


if __name__ == '__main__':
    main()
