/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.11.16-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: logistock
-- ------------------------------------------------------
-- Server version	10.11.16-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `categorie`
--

DROP TABLE IF EXISTS `categorie`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `categorie` (
  `id_categorie` int(11) NOT NULL AUTO_INCREMENT,
  `nom_categorie` varchar(100) NOT NULL,
  PRIMARY KEY (`id_categorie`),
  UNIQUE KEY `uq_categorie_nom` (`nom_categorie`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categorie`
--

LOCK TABLES `categorie` WRITE;
/*!40000 ALTER TABLE `categorie` DISABLE KEYS */;
INSERT INTO `categorie` VALUES
(1,'Alimentation'),
(4,'Consommables'),
(2,'Electronique'),
(3,'Matériel de bureau'),
(5,'Petit équipement');
/*!40000 ALTER TABLE `categorie` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client`
--

DROP TABLE IF EXISTS `client`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `client` (
  `id_client` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `prenom` varchar(100) DEFAULT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `adresse` varchar(150) DEFAULT NULL,
  `plafond_credit` int(11) NOT NULL DEFAULT 0,
  `actif` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_client`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client`
--

LOCK TABLES `client` WRITE;
/*!40000 ALTER TABLE `client` DISABLE KEYS */;
INSERT INTO `client` VALUES
(1,'Soumare','Assan','76000000','Bamako',0,1),
(2,'Keita','Choupii','64056795','Lafiabougou',200000,1),
(3,'Pointeur','Myraaa','93033801','Djelibougou',100000,1),
(4,'Barry','Fanta','76157724','Niamakoro',150000,1),
(5,'Sidibe','Nassou','96130905','Cenou',50000,1),
(6,'Toure','Leila','92666681','Kweite',0,1);
/*!40000 ALTER TABLE `client` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contenir`
--

DROP TABLE IF EXISTS `contenir`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `contenir` (
  `id_vente` int(11) NOT NULL,
  `id_produit` int(11) NOT NULL,
  `quantite` int(11) NOT NULL,
  `prix_unitaire` int(11) NOT NULL,
  PRIMARY KEY (`id_vente`,`id_produit`),
  KEY `idx_contenir_produit` (`id_produit`),
  CONSTRAINT `fk_contenir_produit` FOREIGN KEY (`id_produit`) REFERENCES `produit` (`id_produit`),
  CONSTRAINT `fk_contenir_vente` FOREIGN KEY (`id_vente`) REFERENCES `vente` (`id_vente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contenir`
--

LOCK TABLES `contenir` WRITE;
/*!40000 ALTER TABLE `contenir` DISABLE KEYS */;
INSERT INTO `contenir` VALUES
(1,1,10,2500),
(2,5,20,3500),
(2,6,5,7500),
(3,4,1,250000),
(4,8,3,6500),
(5,7,2,2500),
(5,8,4,6500);
/*!40000 ALTER TABLE `contenir` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `paiement`
--

DROP TABLE IF EXISTS `paiement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `paiement` (
  `id_paiement` int(11) NOT NULL AUTO_INCREMENT,
  `date_paiement` datetime NOT NULL DEFAULT current_timestamp(),
  `montant` int(11) NOT NULL,
  `id_client` int(11) NOT NULL,
  `id_utilisateur` int(11) NOT NULL,
  PRIMARY KEY (`id_paiement`),
  KEY `idx_paiement_client` (`id_client`),
  KEY `idx_paiement_utilisateur` (`id_utilisateur`),
  CONSTRAINT `fk_paiement_client` FOREIGN KEY (`id_client`) REFERENCES `client` (`id_client`),
  CONSTRAINT `fk_paiement_utilisateur` FOREIGN KEY (`id_utilisateur`) REFERENCES `utilisateur` (`id_utilisateur`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `paiement`
--

LOCK TABLES `paiement` WRITE;
/*!40000 ALTER TABLE `paiement` DISABLE KEYS */;
INSERT INTO `paiement` VALUES
(1,'2026-11-06 08:30:00',50000,2,3);
/*!40000 ALTER TABLE `paiement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `produit`
--

DROP TABLE IF EXISTS `produit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `produit` (
  `id_produit` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(30) NOT NULL,
  `designation` varchar(150) NOT NULL,
  `unite` varchar(20) DEFAULT NULL,
  `prix_achat` int(11) NOT NULL,
  `prix_vente` int(11) NOT NULL,
  `seuil_minimal` int(11) NOT NULL DEFAULT 15,
  `id_categorie` int(11) NOT NULL,
  PRIMARY KEY (`id_produit`),
  UNIQUE KEY `uq_produit_code` (`code`),
  KEY `idx_produit_categorie` (`id_categorie`),
  CONSTRAINT `fk_produit_categorie` FOREIGN KEY (`id_categorie`) REFERENCES `categorie` (`id_categorie`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `produit`
--

LOCK TABLES `produit` WRITE;
/*!40000 ALTER TABLE `produit` DISABLE KEYS */;
INSERT INTO `produit` VALUES
(1,'THE','Thé','paquet',1000,2500,15,1),
(2,'TEL','Téléphone','pièce',250000,400000,15,2),
(3,'SUCRE','Sucre','kg',2500,3500,15,1),
(4,'ORDI','Ordinateur','pièce',150000,250000,15,2),
(5,'RAME','Ramette papier A4','ramette',2500,3500,15,4),
(6,'STYLO','Stylo bille (boîte de 50)','boîte',5000,7500,15,3),
(7,'AGRAF','Agrafeuse','pièce',1500,2500,15,5),
(8,'CALC','Calculatrice','pièce',4000,6500,15,5);
/*!40000 ALTER TABLE `produit` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock`
--

DROP TABLE IF EXISTS `stock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock` (
  `id_stock` int(11) NOT NULL AUTO_INCREMENT,
  `date_mouvement` datetime NOT NULL DEFAULT current_timestamp(),
  `type_mouvement` varchar(10) NOT NULL,
  `quantite` int(11) NOT NULL,
  `quantite_restante` int(11) NOT NULL,
  `motif` varchar(150) DEFAULT NULL,
  `id_produit` int(11) NOT NULL,
  `id_utilisateur` int(11) NOT NULL,
  `id_vente` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_stock`),
  KEY `idx_stock_produit` (`id_produit`),
  KEY `idx_stock_utilisateur` (`id_utilisateur`),
  KEY `idx_stock_vente` (`id_vente`),
  CONSTRAINT `fk_stock_produit` FOREIGN KEY (`id_produit`) REFERENCES `produit` (`id_produit`),
  CONSTRAINT `fk_stock_utilisateur` FOREIGN KEY (`id_utilisateur`) REFERENCES `utilisateur` (`id_utilisateur`),
  CONSTRAINT `fk_stock_vente` FOREIGN KEY (`id_vente`) REFERENCES `vente` (`id_vente`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock`
--

LOCK TABLES `stock` WRITE;
/*!40000 ALTER TABLE `stock` DISABLE KEYS */;
INSERT INTO `stock` VALUES
(1,'2026-11-02 09:00:00','entree',100,100,'Approvisionnement',1,4,NULL),
(2,'2026-11-02 09:05:00','entree',30,30,'Approvisionnement',2,4,NULL),
(3,'2026-11-02 09:10:00','entree',60,60,'Approvisionnement',3,5,NULL),
(4,'2026-11-02 09:15:00','entree',45,45,'Approvisionnement',4,5,NULL),
(5,'2026-11-02 09:20:00','entree',200,200,'Approvisionnement',5,5,NULL),
(6,'2026-11-02 09:25:00','entree',40,40,'Approvisionnement',6,5,NULL),
(7,'2026-11-02 09:30:00','entree',25,25,'Approvisionnement',7,5,NULL),
(8,'2026-11-02 09:35:00','entree',18,18,'Approvisionnement',8,5,NULL),
(9,'2026-11-04 18:55:54','sortie',10,90,'Vente V-0001',1,3,1),
(10,'2026-11-05 10:20:00','sortie',20,180,'Vente V-0002',5,3,2),
(11,'2026-11-05 10:20:00','sortie',5,35,'Vente V-0002',6,3,2),
(12,'2026-11-05 15:40:00','sortie',1,44,'Vente V-0003',4,3,3),
(13,'2026-11-05 16:30:00','sortie',3,15,'Vente V-0004',8,3,4),
(14,'2026-11-05 17:00:00','entree',3,18,'Correction : annulation de V-0004',8,1,4),
(15,'2026-11-06 09:10:00','sortie',4,14,'Vente V-0005',8,3,5),
(16,'2026-11-06 09:10:00','sortie',2,23,'Vente V-0005',7,3,5);
/*!40000 ALTER TABLE `stock` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `utilisateur`
--

DROP TABLE IF EXISTS `utilisateur`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `utilisateur` (
  `id_utilisateur` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `prenom` varchar(100) DEFAULT NULL,
  `identifiant` varchar(50) NOT NULL,
  `mot_de_passe` varchar(255) NOT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `adresse` varchar(150) DEFAULT NULL,
  `role` varchar(30) NOT NULL,
  `actif` tinyint(1) NOT NULL DEFAULT 1,
  `tentatives_echec` int(11) NOT NULL DEFAULT 0,
  `bloque_jusqua` datetime DEFAULT NULL,
  `last_login` datetime DEFAULT NULL,
  PRIMARY KEY (`id_utilisateur`),
  UNIQUE KEY `uq_utilisateur_identifiant` (`identifiant`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `utilisateur`
--

LOCK TABLES `utilisateur` WRITE;
/*!40000 ALTER TABLE `utilisateur` DISABLE KEYS */;
INSERT INTO `utilisateur` VALUES
(1,'Diallo','Aly','AD18','pbkdf2_sha256$720000$VEA0LMCgPLRrHM8Botfl0q$Hg8Y7OE2cwstBfq9NunSSCR2ZdsocHhlUQPlIybeO00=','70000000','Bamako','administrateur',1,0,NULL,NULL),
(2,'Tolo','Ousmane','OT99','pbkdf2_sha256$720000$HSCT1Nnn3qtCMvWDUfxACF$s5HdmpldO8VZbOrsXk7JgbSrE+hLyok8oNGX6KHDeRE=','60532824','Baco-Djicoroni ACI','manager',1,0,NULL,NULL),
(3,'Diallo','Pointeur','DP00','pbkdf2_sha256$720000$yfz2QHe2zLbFS4j0tdeUt8$0AvsPHsnW0dob4hVLHcD1qemv2GFOxoRnKaPFop1bIA=','89458881','Moussabougou','gestionnaire_ventes',1,0,NULL,NULL),
(4,'Couloubaly','Mohamed','CM01','pbkdf2_sha256$720000$M8cMVm2hTd0MEf55nCtiTC$/SUGcaUV1ra6gPdfIQsV5HIhgGoKk5EMosa0rZjcu/g=','82703732','Bozolla Lampani Coro','gestionnaire_stock',1,0,NULL,NULL),
(5,'Banou','Fati','BF02','pbkdf2_sha256$720000$wbLzoMgwuvpqcQJJl0tv6D$DqGZFKk9KOxwoNMasAy81mDdta2LOrhAsT3V22Ra1Mo=','60136095','Kati','gestionnaire_stock',1,0,NULL,NULL);
/*!40000 ALTER TABLE `utilisateur` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary table structure for view `v_solde_client`
--

DROP TABLE IF EXISTS `v_solde_client`;
/*!50001 DROP VIEW IF EXISTS `v_solde_client`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_solde_client` AS SELECT
 1 AS `id_client`,
  1 AS `nom`,
  1 AS `prenom`,
  1 AS `plafond_credit`,
  1 AS `solde` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_stock_actuel`
--

DROP TABLE IF EXISTS `v_stock_actuel`;
/*!50001 DROP VIEW IF EXISTS `v_stock_actuel`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_stock_actuel` AS SELECT
 1 AS `id_produit`,
  1 AS `code`,
  1 AS `designation`,
  1 AS `seuil_minimal`,
  1 AS `stock_actuel` */;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `vente`
--

DROP TABLE IF EXISTS `vente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `vente` (
  `id_vente` int(11) NOT NULL AUTO_INCREMENT,
  `reference` varchar(30) NOT NULL,
  `date_vente` datetime NOT NULL DEFAULT current_timestamp(),
  `mode_paiement` varchar(10) NOT NULL,
  `remise` int(11) NOT NULL DEFAULT 0,
  `montant_total` int(11) NOT NULL DEFAULT 0,
  `statut` varchar(20) NOT NULL DEFAULT 'en_cours',
  `motif_annulation` varchar(255) DEFAULT NULL,
  `date_annulation` datetime DEFAULT NULL,
  `id_client` int(11) NOT NULL,
  `id_utilisateur` int(11) NOT NULL,
  `id_utilisateur_annulation` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_vente`),
  UNIQUE KEY `uq_vente_reference` (`reference`),
  KEY `idx_vente_client` (`id_client`),
  KEY `idx_vente_utilisateur` (`id_utilisateur`),
  KEY `idx_vente_annul_utilisateur` (`id_utilisateur_annulation`),
  CONSTRAINT `fk_vente_annul_utilisateur` FOREIGN KEY (`id_utilisateur_annulation`) REFERENCES `utilisateur` (`id_utilisateur`),
  CONSTRAINT `fk_vente_client` FOREIGN KEY (`id_client`) REFERENCES `client` (`id_client`),
  CONSTRAINT `fk_vente_utilisateur` FOREIGN KEY (`id_utilisateur`) REFERENCES `utilisateur` (`id_utilisateur`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vente`
--

LOCK TABLES `vente` WRITE;
/*!40000 ALTER TABLE `vente` DISABLE KEYS */;
INSERT INTO `vente` VALUES
(1,'V-0001','2026-11-04 18:55:54','comptant',0,25000,'validee',NULL,NULL,1,3,NULL),
(2,'V-0002','2026-11-05 10:20:00','credit',2500,105000,'validee',NULL,NULL,2,3,NULL),
(3,'V-0003','2026-11-05 15:40:00','comptant',0,250000,'validee',NULL,NULL,4,3,NULL),
(4,'V-0004','2026-11-05 16:30:00','comptant',0,19500,'annulee','Erreur de saisie : le client a changé d\'avis','2026-11-05 17:00:00',5,3,1),
(5,'V-0005','2026-11-06 09:10:00','comptant',0,31000,'validee',NULL,NULL,6,3,NULL);
/*!40000 ALTER TABLE `vente` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Final view structure for view `v_solde_client`
--

/*!50001 DROP VIEW IF EXISTS `v_solde_client`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_solde_client` AS select `c`.`id_client` AS `id_client`,`c`.`nom` AS `nom`,`c`.`prenom` AS `prenom`,`c`.`plafond_credit` AS `plafond_credit`,coalesce((select sum(`v`.`montant_total`) from `vente` `v` where `v`.`id_client` = `c`.`id_client` and `v`.`mode_paiement` = 'credit' and `v`.`statut` = 'validee'),0) - coalesce((select sum(`p`.`montant`) from `paiement` `p` where `p`.`id_client` = `c`.`id_client`),0) AS `solde` from `client` `c` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_stock_actuel`
--

/*!50001 DROP VIEW IF EXISTS `v_stock_actuel`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_stock_actuel` AS select `p`.`id_produit` AS `id_produit`,`p`.`code` AS `code`,`p`.`designation` AS `designation`,`p`.`seuil_minimal` AS `seuil_minimal`,coalesce(sum(case when `s`.`type_mouvement` = 'entree' then `s`.`quantite` else -`s`.`quantite` end),0) AS `stock_actuel` from (`produit` `p` left join `stock` `s` on(`s`.`id_produit` = `p`.`id_produit`)) group by `p`.`id_produit`,`p`.`code`,`p`.`designation`,`p`.`seuil_minimal` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-09 10:53:25
