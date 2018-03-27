import cx_Oracle
import os
import pandas as pd

os.environ["NLS_LANG"] = "american_america.AL32UTF8"


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
        sql = '''
        select 
            target_name,
            target_type,
            rawtohex(target_guid) as target_guid
        from 
            sysman.mgmt$target
        where 
            target_type in ('{0}')
        order by 1
        '''.format("', '".join(self.target_types))
        return pd.read_sql_query(sql, con, index_col='TARGET_GUID')

    def get_target_metrics(self, target_guid):
        con = self.pool.acquire()
        sql2 = '''
        select distinct
            metric_label,
            metric_name
        from 
            sysman.mgmt$metric_details
        where 
            target_guid = :t_guid 
        order by 1
        '''

        sql = '''
        select 
            tt.metric_label, 
            tt.metric_name
        from 
            sysman.mgmt$target_metric_collections mc
            left join sysman.mgmt$target_type tt on (
                mc.target_guid = tt.target_guid and 
                mc.metric_name = tt.metric_name and 
                mc.metric_column = tt.metric_column
            )
        where 
            mc.target_guid = :t_guid and
            tt.metric_type = 'Table' and
            mc.is_enabled=1 and 
            mc.upload_policy=1 and 
            mc.frequency_code='Interval'
        order by 1
        '''
        return pd.read_sql_query(sql, con, index_col='METRIC_NAME', params={'t_guid': target_guid})

    def get_target_metric_columns(self, target_guid, metric_name):
        con = self.pool.acquire()
        sql = '''
        select distinct
            column_label,
            metric_column,
            rawtohex(metric_guid) as metric_guid
        from
            sysman.mgmt$metric_details
        where 
            target_guid = :t_guid and
            metric_name = :m_name
        order by 1
        '''
        return pd.read_sql_query(sql, con, index_col='METRIC_COLUMN',
                                 params={'t_guid': target_guid, 'm_name': metric_name})

    def get_metric_column_data(self, target_guid, metric_name, metric_column, resample=None, method='bfill'):
        con = self.pool.acquire()
        sql = '''
        select
            collection_timestamp as time,
            value
        from 
            sysman.mgmt$metric_details
        where
            target_guid = :t_guid and
            metric_name = :m_name and
            metric_column = :c_name
        order by 1
        '''
        df = pd.read_sql_query(sql, con, index_col='TIME',
                               params={'t_guid': target_guid,
                                       'm_name': metric_name,
                                       'c_name': metric_column})
        if resample:
            rs = df.apply(pd.to_numeric, errors='ignore').resample(resample)
            rs_resampled = getattr(rs, method)()
            return rs_resampled.interpolate()
        else:
            return df.apply(pd.to_numeric, errors='ignore')

