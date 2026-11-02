-- =====================================================================
-- SAE 3.01 « Climat & Cultures » - equipe 9
-- Insertion des dimensions
--
-- Donnees issues de data/communes-reference.csv et
-- data/referentiel-cultures-v2.csv, tels que poussees dans le depot.
-- A executer apres 01-creation-base.sql.
-- =====================================================================

SET NAMES utf8mb4;

-- --- 16 communes de reference ---------------------------------------
-- Reims porte les valeurs verifiees le 30/09/2026 : centroide API Geo
-- 49.2535 / 4.0551 et altitude de la maille Open-Meteo, 93 m (voir
-- data/test/README.md). Ce sont aussi les valeurs utilisees par
-- indicateurs.py.
--
-- A FAIRE : pour les 15 autres communes, les coordonnees sont arrondies a
-- 0,01 degre et altitude_m semble etre l'altitude de la ville, pas celle de
-- la maille renvoyee par l'API (champ elevation). A remplacer par les
-- valeurs de l'API, ou a signaler dans le commentaire de la colonne.
INSERT INTO Dim_Commune (id_commune, nom, latitude, longitude, altitude_m, zone_climatique, departement) VALUES
  ('59350', 'Lille', 50.63, 3.06, 25, 'océanique dégradé', '59'),
  ('29019', 'Brest', 48.39, -4.49, 50, 'océanique', '29'),
  ('35238', 'Rennes', 48.11, -1.68, 30, 'océanique', '35'),
  ('51454', 'Reims', 49.2535, 4.0551, 93, 'océanique dégradé', '51'),
  ('75056', 'Paris', 48.85, 2.35, 35, 'océanique dégradé', '75'),
  ('45234', 'Orléans', 47.90, 1.90, 100, 'océanique dégradé', '45'),
  ('67482', 'Strasbourg', 48.58, 7.75, 140, 'semi-continental', '67'),
  ('54395', 'Nancy', 48.69, 6.18, 210, 'semi-continental', '54'),
  ('21231', 'Dijon', 47.32, 5.04, 245, 'semi-continental', '21'),
  ('63113', 'Clermont-Ferrand', 45.78, 3.08, 330, 'semi-continental', '63'),
  ('69123', 'Lyon', 45.76, 4.84, 170, 'semi-continental', '69'),
  ('33063', 'Bordeaux', 44.84, -0.58, 10, 'océanique aquitain', '33'),
  ('31555', 'Toulouse', 43.60, 1.44, 150, 'océanique aquitain', '31'),
  ('84007', 'Avignon', 43.95, 4.81, 25, 'méditerranéen', '84'),
  ('34172', 'Montpellier', 43.61, 3.88, 30, 'méditerranéen', '34'),
  ('05023', 'Briançon', 44.90, 6.64, 1326, 'montagnard', '05');

