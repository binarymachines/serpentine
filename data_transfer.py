

import db
import sys, os
from bifrost_models import *
from sqlalchemy import *




def transferVODCategories():
    """move VOD category data from the old schema to the new"""
    
    sourceDB = db.MySQLDatabase('localhost', 'avalon_mmf')
    targetDB = db.MySQLDatabase('localhost', 'bifrost')

    sourceDB.login('dtaylor', 'notobvious')
    targetDB.login('dtaylor', 'notobvious')

    sourceMgr = db.PersistenceManager(sourceDB)
    targetMgr = db.PersistenceManager(targetDB)

    sourceTable = sourceMgr.loadTable('vod_categories')


    targetMgr.mapTypeToTable('bifrost_models.VODCategory', 'vod_categories')

    query = select([sourceTable.c.id, sourceTable.c.distrib_id, sourceTable.c.cat_name, sourceTable.c.cat_path])
    cursor = query.execute()
    rows = cursor.fetchall()

    records = 0
    for record in rows:
        session = targetMgr.getSession()
        newCategory = VODCategory()
        newCategory.id = record['id']
        newCategory.distributor_id = record['distrib_id']
        newCategory.name = record['cat_name']
        newCategory.target_media_path = record['cat_path']

        targetMgr.insert(newCategory, session)
        session.commit()
        records += 1
        print "%d record(s) transferred from source to target." % records


    print "Exiting with no errors."


def main():
    transferVODCategories()



if __name__ == "__main__":
        main() 

        
        
        

