# Conception RGPD

SAÉ 3.01 « Climat & Cultures », équipe 9.
BUT Informatique, IUT de Créteil-Vitry, site de Vitry-sur-Seine.
Version 2, 17 octobre 2026, jalon 2.

## 1. Le constat de départ

**Le cœur de notre application ne traite aucune donnée personnelle.**

Les projections climatiques viennent d'Open-Meteo, les seuils agronomiques
d'instituts techniques, les communes de l'API Géo. Ce sont des données
publiques de référence. Un indicateur comme « 1 jour de gel au débourrement
sur la vigne à Reims entre 2041 et 2050 » ne concerne personne en particulier :
il est identique pour tous les visiteurs.

Le RGPD n'entre donc en jeu que sur une partie périphérique : la session de
navigation, les comptes utilisateurs et les favoris (inscrits en
« Souhaitable » dans notre backlog), ainsi que les journaux techniques du
serveur.

## 2. Une erreur de conception que nous corrigeons

Notre premier document de modélisation prévoyait une colonne `id_session`
dans `Fact_Indicateur`, « pour isoler les données de chaque visiteur ».

C'était une erreur, pour trois raisons :

- Les faits sont **partagés**. Le nombre de jours de gel à Reims ne dépend
  pas de qui regarde l'écran.
- Dupliquer la table de faits par visiteur multiplierait son volume par le
  nombre d'utilisateurs, alors que nous disposons de 100 Mo sur AlwaysData.
- Marquer une donnée publique d'un identifiant de session la ferait entrer
  dans le champ du RGPD sans aucune nécessité. C'est l'inverse de la
  minimisation.

`Fact_Indicateur` ne contient donc **aucun identifiant de personne**. Les
données personnelles vivent dans des tables séparées, décrites plus bas.

## 3. Les données que nous traitons

| Donnée | Finalité | Base légale | Conservation |
|---|---|---|---|
| Identifiant de session (UUID aléatoire) | Retenir les filtres entre deux pages et les favoris d'un visiteur sans compte | Intérêt légitime ; cookie strictement nécessaire au service demandé, exempté de consentement (art. 82 de la loi Informatique et Libertés) | 30 jours après sa création |
| Favoris liés à une session (commune, culture) | Retrouver ses analyses sans créer de compte | Intérêt légitime | 30 jours, supprimés avec la session |
| Adresse e-mail | Identifier un compte persistant | Exécution du contrat (conditions d'utilisation acceptées à l'inscription) | Jusqu'à suppression du compte |
| Mot de passe (empreinte) | Authentifier | Exécution du contrat | Jusqu'à suppression du compte |
| Favoris liés à un compte (commune, culture) | Retrouver ses analyses | Exécution du contrat | Jusqu'à suppression du compte |
| Date de dernière visite (`derniere_visite`) | Détecter et purger les comptes inactifs | Intérêt légitime | Jusqu'à suppression du compte, au plus 24 mois d'inactivité |
| Adresse IP (journaux du serveur) | Sécurité et diagnostic technique | Intérêt légitime | Durée fixée par l'hébergeur : [à vérifier chez AlwaysData] |

**L'identifiant de session est une donnée pseudonymisée.** Il ne permet pas
de nous identifier directement, mais il est rattaché à un navigateur : il
relève donc du RGPD (considérant 30), même s'il ne porte aucune information
en lui-même.

Le compte est **facultatif**. L'application est entièrement utilisable sans
en créer un : c'est l'application du principe de minimisation.

## 4. Ce que nous ne collectons pas

Et c'est volontaire, chaque ligne étant une décision :

- Pas de nom, prénom, adresse postale ni téléphone.
- Pas de géolocalisation. L'utilisateur choisit une commune dans une liste
  de seize, il ne partage jamais sa position.
- Pas de cookie publicitaire ni de traceur tiers. Aucun outil de mesure
  d'audience externe.
- Pas d'exploitation des adresses IP. Elles figurent dans les journaux
  techniques tenus par l'hébergeur, ce qui reste un traitement (voir le
  tableau de la section 3), mais nous ne les utilisons à aucune autre fin
  que la sécurité et le diagnostic.
- Pas de données agricoles réelles. L'utilisateur ne déclare ni sa parcelle,
  ni son exploitation, ni ses rendements.

## 5. Structure retenue

Le script complet, avec les index utiles à la purge, est
`sql/03-tables-rgpd.sql`. Il s'exécute après `01-creation-base.sql`.

```sql
CREATE TABLE Session_Visiteur (
    id_session      CHAR(36)  NOT NULL,   -- UUID v4, donnee pseudonymisee
    date_creation   DATETIME  NOT NULL,
    date_expiration DATETIME  NOT NULL,   -- creation + 30 jours
    PRIMARY KEY (id_session)
);

CREATE TABLE Compte (
    id_compte       INT AUTO_INCREMENT,
    email           VARCHAR(255) NOT NULL UNIQUE,
    mot_de_passe    VARCHAR(255) NOT NULL,  -- empreinte bcrypt, jamais le clair
    date_creation   DATETIME     NOT NULL,
    derniere_visite DATETIME     NULL,
    PRIMARY KEY (id_compte)
);

CREATE TABLE Favori (
    id_favori   INT AUTO_INCREMENT,
    id_compte   INT         NULL,
    id_session  CHAR(36)    NULL,
    id_commune  CHAR(5)     NOT NULL,
    id_culture  VARCHAR(20) NOT NULL,
    PRIMARY KEY (id_favori),
    FOREIGN KEY (id_compte)  REFERENCES Compte (id_compte)        ON DELETE CASCADE,
    FOREIGN KEY (id_session) REFERENCES Session_Visiteur (id_session) ON DELETE CASCADE,
    FOREIGN KEY (id_commune) REFERENCES Dim_Commune (id_commune),
    FOREIGN KEY (id_culture) REFERENCES Dim_Culture (id_culture),
    -- un favori appartient a un compte OU a une session, jamais aux deux ni a aucun
    CHECK ((id_compte IS NULL) <> (id_session IS NULL))
);
```

