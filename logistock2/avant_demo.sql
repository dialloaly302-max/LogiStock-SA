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
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES
(1,'Can add log entry',1,'add_logentry'),
(2,'Can change log entry',1,'change_logentry'),
(3,'Can delete log entry',1,'delete_logentry'),
(4,'Can view log entry',1,'view_logentry'),
(5,'Can add permission',2,'add_permission'),
(6,'Can change permission',2,'change_permission'),
(7,'Can delete permission',2,'delete_permission'),
(8,'Can view permission',2,'view_permission'),
(9,'Can add group',3,'add_group'),
(10,'Can change group',3,'change_group'),
(11,'Can delete group',3,'delete_group'),
(12,'Can view group',3,'view_group'),
(13,'Can add content type',4,'add_contenttype'),
(14,'Can change content type',4,'change_contenttype'),
(15,'Can delete content type',4,'delete_contenttype'),
(16,'Can view content type',4,'view_contenttype'),
(17,'Can add session',5,'add_session'),
(18,'Can change session',5,'change_session'),
(19,'Can delete session',5,'delete_session'),
(20,'Can view session',5,'view_session'),
(21,'Can add utilisateur',6,'add_utilisateur'),
(22,'Can change utilisateur',6,'change_utilisateur'),
(23,'Can delete utilisateur',6,'delete_utilisateur'),
(24,'Can view utilisateur',6,'view_utilisateur');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
(6,'Toure','Leila','92666681','Kweite',0,1),
(7,'Essai','client','60000000',NULL,30000,0),
(8,'EssaiVente','Test',NULL,NULL,5000,1);
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
(5,8,4,6500),
(6,1,1,2500),
(6,8,2,6500),
(7,10,2,1500),
(8,10,6,1500),
(9,10,1,1500),
(10,10,2,1500),
(11,10,1,1500),
(12,10,3,1500);
/*!40000 ALTER TABLE `contenir` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_utilisateur_id_utilisateur` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_utilisateur_id_utilisateur` FOREIGN KEY (`user_id`) REFERENCES `utilisateur` (`id_utilisateur`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES
(1,'admin','logentry'),
(3,'auth','group'),
(2,'auth','permission'),
(6,'comptes','utilisateur'),
(4,'contenttypes','contenttype'),
(5,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES
(1,'contenttypes','0001_initial','2026-11-09 10:02:19.219668'),
(2,'comptes','0001_initial','2026-11-09 10:02:19.226340'),
(3,'admin','0001_initial','2026-11-09 10:02:19.368533'),
(4,'admin','0002_logentry_remove_auto_add','2026-11-09 10:02:19.377263'),
(5,'admin','0003_logentry_add_action_flag_choices','2026-11-09 10:02:19.385265'),
(6,'contenttypes','0002_remove_content_type_name','2026-11-09 10:02:19.460737'),
(7,'auth','0001_initial','2026-11-09 10:02:19.694379'),
(8,'auth','0002_alter_permission_name_max_length','2026-11-09 10:02:19.780837'),
(9,'auth','0003_alter_user_email_max_length','2026-11-09 10:02:19.799295'),
(10,'auth','0004_alter_user_username_opts','2026-11-09 10:02:19.810908'),
(11,'auth','0005_alter_user_last_login_null','2026-11-09 10:02:19.823199'),
(12,'auth','0006_require_contenttypes_0002','2026-11-09 10:02:19.825396'),
(13,'auth','0007_alter_validators_add_error_messages','2026-11-09 10:02:19.837711'),
(14,'auth','0008_alter_user_username_max_length','2026-11-09 10:02:19.846669'),
(15,'auth','0009_alter_user_last_name_max_length','2026-11-09 10:02:19.857361'),
(16,'auth','0010_alter_group_name_max_length','2026-11-09 10:02:19.892413'),
(17,'auth','0011_update_proxy_permissions','2026-11-09 10:02:19.907886'),
(18,'auth','0012_alter_user_first_name_max_length','2026-11-09 10:02:19.917965'),
(19,'sessions','0001_initial','2026-11-09 10:02:19.962930');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES
('leof74p0zer6ugr5576k6hyq5t0e8mkf','.eJxVjDsOwjAQBe_iGln-xD9Kes5geb1rHECOFCcV4u5gKQW0M_Pei8W0bzXundY4IzszyU6_DFJ-UBsC76ndFp6Xtq0z8JHww3Z-XZCel6P9O6ip17EmD0o6q9CQFmECF_IXFQQIZKXQGTNNppC02mJBnZyyXltIpiihPHt_AP9aOGk:1xR3Lq:REHS6aCv8lUR2rJPl6HjTgSx3gh_pHpcKRzdH1G9Bhw','2026-11-25 08:06:38.234579'),
('tibenvgj4ltmfkyjkw3pb2qml6he9nne','.eJxVjDsOwjAQBe_iGln-xD9Kes5geb1rHECOFCcV4u5gKQW0M_Pei8W0bzXundY4IzszyU6_DFJ-UBsC76ndFp6Xtq0z8JHww3Z-XZCel6P9O6ip17EmD0o6q9CQFmECF_IXFQQIZKXQGTNNppC02mJBnZyyXltIpiihPHt_AP9aOGk:1xR3Mt:ZtQUVP9qiRRLUelxPo03SgFuxKECfcjYYLljMWomxsA','2026-11-25 08:07:43.359403');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `paiement`
--

LOCK TABLES `paiement` WRITE;
/*!40000 ALTER TABLE `paiement` DISABLE KEYS */;
INSERT INTO `paiement` VALUES
(1,'2026-11-06 08:30:00',50000,2,3),
(2,'2026-11-13 20:44:33',500,8,1),
(3,'2026-11-13 20:45:19',1000,8,1);
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
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
(8,'CALC','Calculatrice','pièce',4000,6500,15,5),
(10,'ESSAI2','Essai stock (ne pas utiliser)','500',1000,1500,10,3);
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
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
(16,'2026-11-06 09:10:00','sortie',2,23,'Vente V-0005',7,3,5),
(17,'2026-11-10 18:07:50','entree',10,10,'Approvisionnement',10,1,NULL),
(18,'2026-11-10 18:11:39','entree',2,12,'Inventaire',10,1,NULL),
(19,'2026-11-10 18:13:54','sortie',4,8,'Inventaire',10,1,NULL),
(20,'2026-11-12 10:29:23','sortie',1,89,'Vente V-0006',1,1,6),
(21,'2026-11-12 10:29:23','sortie',2,12,'Vente V-0006',8,1,6),
(22,'2026-11-12 10:40:35','entree',10,18,'Approvisionnement',10,1,NULL),
(23,'2026-11-12 10:52:34','sortie',2,16,'Vente V-0007',10,1,7),
(24,'2026-11-12 10:58:45','sortie',6,10,'Vente V-0008',10,1,8),
(25,'2026-11-12 11:06:39','sortie',1,9,'Vente V-0009',10,1,9),
(26,'2026-11-12 11:12:34','sortie',2,7,'Vente V-0010',10,7,10),
(27,'2026-11-12 11:13:47','sortie',1,6,'Vente V-0011',10,7,11),
(28,'2026-11-12 17:34:32','sortie',3,3,'Vente V-0012',10,1,12),
(29,'2026-11-13 20:37:51','entree',1,90,'Correction : annulation de V-0006',1,1,6),
(30,'2026-11-13 20:37:51','entree',2,14,'Correction : annulation de V-0006',8,1,6),
(31,'2026-11-13 20:49:10','entree',1,4,'Correction : annulation de V-0011',10,7,11);
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
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `utilisateur`
--

