-- =====================================================================
-- SAE 3.01 « Climat & Cultures » - equipe 9
-- Script de creation de la base - modele dimensionnel en etoile
--
-- Cible : MySQL 8 (AlwaysData). Encodage utf8mb4, moteur InnoDB.
-- Source du modele : data/J1-dimensions-necessaires.md
--
-- Grain de la table de faits : commune x culture x horizon x modele x indicateur
--
-- Deux choix de conception sont a connaitre pour la soutenance :
--
--  1. id_commune est un CHAR(5), pas un entier. Le code INSEE est une
--     etiquette, pas une quantite : 2A004 contient une lettre, et 05023
--     (Briancon) perdrait son zero initial dans un champ numerique.
--
--  2. Fact_Indicateur stocke UNE LIGNE PAR INDICATEUR, et non une colonne
--     par indicateur. Ajouter un indicateur en J3 ne demandera donc aucune
--     modification du schema, seulement des lignes supplementaires.
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS Fact_Indicateur;
DROP TABLE IF EXISTS Fenetre_Calcul;
DROP TABLE IF EXISTS Dim_Modele;
DROP TABLE IF EXISTS Dim_Temps;
DROP TABLE IF EXISTS Dim_Culture;
DROP TABLE IF EXISTS Dim_Commune;

SET FOREIGN_KEY_CHECKS = 1;


