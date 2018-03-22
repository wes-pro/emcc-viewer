import db, config

d = db.OMRdb(config.db_user, config.db_pass, config.db_tns, config.target_types)

types = d.get_targets()

print(types)