LOCK TABLES `utilisateur` WRITE;
/*!40000 ALTER TABLE `utilisateur` DISABLE KEYS */;
INSERT INTO `utilisateur` VALUES
(1,'Diallo','Aly','AD18','pbkdf2_sha256$1000000$dnFVpHYItdgGQEe1pRnPLV$tR674YUPk0G61rWjFRqaFBHURUHNHIJwZ01mrGTIGOY=','70000000','Bamako','administrateur',1,0,NULL,'2026-11-15 08:40:10'),
(2,'Tolo','Ousmane','OT99','pbkdf2_sha256$1000000$Jbjo7ihvC06kmrHu4V0xRZ$P/ygka8deoJZY1tnZOKvPAVyD33f+SaYaP3SXGiTAVg=','60532824','Baco-Djicoroni ACI','manager',1,0,NULL,'2026-11-14 15:58:25'),
(3,'Diallo','Pointeur','DP00','pbkdf2_sha256$1000000$LD4ZTpYfmk7UrnJ7ZRz6pW$9MkpQXjuQ9lrsARmqQxs1Mc1TVi7E/rjWf36Ixz+/LQ=','89458881','Moussabougou','gestionnaire_ventes',1,3,NULL,NULL),
(4,'Couloubaly','Mohamed','CM01','pbkdf2_sha256$720000$M8cMVm2hTd0MEf55nCtiTC$/SUGcaUV1ra6gPdfIQsV5HIhgGoKk5EMosa0rZjcu/g=','82703732','Bozolla Lampani Coro','gestionnaire_stock',0,0,NULL,NULL),
(5,'Banou','Fati','BF02','pbkdf2_sha256$720000$wbLzoMgwuvpqcQJJl0tv6D$DqGZFKk9KOxwoNMasAy81mDdta2LOrhAsT3V22Ra1Mo=','60136095','Kati','gestionnaire_stock',0,0,NULL,NULL),
(6,'Fofana','Issa','IS41','pbkdf2_sha256$1000000$2CKG1syboCRLtqsZzQdD4y$hIWIYuLS2SFOAbvpjY8R3PrymB4lkqEZ8Imk3jBvg3o=','63422312','Badalabougou','gestionnaire_stock',1,0,NULL,'2026-11-13 20:50:21'),
(7,'VTEST','gr','VET65','pbkdf2_sha256$1000000$om8dbhPGrIG8GtDceDNo71$KESVAUlybUet7I7nLaPgxA43we2ri5LTile4HYv6Ny4=','52343456','kabala','gestionnaire_ventes',1,0,NULL,'2026-11-14 16:03:05'),
(8,'MTES',NULL,'MT5','pbkdf2_sha256$1000000$aXmGteIpHgEh3kw9kWSQB0$+onKRcaW6/I3EWUTNzy9JrmIlnBE8txmFGBv6hFmB/0=','50987654','baco','manager',1,0,NULL,'2026-11-12 11:36:30');
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
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
(5,'V-0005','2026-11-06 09:10:00','comptant',0,31000,'validee',NULL,NULL,6,3,NULL),
(6,'V-0006','2026-11-12 10:29:23','credit',5000,10500,'annulee','erreur','2026-11-13 20:37:51',2,1,1),
(7,'V-0007','2026-11-12 10:52:34','comptant',0,3000,'validee',NULL,NULL,8,1,NULL),
(8,'V-0008','2026-11-12 10:58:45','comptant',0,9000,'validee',NULL,NULL,8,1,NULL),
(9,'V-0009','2026-11-12 11:06:39','comptant',500,1000,'validee',NULL,NULL,8,1,NULL),
(10,'V-0010','2026-11-12 11:12:34','comptant',300,2700,'validee',NULL,NULL,8,7,NULL),
(11,'V-0011','2026-11-12 11:13:47','credit',0,1500,'annulee','debuit','2026-11-13 20:49:10',8,7,7),
(12,'V-0012','2026-11-12 17:34:32','comptant',0,4500,'validee',NULL,NULL,8,1,NULL);
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

-- Dump completed on 2026-11-15 19:40:10
