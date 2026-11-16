-- =====================================================================
-- SAE 3.01 « Climat & Cultures » - equipe 9
-- Agregation des faits a la region
--
-- A executer apres 01-creation-base.sql et 02-insertion-dimensions.sql.
--
-- Le contrat d'interface du 02/11/2026 tranche le grain : on stocke a la
-- commune, on agrege a la region par requete. Rien n'est stocke en plus :
-- id_region et nom_region sont des colonnes de Dim_Commune.
--
-- CE QUE CETTE VUE AGREGE REELLEMENT
--
-- Le min et le max portent sur toutes les communes ET tous les modeles de la
-- region. Ce n'est donc plus seulement l'incertitude entre modeles, comme
-- dans V_Fourchette_Indicateur : s'y ajoute l'ecart entre communes.
-- Exemple : Avignon (25 m) et Briancon (1326 m) sont tous deux en region 93.
-- Leur fourchette commune traduit 1300 m d'altitude, pas un desaccord de
-- modeles. Et leur moyenne ne decrit aucun lieu reel.
--
-- Autre limite : une region n'est representee que par nos communes de
-- reference. Cinq regions n'en ont qu'une (11, 24, 27, 32, 75), la region
-- y est la commune. nb_communes doit etre affiche avec le resultat.
-- =====================================================================

SET NAMES utf8mb4;

CREATE OR REPLACE VIEW V_Fourchette_Region AS
SELECT
    c.id_region,
    c.nom_region,
    f.id_culture,
    f.id_horizon,
    f.indicateur,
    f.unite,
    MIN(f.valeur)                           AS valeur_min,
    MAX(f.valeur)                           AS valeur_max,
    ROUND(AVG(f.valeur), 2)                 AS valeur_moyenne,
    ROUND(MAX(f.valeur) - MIN(f.valeur), 2) AS ecart,
    COUNT(DISTINCT f.id_commune)            AS nb_communes,
    COUNT(DISTINCT f.id_modele)             AS nb_modeles,
    COUNT(*)                                AS nb_faits
FROM Fact_Indicateur f
JOIN Dim_Commune c ON c.id_commune = f.id_commune
WHERE f.valeur IS NOT NULL
GROUP BY c.id_region, c.nom_region, f.id_culture, f.id_horizon, f.indicateur, f.unite;


-- ---------------------------------------------------------------------
-- Exemple de lecture : jours de gel de la vigne au debourrement, Grand
-- Est (code 44, soit Reims, Strasbourg et Nancy), par horizon.
-- ---------------------------------------------------------------------
-- SELECT nom_region, id_horizon, valeur_min, valeur_max, nb_communes, nb_modeles
-- FROM V_Fourchette_Region
-- WHERE id_region = '44'
--   AND id_culture = 'VIGNE'
--   AND indicateur = 'gel'
-- ORDER BY id_horizon;
