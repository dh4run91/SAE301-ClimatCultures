-- =====================================================================
-- SAE 3.01 « Climat & Cultures » - equipe 9
-- Tables des donnees personnelles (perimetre « Souhaitable »)
--
-- Reprend exactement la section 5 de docs/CONCEPTION-RGPD.md (version 2).
-- Independant du modele en etoile : aucune de ces tables n'est reliee a
-- Fact_Indicateur, qui ne contient aucun identifiant de personne.
--
-- A executer apres 01-creation-base.sql, et seulement si l'equipe garde
-- les comptes et les favoris dans le perimetre.
--
-- La contrainte CHECK de Favori exige MySQL 8.0.16 ou plus recent : les
-- versions anterieures l'acceptent sans erreur mais ne l'appliquent pas.
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS Favori;
DROP TABLE IF EXISTS Compte;
DROP TABLE IF EXISTS Session_Visiteur;

SET FOREIGN_KEY_CHECKS = 1;


-- ---------------------------------------------------------------------
-- Session_Visiteur : le cookie de session
--
-- L'UUID ne porte aucune information, mais il est rattache a un
-- navigateur : c'est une donnee pseudonymisee, qui releve du RGPD.
-- Purge : lignes dont date_expiration est depassee, chaque nuit.
-- ---------------------------------------------------------------------
CREATE TABLE Session_Visiteur (
    id_session      CHAR(36)  NOT NULL COMMENT 'UUID v4, donnee pseudonymisee',
    date_creation   DATETIME  NOT NULL,
    date_expiration DATETIME  NOT NULL COMMENT 'Creation + 30 jours',
    PRIMARY KEY (id_session),
    INDEX idx_session_expiration (date_expiration)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Sessions des visiteurs, conservees 30 jours';


-- ---------------------------------------------------------------------
-- Compte : le compte facultatif
--
-- Le mot de passe n'est jamais stocke en clair : seule son empreinte
-- bcrypt est enregistree. Purge : comptes inactifs depuis 24 mois.
-- ---------------------------------------------------------------------
CREATE TABLE Compte (
    id_compte       INT          NOT NULL AUTO_INCREMENT,
    email           VARCHAR(255) NOT NULL,
    mot_de_passe    VARCHAR(255) NOT NULL COMMENT 'Empreinte bcrypt, jamais le clair',
    date_creation   DATETIME     NOT NULL,
    derniere_visite DATETIME     NULL,
    PRIMARY KEY (id_compte),
    UNIQUE KEY uq_compte_email (email),
    INDEX idx_compte_derniere_visite (derniere_visite)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Comptes utilisateurs facultatifs';


-- ---------------------------------------------------------------------
-- Favori : une commune et une culture retenues par un compte OU une session
--
-- Les ON DELETE CASCADE realisent le droit a l'effacement : supprimer un
-- compte, ou purger une session expiree, supprime ses favoris dans la meme
-- transaction.
-- ---------------------------------------------------------------------
CREATE TABLE Favori (
    id_favori   INT         NOT NULL AUTO_INCREMENT,
    id_compte   INT         NULL,
    id_session  CHAR(36)    NULL,
    id_commune  CHAR(5)     NOT NULL,
    id_culture  VARCHAR(20) NOT NULL,
    PRIMARY KEY (id_favori),
    CONSTRAINT fk_favori_compte  FOREIGN KEY (id_compte)
        REFERENCES Compte (id_compte) ON DELETE CASCADE,
    CONSTRAINT fk_favori_session FOREIGN KEY (id_session)
        REFERENCES Session_Visiteur (id_session) ON DELETE CASCADE,
    CONSTRAINT fk_favori_commune FOREIGN KEY (id_commune)
        REFERENCES Dim_Commune (id_commune),
    CONSTRAINT fk_favori_culture FOREIGN KEY (id_culture)
        REFERENCES Dim_Culture (id_culture),
    -- un favori appartient a un compte OU a une session, jamais aux deux ni a aucun
    CONSTRAINT chk_favori_proprietaire
        CHECK ((id_compte IS NULL) <> (id_session IS NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Favoris, effaces en cascade avec leur compte ou leur session';
