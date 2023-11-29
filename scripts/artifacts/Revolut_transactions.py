import scripts
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline, open_sqlite_db_readonly, convert_ts_human_to_utc, convert_utc_human_to_timezone

__artifacts_v2__ = { "Transactions": {
    "name": "Transactions_Revolut",
    "description": "Exctraction of Revolut transactions from ZTRANSACTIONS.db", "author": "@GroupB",
    "version": "0.1",
    "date": "2023-11-27",
    "requirements": "none",
    "category": "ZTRANSACTIONS.db",
    "notes": "",
    "paths": ('*/Users/emanuellemary/Desktop/Apple_iPhone 8 (A1905).zip/root/private/var/mobile/Containers/Shared/AppGroup/1C1C9AC4-DC6D-43B4-9AC6-CF13F221912A/RevolutRetailCoreDroppable.sqlite*'), "function": "get_knowledgeC_BatteryPercentage"
    } }

for file_found in files_found:
    file_found = str(file_found)
    if file_found.endswith('/RevolutRetailCoreDroppable.sqlite'):
        break

db = open_sqlite_db_readonly(file_found)
cursor = db.cursor()