-- --- 10 cultures et leurs seuils ------------------------------------
INSERT INTO Dim_Culture (id_culture, nom, type, t_base_c, t_plafond_gdd_c,
  gdd_maturite_cj, seuil_gel_c, besoin_eau_mm, t_opt_min_c, t_opt_max_c,
  seuil_stress_thermique_c, stade_concerne, perimetre, source_institut,
  url_t_base, url_t_plafond, url_gdd, url_gel, url_eau, url_t_opt, url_stress,
  date_consultation, confiance, seuils_a_revoir, remarque) VALUES
  ('BLE_TENDRE_H', 'Blé tendre d''hiver', 'cereale_hiver', 0, NULL,
   2150, -4, 500, 15, 22,
   30, 'épi 1 cm / début montaison (gel)', 'MVP', 'ARVALIS / Chambres d''agriculture / FAO',
   'https://opera-connaissances.chambres-agriculture.fr/doc_num.php?explnum_id=185517', NULL, 'https://www.arvalis.fr/infos-techniques/chaleur-exceptionnelle-doctobre-les-consequences-possibles-sur-les-cereales-juste', 'https://www.arvalis.fr/infos-techniques/comment-diagnostiquer-deventuels-degats-lies-au-froid',
   'https://www.perspectives-agricoles.com/conduite-de-cultures/modelisation-des-besoins-en-eau-combien-consomment-les-cultures', 'https://www.fao.org/land-water/databases-and-software/crop-information/wheat/en/', 'https://www.arvalis.fr/infos-techniques/quelles-consequences-des-temperatures-elevees-sur-le-remplissage-des-grains',
   '2026-09-15', 'Elevee', 't_opt_max 20 et non 22 ; échaudage dès 25 °C selon AgriClim', 'Gel d''épi à -4 °C sous abri peu après épi 1 cm (ARVALIS 2017) : le stade retenu est le bon. Écrêtage à 25 °C à ajouter à la formule des degrés-jours.'),
  ('ORGE_H', 'Orge d''hiver', 'cereale_hiver', 0, NULL,
   1900, -5, 450, 12, 20,
   30, 'début montaison (gel)', 'hors_perimetre', 'ARVALIS / FAO / Université de Liège',
   'https://matheo.uliege.be/bitstream/2268.2/2633/1/Memoire-final-Raphael-Delattre.pdf', NULL, 'https://blog.spotifarm.fr/tour-de-plaine-spotifarm/somme-de-temperature-pourquoi-suivre-levolution-des-degres-jours', 'https://fiches.arvalis-infos.fr/fiche_accident/fiches_accidents.php?mode=fa&type_cul=12&type_acc=5&id_acc=489',
   'https://www.arvalis.fr/infos-techniques/declencher-lirrigation-au-bon-moment', 'https://www.fao.org/4/S8500F/s8500f0e.htm', 'https://www.arvalis.fr/infos-techniques/quelles-consequences-des-temperatures-elevees-sur-le-remplissage-des-grains',
   '2026-09-15', 'Elevee', 'gel -4 et non -5 ; t_opt_min 15 et non 12', 'ARVALIS classe l''orge d''hiver plus sensible au gel que le blé : retenir -5 °C inverse la hiérarchie réelle.'),
  ('COLZA_H', 'Colza d''hiver', 'oleagineux_hiver', 5, NULL,
   2200, -5, 450, 12, 22,
   27, 'floraison (gel)', 'hors_perimetre', 'Terres Inovia / INRAE',
   'https://mots-agronomie.inrae.fr/index.php/Temps_thermique_(sommes_de_temp%C3%A9ratures)', NULL, 'https://climadiag-agriculture.fr/static/Climadiag_Agriculture_Guide_Utilisateur_2024v1.pdf', 'https://www.terresinovia.fr/-/accidents-climatiques-sur-colza-gelees-printanieres',
   'https://www.terresinovia.fr/-/accidents-climatiques-sur-colza-manque-ou-exces-d-eau', 'https://www.yara.fr/fertilisation/solutions-pour-cultures/colza/agronomie-colza/', 'https://www.nature.com/articles/s41598-026-41957-7',
   '2026-09-15', 'Moyenne', 'gdd_maturite ; besoin_eau 600 et non 450 ;', 'Aucune source ne donne 5 °C : INRAE dit 6 °C, AgroParisTech dit voisin de 0 °C. Les -5 °C portent sur la destruction foliaire, pas sur la floraison.'),
  ('MAIS_GRAIN', 'Maïs grain', 'cereale_ete', 6, 30,
   1600, 0, 600, 20, 30,
   35, 'fin de cycle (gel), floraison (stress)', 'MVP', 'ARVALIS / FAO',
   'https://www.perspectives-agricoles.com/sites/default/files/imported_files/309_624182783890695089.pdf', 'https://www.perspectives-agricoles.com/sites/default/files/imported_files/309_624182783890695089.pdf', 'https://www.perspectives-agricoles.com/sites/default/files/imported_files/309_624182783890695089.pdf', 'https://fiches.arvalis-infos.fr/fiche_accident/fiches_accidents.php?mode=fa&type_cul=3&type_acc=5&id_acc=327',
   'https://www.perspectives-agricoles.com/conduite-de-cultures/modelisation-des-besoins-en-eau-combien-consomment-les-cultures', 'https://www.perspectives-agricoles.com/recherche-agronomie/les-fortes-chaleurs-penalisent-le-potentiel-des-mais', 'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/crop_profiles/GAEZ_Crop_profile_maize.pdf',
   '2026-09-15', 'Elevee', 'gdd_maturite 1600 ne couvre que les variétés très précoces', 'Formule officielle française en base 6 °C avec écrêtage de Tmax à 30 °C. La notation base 6-30 est reprise sur arvalis.fr, page Les previsions du stade floraison du mais. Besoin en eau 600 mm = haut de fourchette, moyenne 500 mm.'),
  ('TOURNESOL', 'Tournesol', 'oleagineux_ete', 6, NULL,
   1550, -1, 500, 20, 28,
   34, 'levée (gel)', 'MVP', 'AgroParisTech / INRAE / Chambre d''agriculture du Tarn',
   'https://siafee.fr/phytotechnie/tournesol/tour_devlpt.htm', NULL, 'https://siafee.fr/phytotechnie/tournesol/tour_devlpt.htm', 'https://www.masseeds.fr/wp-content/uploads/sites/2/2024/05/fr_sunflower_lv.pdf',
   'https://tarn.chambres-agriculture.fr/fileadmin/user_upload/284_chambre_dagriculture_-_tarn/Interface/Bulletins_techniques/Bulletins_irrigation_Hydro/bulletins_irrigation_2024/Pilotage_irrigation_tournesol.pdf', 'https://sunflo.pages-forge.inrae.fr/sunflower/articles/_0_sunflo_documentation.html', 'https://sunflo.pages-forge.inrae.fr/sunflower/articles/_0_sunflo_documentation.html',
   '2026-09-15', 'Moyenne', 'gdd_maturite 1600-1700 ; besoin_eau 400 en contexte français ; seuil_stress 37 ou 28', 't_opt 20-28 °C est la seule valeur exactement confirmée par une source primaire (modèle SUNFLO, INRAE).'),
  ('SOJA', 'Soja', 'oleoproteagineux_ete', 10, NULL,
   1500, 0, 550, 20, 30,
   35, 'floraison (gel)', 'hors_perimetre', 'OCL / FAO / Terres Inovia',
   'https://www.ocl-journal.org/articles/ocl/full_html/2015/05/ocl150028-s/ocl150028-s.html', NULL, 'https://www.ocl-journal.org/articles/ocl/full_html/2015/05/ocl150028-s/ocl150028-s.html', 'https://www.ndsu.edu/agriculture/ag-hub/ag-topics/crops/soybeans/evaluating-frost-damage-soybean-09/10/20',
   'https://www.fao.org/land-water/databases-and-software/crop-information/soybean/ru/', 'https://www.fao.org/land-water/databases-and-software/crop-information/soybean/ru/', 'https://www.fao.org/land-water/databases-and-software/crop-information/soybean/ru/',
   '2026-09-15', 'Moyenne', 't_base 6 et non 10 ; gdd_maturite 1910-2070 en base 6 ;', 'Les 10 °C correspondent au seuil de sol au semis, pas à la base des degrés-jours. t_base et gdd_maturite doivent être corrigés ensemble.'),
  ('BETTERAVE', 'Betterave sucrière', 'industrielle', 3, NULL,
   2400, -4, 650, 18, 22,
   30, 'jeune plante (gel)', 'hors_perimetre', 'ITB / IRBAB-KBIVB / FAO',
   'https://www.irbab-kbivb.be/wp-content/uploads/2018/04/Pr%C3%A9paration-semis.pdf', NULL, 'https://www.larousse.fr/archives/agricole/page/73', 'https://www.itbfr.org/tous-les-articles/article/news/episode-de-gel-dans-quels-cas-faut-il-ressemer-1',
   'https://www.fao.org/land-water/databases-and-software/crop-information/sugarbeet/fr', 'https://www.fao.org/land-water/databases-and-software/crop-information/sugarbeet/fr', 'https://www.fao.org/land-water/databases-and-software/crop-information/sugarbeet/fr',
   '2026-09-15', 'Moyenne', 'besoin_eau 400-600 selon l''ITB contre 550-750 selon la FAO', 'Les 3 °C sont un seuil d''activité de la graine, pas une température de base de degrés-jours.'),
  ('POMME_TERRE', 'Pomme de terre', 'tubercule', 7, NULL,
   1500, -2, 600, 15, 20,
   28, 'feuillage (gel)', 'hors_perimetre', 'FAO / INRAE Ephytia',
   'https://www.arvalis.fr/infos-techniques/pommes-de-terre-un-climat-qui-favorise-les-defauts-physiologiques-pouvant-alterer', NULL, 'https://blog.spotifarm.fr/tour-de-plaine-spotifarm/somme-de-temperature-pourquoi-suivre-levolution-des-degres-jours', 'https://ephytia.inrae.fr/fr/C/21109/Pomme-de-terre-Gel-ou-froid',
   'https://www.fao.org/land-water/databases-and-software/crop-information/potato/ru', 'https://ephytia.inrae.fr/fr/C/23964/Tropileg-Pomme-de-terre', 'https://ephytia.inrae.fr/fr/C/23964/Tropileg-Pomme-de-terre',
   '2026-09-16', 'Elevee', NULL, 'La filière raisonne en jours de cycle par groupe de précocité, pas en degrés-jours.'),
  ('VIGNE', 'Vigne (raisin de cuve)', 'perenne', 10, NULL,
   1300, -2, 400, 25, 30,
   35, 'débourrement / pointe verte (gel)', 'MVP', 'Huglin 1978 / Chambre d''agriculture du Var / OENO One',
   'https://www-iuem.univ-brest.fr/wapps/letg/adviclim/BDX/PDF/CR_Acad%C3%A9mie_agriculture_1978_64_Huglin.pdf', NULL, 'https://ives-openscience.eu/wp-content/uploads/2023/03/Heat_Requirements_Grapevine_Van_Leeuwen.pdf', 'https://paca.chambres-agriculture.fr/fileadmin/user_upload/257_chambres_dagriculture_provence-alpes-cote_dazur/CA83/Documents/Pages/Fiche_post_alea_Gel_-_Viticulture.pdf',
   'https://www.vignevin-occitanie.com/vignobles-innovants-et-ecoresponsables-fiches-pratiques/irrigation-et-profil-produit-dun-vie/', 'https://oeno-one.eu/article/view/1587', 'https://vignevin-charentes.com/wp-content/uploads/2024/11/ADAPTATION-AU-STRESS-HYDRIQUE-ET-THERMIQUE.pdf',
   '2026-09-16', 'Elevee', 'gdd varie de 1204 à 1940 selon le cépage', 'Seuil de gel très dépendant du stade : -2 °C à la pointe verte mais sous -8 °C en bourgeon dormant.'),
  ('OLIVIER', 'Olivier', 'perenne', 10, NULL,
   NULL, -8, 300, 25, 32,
   40, 'jeune plant et bourgeons (gel)', 'hors_perimetre', 'France Olive - AFIDOL / FAO',
   'https://www.franceolive.fr/categorie/connaissance-de-l-arbre/presentation-de-l-arbre', NULL, 'https://www.fao.org/4/i2800e/i2800e09.pdf', 'https://www.franceolive.fr/categorie/connaissance-de-l-arbre/presentation-de-l-arbre',
   'https://franceolive.fr/wp-content/uploads/2021/10/SITEVI-2021-bien-maitriser-irrigation-mieux-produire.pdf', 'https://www.mdpi.com/2073-4395/11/8/1492', 'https://www.fao.org/4/i2800e/i2800e09.pdf',
   '2026-09-16', 'Faible', 't_opt 16-25 et non 25-32 ; seuil_stress 35 et non 40', 'Pas de degrés-jours de maturité : cycle reproductif de 15 à 18 mois et besoin de froid hivernal. Les -8 °C valent pour un jeune plant, -17 à -18 °C pour un arbre adulte.');

