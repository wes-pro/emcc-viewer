import cx_Oracle


class OMRdb:

    def __init__(self, db_user, db_pass, db_tns, target_types):
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_tns = db_tns
        self.target_types = target_types
        self.pool = cx_Oracle.SessionPool(
            user=self.db_user,
            password=self.db_pass,
            dsn=self.db_tns,
            min=1,
            max=10,
            increment=1,
            threaded=True
        )

    def get_targets(self):
        con = self.pool.acquire()
        cur = con.cursor()
        sql = '''
        select 
            target_name from sysman.mgmt$target
        where 
            target_type in ('{0}')
        order by 1
        '''.format("', '".join(self.target_types))
        print(sql)
        cur.execute(sql)
        return cur.fetchall()









