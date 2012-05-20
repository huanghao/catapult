import os
from MySQLdb import escape_string


def main():
    dirname = os.path.dirname(os.path.abspath(__file__))

    SQL = '''
INSERT INTO core_proj(id,`name`,home,owner,cvs_model,cvs_path) VALUES (
       1000, 'dummy', '/tmp/dummy', 'nobody', 'svn',
       'file://%s');

INSERT INTO core_proj(id,`name`,home,owner,cvs_model,cvs_path) VALUES (
       1001, 'yummy', '/tmp/yummy', 'nobody', 'git',
       'file://%s');

INSERT INTO core_ip VALUES (1002,'localhost','lo',NULL);

INSERT INTO core_proj_ips(proj_id,ip_id) VALUES (1000,1002);
INSERT INTO core_proj_ips(proj_id,ip_id) VALUES (1001,1002);
''' % (escape_string(os.path.join(dirname, 'svn-repo')),
       escape_string(os.path.join(dirname, 'git-repo')))
    print SQL


if __name__ == '__main__':
    main()
