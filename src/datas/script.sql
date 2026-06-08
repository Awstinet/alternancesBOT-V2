-- 1. Table des utilisateurs
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
);

-- 2. Table des filtres disponibles
CREATE TABLE filtres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL
);

-- 3. Table de liaison entre les utilisateurs et leurs filtres
CREATE TABLE usersFilters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    userID INTEGER NOT NULL,
    filterID INTEGER NOT NULL,
    FOREIGN KEY (userID) REFERENCES users (id),
    FOREIGN KEY (filterID) REFERENCES filtres (id)
);

-- 4. Table principale des candidatures
CREATE TABLE usersApplications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idUser INTEGER,
    company TEXT NOT NULL,
    post TEXT NOT NULL,
    dateApply TEXT NOT NULL,
    dateRevival TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (idUser) REFERENCES users (id)
);