-- --- 2 horizons climatiques -----------------------------------------
-- Deux periodes de MEME longueur, dix ans chacune. L'API s'arretant en
-- 2050, la projection va de 2041 a 2050 et non de 2041 a 2060.
INSERT INTO Dim_Temps (id_horizon, libelle, annee_debut, annee_fin, type) VALUES
  ('REF_2011_2020',  'Reference 2011-2020',  2011, 2020, 'reference'),
  ('PROJ_2041_2050', 'Projection 2041-2050', 2041, 2050, 'projection');


-- --- 2 modeles climatiques ------------------------------------------
-- EC_Earth3P_HR a renvoye des series vides lors de nos tests du 30/09 et
-- a ete ecarte. Les deux modeles retenus ont ete verifies sur Reims 2049.
INSERT INTO Dim_Modele (id_modele, nom_complet, institution, pays,
                        resolution_native_km, variables_disponibles,
                        date_verification, remarque) VALUES
  ('MRI_AGCM3_2_S', 'MRI-AGCM3-2-S', 'Meteorological Research Institute', 'Japon',
   20, 'temperature_2m_min, temperature_2m_max, temperature_2m_mean, precipitation_sum',
   '2026-09-30',
   'Amplitude annuelle plus large : 28 jours de gel et 16 jours au-dessus de 30 degres sur Reims 2049.'),
  ('CMCC_CM2_VHR4', 'CMCC-CM2-VHR4', 'Centro Euro-Mediterraneo sui Cambiamenti Climatici', 'Italie',
   30, 'temperature_2m_min, temperature_2m_max, temperature_2m_mean, precipitation_sum',
   '2026-09-30',
   'Hivers plus doux et etes plus chauds : 11 jours de gel et 28 jours au-dessus de 30 degres sur Reims 2049.');