Les `ON DELETE CASCADE` ne sont pas un détail technique : ils réalisent le
droit à l'effacement. Supprimer un compte supprime ses favoris dans la même
transaction, sans script de nettoyage à lancer à la main. De même, la purge
d'une session expirée emporte les favoris qui lui sont liés.

La contrainte `CHECK` garantit qu'aucun favori ne reste orphelin, donc
qu'aucune donnée n'échappe à la purge. Elle est appliquée à partir de
MySQL 8.0.16 ; les versions antérieures l'ignorent sans erreur.

## 6. Les droits des personnes

| Droit | Mise en œuvre |
|---|---|
| Accès | Une page « Mes données » affiche tout ce que le compte contient |
| Rectification | L'adresse e-mail est modifiable depuis la même page |
| Effacement | Un bouton « Supprimer mon compte », effet immédiat, cascade comprise |
| Limitation | Sur demande à l'adresse de contact : le compte est gelé (plus d'utilisation des données) le temps de traiter une contestation |
| Portabilité | Export JSON de toutes les données du compte : e-mail, date de création, date de dernière visite et favoris |
| Opposition | Refuser le cookie de session reste possible : l'application fonctionne, elle ne retient simplement plus les filtres ni les favoris anonymes |
| Réclamation | Toute personne peut saisir la CNIL (cnil.fr) si elle estime que ses droits ne sont pas respectés |

Les demandes qui ne passent pas par l'interface, par exemple quand
l'utilisateur ne peut plus se connecter, sont adressées à
[adresse de contact à compléter]. Nous y répondons dans un délai d'**un mois**,
comme le prévoit l'article 12.

Un visiteur sans compte n'a pas de démarche à faire. Effacer le cookie rend sa
session inutilisable : personne ne peut plus la relier à lui. La ligne
correspondante et ses favoris restent sur le serveur jusqu'à leur expiration,
puis sont supprimés automatiquement, au plus tard 30 jours après la création
de la session.

## 7. Mesures techniques

**Mots de passe.** Empreinte bcrypt avec sel, jamais de stockage en clair,
jamais de chiffrement réversible.

**Secrets.** Aucun identifiant de connexion dans le dépôt. Le fichier `.env`
est dans `.gitignore` depuis le jalon 0, et `.env.example` ne contient que
des noms de variables sans valeur.

**Transport.** HTTPS sur AlwaysData.

**Accès à la base.** AlwaysData interdit les connexions distantes à MySQL
sur le plan gratuit. Cette contrainte, qui nous gêne en développement, est
aussi une protection : la base n'est joignable que depuis le serveur.

**Purge.** Une tâche planifiée AlwaysData exécute chaque nuit deux
suppressions :

- les sessions dont `date_expiration` est dépassée, et par cascade leurs
  favoris ;
- les comptes dont `derniere_visite` remonte à plus de 24 mois, après un
  e-mail d'avertissement resté sans reconnexion pendant 30 jours.

## 8. Mentions à afficher

Deux pages, prévues dans les maquettes sous « Mentions légales » et
« Données personnelles » :

- Le responsable du traitement. Dans ce cadre pédagogique, c'est
  l'établissement : l'Université Paris-Est Créteil (UPEC), dont dépend
  l'IUT de Créteil-Vitry (BUT Informatique, site de Vitry-sur-Seine).
  L'équipe projet en est le contact.
- L'hébergeur, obligatoire au titre de la LCEN : AlwaysData, avec sa raison
  sociale et son adresse.
- Quelles données, pour quoi, sur quelle base légale et combien de temps : ce
  que reprend le tableau de la section 3.
- Le cookie de session, sa finalité et sa durée.
- Comment exercer ses droits, l'adresse de contact, le délai de réponse et la
  possibilité de saisir la CNIL.
- L'attribution **CC BY 4.0** des données Open-Meteo, qui relève du droit
  d'auteur et non du RGPD, mais qui a sa place sur la même page.

## 9. Limite assumée

Ce document décrit une conception, pas un traitement en production. Le projet
est pédagogique, il n'y a ni utilisateurs réels, ni registre des traitements
au sens de l'article 30, ni analyse d'impact.

Si l'application devait être mise en service, trois points demanderaient un
examen :

- **La durée de conservation des comptes inactifs.** Les 24 mois retenus
  suivent les pratiques courantes, mais ils seraient à justifier.
- **L'hébergeur comme sous-traitant.** AlwaysData traite des données pour
  notre compte : c'est un sous-traitant au sens de l'article 28. Il faudrait
  vérifier que ses conditions générales contiennent bien les clauses de
  sous-traitance exigées.
- **La localisation des serveurs.** AlwaysData est une société française ;
  le pays d'hébergement des serveurs reste à confirmer :
  [à vérifier chez AlwaysData].
