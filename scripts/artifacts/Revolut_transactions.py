import json
import shutil
import sqlite3
import tempfile
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, open_sqlite_db_readonly

# Structure de l'artifact
__artifacts_v2__ = {
    "Transactions": {
        "name": "Revolut online banking Transactions",
        "description": "Extraction of all the data available from transactions and the account of a user of Revolut.",
        "author": "@GroupB",
        "version": "0.1",
        "date": "2023-11-29",
        "requirements": "none",
        "category": "Revolut online banking",
        "notes": "",
        "paths": ('*/filesystem1/private/var/mobile/Containers/Shared/AppGroup/1C1C9AC4-DC6D-43B4-9AC6-CF13F221912A/RevolutRetailCoreDroppableDatabase/RevolutRetailCoreDroppable.sqlite*',),
        "function": "get_revolut"
    }
}
# Le montant est stocké en centimes dans la base de données, il faut donc le convertir en euros (à l'unité)
def update_amount_column(cursor):
    cursor.execute('''
        UPDATE ZTRANSACTION 
        SET ZAMOUNT = SUBSTRING(ZAMOUNT, 1, LENGTH(ZAMOUNT) - 2) || '.' || SUBSTRING(ZAMOUNT, -2)
    ''')

# Ajout de la colonne Messages
def add_messages_column(cursor):
    add_column_query = """
    ALTER TABLE ZTRANSACTION
    ADD COLUMN Messages TEXT;
    """
    cursor.execute(add_column_query)

# Mise à jour de la colonne Messages
def update_messages_column(cursor):
    # Définition de la requête SQL
    update_query = """
    UPDATE ZTRANSACTION
    SET Messages = (
        SELECT json_extract(t.ZINFO, '$.comment')
        FROM ZTRANSACTION t
        WHERE json_extract(t.ZINFO, '$.type') = 'TRANSFER'
          AND json_extract(t.ZINFO, '$.comment') IS NOT NULL
          AND t.rowid = ZTRANSACTION.rowid
    )
    """
    cursor.execute(update_query)

# Tri des colonnes et requête SQL finale pour l'extraction des données
def sort(cursor):
    cursor.execute(f'''
    SELECT
    ZTRANSACTION.Z_PK,
    ZTRANSACTION.ZDETAILS, 
    ZTRANSACTION.ZRECIPIENTCODE,
    ZTRANSACTION.ZRECIPIENTUSERNAME,
    ZTRANSACTION.ZSENDERCODE,
    ZTRANSACTION.ZSENDERUSERNAME,
    datetime(ZTRANSACTION.ZCREATEDDATE/1000,'unixepoch'),
    ZTRANSACTION.ZAMOUNT,
    ZTRANSACTION.ZCURRENCY,
    ZTRANSACTION.Messages,
    ZTRANSACTION.ZSTATE,
    ZTRANSACTION.ZCATEGORY,
    ZTRANSACTION.ZTYPE,
    ZMERCHANT.ZADDRESS FROM ZTRANSACTION LEFT JOIN ZMERCHANT ON ZTRANSACTION.Z_PK = ZMERCHANT.ZTRANSACTION;''')

# Copie de la base de données car elle est en lecture seule et il faut pouvoir la modifier
def copy_database(original_path):
    temp_dir = tempfile.mkdtemp()
    temp_db_path = f"{temp_dir}/RevolutCopy.sqlite"
    shutil.copy(original_path, temp_db_path)
    return temp_db_path

# Extraction des données en allant chercher grâce au chemin la base de données et appel des fonctions précédentes
# pour le formatage des données et appel à write_artifact_data_table pour l'écriture dans le rapport
def get_revolut(files_found, report_folder, seeker, wrap_text, offset):
    for file_found in files_found:
        file_found = str(file_found)
        if file_found.endswith('/RevolutRetailCoreDroppable.sqlite'):
            break

    try:
        temp_db_path = copy_database(file_found)
        db = sqlite3.connect(temp_db_path)
        cursor = db.cursor()

        update_amount_column(cursor)
        add_messages_column(cursor)
        update_messages_column(cursor)
        sort(cursor)


        data_list = cursor.fetchall()
        nmbr_entries = len(data_list)

        if nmbr_entries > 0:
            description = "Revolut_transactions"
            report = ArtifactHtmlReport(f'{description}')
            report.start_artifact_report(report_folder, f'{description}')
            report.add_script()
            data_headers = (
                'Index', 'Transaction title', 'Revolut recipient code','Revolut recipient username','Revolut sender code',
                'Revolut sender username', 'Creation date','Amount', 'Currency', 'Messages', 'Status', 'Transaction category', 'Type of payment',
                'Payment address'
            )
            report.write_artifact_data_table(data_headers, data_list, file_found, html_escape=False)
            report.end_artifact_report()
            tsvname = f'{description}'
            tsv(report_folder, data_headers, data_list, tsvname)
        else:
            logfunc('No data available for Revolut')

    except Exception as e:
        logfunc(f"An error occurred: {str(e)}")

    finally:
        db.close()