-- --- Fenetres de calcul ----------------------------------------------
-- Un indicateur n'est pas une regle, c'est une regle ET une periode.
--
-- La ligne la plus parlante est le couple VIGNE / gel et VIGNE / gel_dormance :
-- la meme culture, le meme phenomene, deux seuils separes par 6 degres selon
-- le stade. C'est ce que seul un seuil par fenetre permet de representer.
INSERT INTO Fenetre_Calcul (id_culture, indicateur, mois_debut, mois_fin,
                            seuil_specifique, commentaire) VALUES
  -- Ble tendre d'hiver
  ('BLE_TENDRE_H', 'gdd',             10,  7, NULL, 'Semis d octobre a la recolte de juillet, base 0'),
  ('BLE_TENDRE_H', 'gel',              3,  5, -4.0, 'Gel d epi, peu apres le stade epi 1 cm (ARVALIS 2017)'),
  ('BLE_TENDRE_H', 'echaudage',        4,  6, NULL, 'AgriClim retient 25 degres, notre referentiel 30 : a arbitrer en J3'),
  ('BLE_TENDRE_H', 'bilan_hydrique',   4, 10, NULL, 'Periode de consommation en eau'),
  -- Mais grain
  ('MAIS_GRAIN',   'gdd',              4, 10, NULL, 'Base 6 avec ecretage de Tmax a 30 (formule ARVALIS)'),
  ('MAIS_GRAIN',   'gel',              9, 10,  0.0, 'Gel de fin de cycle : degats aux feuilles des 0 degre'),
  ('MAIS_GRAIN',   'stress_thermique', 7,  8, NULL, 'Floraison, periode la plus sensible'),
  ('MAIS_GRAIN',   'bilan_hydrique',   4, 10, NULL, NULL),
  -- Vigne
  ('VIGNE',        'gdd',              4,  9, NULL, 'Base 10 du 1er avril au 30 septembre (Huglin 1978)'),
  ('VIGNE',        'gel',              3,  5, -2.0, 'Debourrement, stade pointe verte : le bourgeon est ouvert'),
  ('VIGNE',        'gel_dormance',    11,  2, -8.0, 'Bourgeon dormant : la vigne supporte bien plus froid'),
  ('VIGNE',        'stress_thermique', 7,  8, NULL, 'Blocage de maturite'),
  ('VIGNE',        'bilan_hydrique',   4, 10, NULL, NULL),
  -- Tournesol
  ('TOURNESOL',    'gdd',              4,  9, NULL, 'Base 6'),
  ('TOURNESOL',    'gel',              4,  5, -1.0, 'Sensibilite a la levee'),
  ('TOURNESOL',    'stress_thermique', 7,  8, NULL, NULL),
  ('TOURNESOL',    'bilan_hydrique',   4, 10, NULL, NULL);


-- --- Controle ---------------------------------------------------------
SELECT 'Dim_Commune'    AS table_remplie, COUNT(*) AS lignes FROM Dim_Commune
UNION ALL SELECT 'Dim_Culture',    COUNT(*) FROM Dim_Culture
UNION ALL SELECT 'Dim_Temps',      COUNT(*) FROM Dim_Temps
UNION ALL SELECT 'Dim_Modele',     COUNT(*) FROM Dim_Modele
UNION ALL SELECT 'Fenetre_Calcul', COUNT(*) FROM Fenetre_Calcul;
-- Attendu : 16, 10, 2, 2, 17
