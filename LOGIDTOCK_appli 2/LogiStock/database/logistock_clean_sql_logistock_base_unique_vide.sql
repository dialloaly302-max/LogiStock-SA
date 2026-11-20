-- LOGISTOCK : Script SQL unique et propre (base vide, structure complète + modes de paiement + historique)
-- À importer UNE SEULE FOIS dans la base de données `logistock`.

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

CREATE DATABASE IF NOT EXISTS `logistock` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `logistock`;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `historique_vente`;
DROP TABLE IF EXISTS `paiement`;
DROP TABLE IF EXISTS `stock`;
DROP TABLE IF EXISTS `contenir`;
DROP TABLE IF EXISTS `vente`;
DROP TABLE IF EXISTS `produit`;
DROP TABLE IF EXISTS `client`;
DROP TABLE IF EXISTS `categorie`;
DROP TABLE IF EXISTS `utilisateur`;
DROP TABLE IF EXISTS `mode_paiement`;
SET FOREIGN_KEY_CHECKS = 1;

-- --------------------------------------------------------
-- Structure de la table `categorie`
-- --------------------------------------------------------
CREATE TABLE `categorie` (
  `id_categorie` int(11) NOT NULL AUTO_INCREMENT,
  `nom_categorie` varchar(100) NOT NULL,
  PRIMARY KEY (`id_categorie`),
  UNIQUE KEY `nom_categorie` (`nom_categorie`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Structure de la table `client`
-- --------------------------------------------------------
CREATE TABLE `client` (
  `id_client` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `prenom` varchar(75) NOT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `adresse` varchar(150) DEFAULT NULL,
  `plafond` int(11) NOT NULL DEFAULT 100000,
  `actif` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_client`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Structure de la table `produit`
-- --------------------------------------------------------
CREATE TABLE `produit` (
  `id_produit` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(30) NOT NULL,
  `designation` varchar(150) NOT NULL,
  `unite` varchar(20) DEFAULT NULL,
  `prix_achat` int(11) NOT NULL CHECK (`prix_achat` >= 0),
  `prix_vente` int(11) NOT NULL CHECK (`prix_vente` >= 0),
  `seuil_minimal` int(11) NOT NULL DEFAULT 15 CHECK (`seuil_minimal` >= 0),
  `id_categorie` int(11) NOT NULL,
  PRIMARY KEY (`id_produit`),
  UNIQUE KEY `code` (`code`),
  KEY `fk_produit_categorie` (`id_categorie`),
  CONSTRAINT `fk_produit_categorie` FOREIGN KEY (`id_categorie`) REFERENCES `categorie` (`id_categorie`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Structure de la table `utilisateur`
-- --------------------------------------------------------
CREATE TABLE `utilisateur` (
  `id_utilisateur` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `prenom` varchar(75) NOT NULL,
  `identifiant` varchar(50) NOT NULL,
  `mot_de_passe` varchar(255) NOT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `adresse` varchar(150) DEFAULT NULL,
  `role` varchar(30) NOT NULL,
  `actif` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_utilisateur`),
  UNIQUE KEY `identifiant` (`identifiant`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Structure de la table `mode_paiement`
-- --------------------------------------------------------
CREATE TABLE `mode_paiement` (
  `id_mode` int(11) NOT NULL AUTO_INCREMENT,
  `nom_mode` varchar(30) NOT NULL,
  `est_credit` tinyint(1) NOT NULL DEFAULT 0,
  `actif` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_mode`),
  UNIQUE KEY `nom_mode` (`nom_mode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `mode_paiement` (`nom_mode`, `est_credit`, `actif`) VALUES
('Espèces', 0, 1),
('Orange Money', 0, 1),
('Moov Money', 0, 1),
('Virement bancaire', 0, 1),
('Chèque', 0, 1),
('Carte bancaire', 0, 1),
('Crédit', 1, 1);

-- --------------------------------------------------------
-- Structure de la table `vente`
-- --------------------------------------------------------
CREATE TABLE `vente` (
  `id_vente` int(11) NOT NULL AUTO_INCREMENT,
  `reference` varchar(30) NOT NULL,
  `date_vente` datetime NOT NULL DEFAULT current_timestamp(),
  `mode_paiement` varchar(10) NOT NULL CHECK (`mode_paiement` in ('comptant','credit')),
  `id_mode` int(11) DEFAULT NULL,
  `remise` int(11) NOT NULL DEFAULT 0 CHECK (`remise` >= 0),
  `montant_total` int(11) NOT NULL DEFAULT 0 CHECK (`montant_total` >= 0),
  `statut` varchar(20) NOT NULL DEFAULT 'en_cours' CHECK (`statut` in ('en_cours','validee','annulee')),
  `id_client` int(11) NOT NULL,
  `id_utilisateur` int(11) NOT NULL,
  `motif_annulation` varchar(255) DEFAULT NULL,
  `annule_par` int(11) DEFAULT NULL,
  `date_annulation` datetime DEFAULT NULL,
  PRIMARY KEY (`id_vente`),
  UNIQUE KEY `reference` (`reference`),
  KEY `fk_vente_client` (`id_client`),
  KEY `fk_vente_utilisateur` (`id_utilisateur`),
  KEY `fk_vente_mode` (`id_mode`),
  CONSTRAINT `fk_vente_client` FOREIGN KEY (`id_client`) REFERENCES `client` (`id_client`),
  CONSTRAINT `fk_vente_utilisateur` FOREIGN KEY (`id_utilisateur`) REFERENCES `utilisateur` (`id_utilisateur`),
  CONSTRAINT `fk_vente_mode` FOREIGN KEY (`id_mode`) REFERENCES `mode_paiement` (`id_mode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Structure de la table `contenir`
-- --------------------------------------------------------
CREATE TABLE `contenir` (
  `id_vente` int(11) NOT NULL,
  `id_produit` int(11) NOT NULL,
  `quantite` int(11) NOT NULL CHECK (`quantite` > 0),
  `prix_unitaire` int(11) NOT NULL CHECK (`prix_unitaire` >= 0),
  PRIMARY KEY (`id_vente`,`id_produit`),
  KEY `fk_contenir_produit` (`id_produit`),
  CONSTRAINT `fk_contenir_produit` FOREIGN KEY (`id_produit`) REFERENCES `produit` (`id_produit`),
  CONSTRAINT `fk_contenir_vente` FOREIGN KEY (`id_vente`) REFERENCES `vente` (`id_vente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Structure de la table `stock`
-- --------------------------------------------------------
CREATE TABLE `stock` (
  `id_stock` int(11) NOT NULL AUTO_INCREMENT,
  `date_mouvement` datetime NOT NULL DEFAULT current_timestamp(),
  `type_mouvement` varchar(20) NOT NULL CHECK (`type_mouvement` in ('entree','sortie')),
  `quantite` int(11) NOT NULL CHECK (`quantite` > 0),
  `quantite_restante` int(11) NOT NULL CHECK (`quantite_restante` >= 0),
  `id_produit` int(11) NOT NULL,
  `id_utilisateur` int(11) NOT NULL,
  `id_vente` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_stock`),
  KEY `fk_stock_produit` (`id_produit`),
  KEY `fk_stock_utilisateur` (`id_utilisateur`),
  KEY `fk_stock_vente` (`id_vente`),
  CONSTRAINT `fk_stock_produit` FOREIGN KEY (`id_produit`) REFERENCES `produit` (`id_produit`),
  CONSTRAINT `fk_stock_utilisateur` FOREIGN KEY (`id_utilisateur`) REFERENCES `utilisateur` (`id_utilisateur`),
  CONSTRAINT `fk_stock_vente` FOREIGN KEY (`id_vente`) REFERENCES `vente` (`id_vente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Structure de la table `paiement`
-- --------------------------------------------------------
CREATE TABLE `paiement` (
  `id_paiement` int(11) NOT NULL AUTO_INCREMENT,
  `id_client` int(11) NOT NULL,
  `montant` int(11) NOT NULL CHECK (`montant` > 0),
  `date_paiement` datetime NOT NULL DEFAULT current_timestamp(),
  `id_utilisateur` int(11) NOT NULL,
  PRIMARY KEY (`id_paiement`),
  KEY `fk_paiement_client` (`id_client`),
  CONSTRAINT `fk_paiement_client` FOREIGN KEY (`id_client`) REFERENCES `client` (`id_client`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Structure de la table `historique_vente`
-- --------------------------------------------------------
CREATE TABLE `historique_vente` (
  `id_historique` int(11) NOT NULL AUTO_INCREMENT,
  `id_vente` int(11) NOT NULL,
  `action` varchar(20) NOT NULL,
  `details` varchar(255) DEFAULT NULL,
  `date_action` datetime NOT NULL,
  `id_utilisateur` int(11) NOT NULL,
  PRIMARY KEY (`id_historique`),
  KEY `idx_hv_vente` (`id_vente`),
  CONSTRAINT `fk_hv_vente` FOREIGN KEY (`id_vente`) REFERENCES `vente` (`id_vente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
