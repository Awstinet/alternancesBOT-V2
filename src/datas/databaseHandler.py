import sqlite3
import os
import pandas 
import datetime

# Chemin d'accès de la base de données
dbPath = os.path.join(os.path.dirname(__file__), "database.db")   

def connectDB():
    return sqlite3.connect(dbPath)


def getAllFilters() -> dict:
    """Fonction qui permet de voir tous les filtres de la base de données."""
    conn = connectDB()
    query = """SELECT id, nom FROM filtres;"""
    filters = pandas.read_sql_query(query, conn)
    conn.close()
    return filters.set_index("id")["nom"].to_dict()


def addFilterTo(userID: int, filterID: int) -> None:
    """Filtre qui permet à un utilisateur d'ajouter un filtre à son profil."""
    conn = connectDB()
    cursor = conn.cursor()
    query = f"""INSERT OR IGNORE INTO usersFilters (id, userID, filterID) VALUES ({int(str(userID) + str(filterID))}, {userID}, {filterID});"""
    cursor.execute(query)
    conn.commit()
    conn.close()
    conn.close()

def getUserFiltersID(userID: int) -> None:
    """Fonction qui permet de récupérer l'identifiant de tous les filtres qu'un utilisateur a choisi."""
    conn = connectDB()
    query = f"""SELECT usersFilters.id AS identify, nom FROM usersFilters JOIN filtres ON usersFilters.filterID = filtres.id WHERE userID = ?;"""
    filters = pandas.read_sql_query(query, conn, params=(userID,))
    conn.close()
    return filters.set_index("identify")["nom"].to_dict()

def deleterFilterTo(id: int) -> None:
    """Fonction qui permet à un utilisateur de supprimer un des filtres qu'ils ont en possession."""
    conn = connectDB()
    cursor = conn.cursor()
    query = f"""DELETE FROM usersFilters WHERE id = {id};"""
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()

def getAllMembersWithFilter(filter1: str) -> dict:
    """Fonction qui permet de récupérer l'identifiant de tous les utilisateurs intéressés par le filtre mis en paramètre."""
    conn = connectDB()
    query = """SELECT userID FROM usersFilters WHERE filterID IN (SELECT id FROM filtres WHERE nom = ?);"""
    members = pandas.read_sql_query(query, conn, params=(filter1,))
    conn.close()
    return members.to_dict()

def getUserFilters(userID: int) -> dict:
    """Fonction qui permet de récupérer tous les filtres qu'un utilisateur a choisi."""
    conn = connectDB()
    query = """SELECT filtres.nom FROM filtres WHERE filtres.id IN (SELECT usersFilters.filterId FROM usersFilters WHERE userId = ?);"""
    filters = pandas.read_sql_query(query, conn, params=(userID,))
    conn.close()
    return filters.to_dict()

def addUserApplication(userID: int, company: str, post: str):
    """Fonction qui permet d'ajouter une offre à laquelle un utilisateur a postulé."""
    today = datetime.date.today()
    revivalDate = today + datetime.timedelta(days=3)
    conn = connectDB()
    cursor = conn.cursor()
    query = f"""INSERT INTO usersApplications (idUser, company, post, dateApply, dateRevival, status) VALUES (
        {userID}, "{company}", "{post}", "{today.strftime("%d/%m/%Y")}", "{revivalDate.strftime("%d/%m/%Y")}", "applied"
    );"""
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()

def deleteUserApplication(appID: int):
    """Fonction qui permet de supprimer une offre à l'aide de son identifiant"""
    conn = connectDB()
    cursor = conn.cursor()
    query = f"""DELETE FROM usersApplications WHERE id = {appID};"""
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()

def getUserApplications(userID: int):
    """Fonction qui permet de récupérer toutes les informations relatives aux offres à laquelle un utilisateur a postulé."""
    conn=connectDB()
    query= """SELECT * FROM usersApplications WHERE idUser = ?;"""
    applications = pandas.read_sql_query(query, conn, params=(userID,))
    conn.close()
    return applications

def getRevivalDates():
    conn = connectDB()
    query = """SELECT idUser, dateRevival FROM usersApplications"""
    revivalDates = pandas.read_sql_query(query, conn)
    conn.close()
    return revivalDates

def changeStatus(applicationID: int, newStatus: str):
    conn = connectDB()
    cursor = conn.cursor()
    query = f"""UPDATE usersApplications SET status = "{newStatus}" WHERE id = {applicationID};"""
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()