-- ---------------------------------------------------------------------
-- Dim_Commune : le « ou »
--
-- L'API Open-Meteo ne connait pas « Reims », seulement un couple
-- latitude / longitude. Cette table fait la traduction.
--
-- altitude_m est l'altitude de la MAILLE renvoyee par l'API (champ
-- elevation), pas celle du clocher. Pour Reims l'API renvoie 93 m.
-- ---------------------------------------------------------------------
CREATE TABLE Dim_Commune (
    id_commune       CHAR(5)       NOT NULL COMMENT 'Code INSEE officiel, 5 caracteres',
    nom              VARCHAR(100)  NOT NULL,
    latitude         DECIMAL(8,5)  NOT NULL COMMENT 'Centroide API Geo, degres decimaux',
    longitude        DECIMAL(8,5)  NOT NULL COMMENT 'Attention : API Geo renvoie [lon, lat]',
    altitude_m       SMALLINT      NULL     COMMENT 'Altitude de la maille (champ elevation)',
    zone_climatique  VARCHAR(50)   NULL,
    departement      CHAR(3)       NOT NULL,
    PRIMARY KEY (id_commune),
    INDEX idx_commune_departement (departement)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Les 16 communes de reference';


-- ---------------------------------------------------------------------
-- Dim_Culture : le « quoi »
--
-- Porte les seuils agronomiques qui transforment une donnee brute en
-- information. -3 degres le 5 avril ne veut rien dire ; -3 degres face a
-- un seuil de gel de -2 au debourrement veut dire « degats sur la vigne ».
--
-- Les colonnes url_* portent la tracabilite exigee par le sujet : chaque
-- valeur pointe vers une source reelle, ou vaut 'non_trouve'.
-- ---------------------------------------------------------------------
CREATE TABLE Dim_Culture (
    id_culture               VARCHAR(20)  NOT NULL,
    nom                      VARCHAR(100) NOT NULL,
    type                     VARCHAR(40)  NULL,
    t_base_c                 DECIMAL(4,1) NULL COMMENT 'Zero de vegetation',
    t_plafond_gdd_c          DECIMAL(4,1) NULL COMMENT 'Ecretage de Tmax, 30 pour le mais',
    gdd_maturite_cj          SMALLINT     NULL COMMENT 'Somme de temperatures a maturite',
    seuil_gel_c              DECIMAL(4,1) NULL,
    besoin_eau_mm            SMALLINT     NULL,
    t_opt_min_c              DECIMAL(4,1) NULL,
    t_opt_max_c              DECIMAL(4,1) NULL,
    seuil_stress_thermique_c DECIMAL(4,1) NULL,
    stade_concerne           VARCHAR(80)  NULL COMMENT 'Stade auquel s applique le seuil de gel',
    perimetre                ENUM('MVP','hors_perimetre') NOT NULL DEFAULT 'hors_perimetre',
    source_institut          VARCHAR(255) NULL,
    url_t_base               VARCHAR(500) NULL,
    url_t_plafond            VARCHAR(500) NULL,
    url_gdd                  VARCHAR(500) NULL,
    url_gel                  VARCHAR(500) NULL,
    url_eau                  VARCHAR(500) NULL,
    url_t_opt                VARCHAR(500) NULL,
    url_stress               VARCHAR(500) NULL,
    date_consultation        DATE         NULL,
    confiance                ENUM('Elevee','Moyenne','Faible') NULL,
    seuils_a_revoir          TEXT         NULL COMMENT 'Seuils que la source contredit',
    remarque                 TEXT         NULL,
    PRIMARY KEY (id_culture)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Cultures et leurs seuils agronomiques sources';


-- ---------------------------------------------------------------------
-- Dim_Temps : le « quand »
--
-- Un horizon n'est pas une annee. Dans une projection, 2049 n'est pas une
-- prediction de 2049 : c'est une annee plausible parmi d'autres. Seule une
-- moyenne sur une dizaine d'annees a un sens, d'ou deux periodes de meme
-- longueur, une de reference et une de projection.
-- ---------------------------------------------------------------------
CREATE TABLE Dim_Temps (
    id_horizon   VARCHAR(20)  NOT NULL,
    libelle      VARCHAR(80)  NOT NULL,
    annee_debut  SMALLINT     NOT NULL,
    annee_fin    SMALLINT     NOT NULL,
    type         ENUM('reference','projection') NOT NULL,
    PRIMARY KEY (id_horizon),
    CONSTRAINT chk_horizon_ordre CHECK (annee_fin >= annee_debut),
    CONSTRAINT chk_horizon_borne CHECK (annee_fin <= 2050)
        -- L'API Open-Meteo Climate s'arrete en 2050.
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Horizons climatiques compares';


-- ---------------------------------------------------------------------
-- Dim_Modele : « selon quelle simulation »
--
-- Sans le modele dans la cle, deux valeurs contradictoires ne peuvent pas
-- coexister : sur Reims en 2049 nos deux modeles donnent 28 et 11 jours de
-- gel. Il faudrait en choisir un arbitrairement et faire disparaitre
-- l'autre, donc afficher une fausse certitude.
-- ---------------------------------------------------------------------
CREATE TABLE Dim_Modele (
    id_modele             VARCHAR(30)  NOT NULL,
    nom_complet           VARCHAR(120) NULL,
    institution           VARCHAR(120) NULL,
    pays                  VARCHAR(60)  NULL,
    resolution_native_km  SMALLINT     NULL,
    variables_disponibles TEXT         NULL,
    date_verification     DATE         NULL,
    remarque              TEXT         NULL,
    PRIMARY KEY (id_modele)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Modeles climatiques CMIP6 retenus';


-- ---------------------------------------------------------------------
-- Fenetre_Calcul : la bonne periode pour chaque indicateur
--
-- C'est la table qui evite la faute la plus couteuse du projet. Sur Reims
-- en 2049 nos modeles donnent 28 et 11 jours de gel sur l'annee entiere,
-- soit 17 jours d'ecart. Mais 22 de ces 28 jours tombent en janvier et
-- fevrier, quand la vigne dort et supporte -8 degres.
--
-- En appliquant cette fenetre, mars a mai, et le seuil du stade, -2 degres
-- au debourrement, l'ecart tombe a 1 jour contre 0. L'incertitude apparente
-- etait un artefact de comptage.
--
-- seuil_specifique permet au seuil de dependre du stade : la vigne gele a
-- -8 en dormance et a -2 au debourrement, un facteur 4.
-- ---------------------------------------------------------------------
CREATE TABLE Fenetre_Calcul (
    id_culture       VARCHAR(20)  NOT NULL,
    indicateur       VARCHAR(40)  NOT NULL,
    mois_debut       TINYINT      NOT NULL,
    mois_fin         TINYINT      NOT NULL,
    seuil_specifique DECIMAL(5,1) NULL COMMENT 'Remplace le seuil de Dim_Culture sur cette fenetre',
    commentaire      VARCHAR(255) NULL,
    PRIMARY KEY (id_culture, indicateur),
    CONSTRAINT fk_fenetre_culture FOREIGN KEY (id_culture)
        REFERENCES Dim_Culture (id_culture) ON DELETE CASCADE,
    CONSTRAINT chk_fenetre_mois CHECK (mois_debut BETWEEN 1 AND 12
                                   AND mois_fin   BETWEEN 1 AND 12)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Un indicateur est une regle ET une periode';


-- ---------------------------------------------------------------------
-- Fact_Indicateur : les resultats calcules
--
-- Ce que l'on NE stocke PAS : les series brutes. 365 jours x 10 ans x 4
-- variables x 2 modeles x 16 communes font environ 470 000 valeurs, pour
-- 100 Mo d'hebergement sur AlwaysData. Et c'est inutile : l'API peut les
-- redonner, alors que le resultat tient en un nombre.
--
-- Une ligne par indicateur plutot qu'une colonne par indicateur : le bilan
-- hydrique, deja calcule par indicateurs.py, ou tout indicateur ajoute en J3
-- n'exigera aucun ALTER TABLE.
-- ---------------------------------------------------------------------
CREATE TABLE Fact_Indicateur (
    id_commune    CHAR(5)       NOT NULL,
    id_culture    VARCHAR(20)   NOT NULL,
    id_horizon    VARCHAR(20)   NOT NULL,
    id_modele     VARCHAR(30)   NOT NULL,
    indicateur    VARCHAR(40)   NOT NULL,
    valeur        DECIMAL(10,2) NULL COMMENT 'NULL = non calculable, jamais 0 par defaut',
    unite         VARCHAR(20)   NOT NULL,
    nb_annees     TINYINT       NULL COMMENT 'Nombre d annees moyennees, pour la tracabilite',
    date_calcul   DATE          NOT NULL,
    PRIMARY KEY (id_commune, id_culture, id_horizon, id_modele, indicateur),
    CONSTRAINT fk_fait_commune FOREIGN KEY (id_commune) REFERENCES Dim_Commune (id_commune),
    CONSTRAINT fk_fait_culture FOREIGN KEY (id_culture) REFERENCES Dim_Culture (id_culture),
    CONSTRAINT fk_fait_horizon FOREIGN KEY (id_horizon) REFERENCES Dim_Temps   (id_horizon),
    CONSTRAINT fk_fait_modele  FOREIGN KEY (id_modele)  REFERENCES Dim_Modele  (id_modele),
    INDEX idx_fait_lecture (id_commune, id_culture, indicateur)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Un fait = le croisement d une donnee climatique et d un seuil';


-- ---------------------------------------------------------------------
-- Vue de lecture : la fourchette entre modeles
--
-- L'application ne doit jamais afficher la valeur d'un seul modele. Cette
-- vue renvoie directement le minimum, le maximum et l'ecart, pour que le
-- front n'ait pas a recalculer l'incertitude a chaque affichage.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW V_Fourchette_Indicateur AS
SELECT
    f.id_commune,
    f.id_culture,
    f.id_horizon,
    f.indicateur,
    f.unite,
    MIN(f.valeur)                     AS valeur_min,
    MAX(f.valeur)                     AS valeur_max,
    ROUND(AVG(f.valeur), 2)           AS valeur_moyenne,
    ROUND(MAX(f.valeur) - MIN(f.valeur), 2) AS ecart_modeles,
    COUNT(DISTINCT f.id_modele)       AS nb_modeles
FROM Fact_Indicateur f
WHERE f.valeur IS NOT NULL
GROUP BY f.id_commune, f.id_culture, f.id_horizon, f.indicateur, f.unite;
