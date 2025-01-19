-- MySQL dump 10.13  Distrib 5.7.34, for Linux (x86_64)
--
-- Host: localhost    Database: cat
-- ------------------------------------------------------
-- Server version	5.7.34

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `audit`
--

DROP TABLE IF EXISTS `audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `audit` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user` varchar(50) DEFAULT NULL,
  `task_type` varchar(100) DEFAULT NULL,
  `task` varchar(5000) DEFAULT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user` (`user`),
  CONSTRAINT `audit_ibfk_1` FOREIGN KEY (`user`) REFERENCES `user` (`username`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit`
--

LOCK TABLES `audit` WRITE;
/*!40000 ALTER TABLE `audit` DISABLE KEYS */;
/*!40000 ALTER TABLE `audit` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cases`
--

DROP TABLE IF EXISTS `cases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cases` (
  `id` varchar(50) NOT NULL,
  `user` varchar(50) NOT NULL,
  `product` varchar(200) NOT NULL,
  `time` datetime NOT NULL,
  `comments` varchar(300) DEFAULT NULL,
  `mode` varchar(50) DEFAULT NULL,
  `priority` varchar(10) DEFAULT NULL,
  `assigned_by` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user` (`user`),
  KEY `product` (`product`),
  KEY `assigned_by` (`assigned_by`),
  CONSTRAINT `cases_ibfk_1` FOREIGN KEY (`user`) REFERENCES `user` (`username`),
  CONSTRAINT `cases_ibfk_2` FOREIGN KEY (`product`) REFERENCES `product` (`productname`),
  CONSTRAINT `cases_ibfk_3` FOREIGN KEY (`assigned_by`) REFERENCES `user` (`username`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cases`
--

LOCK TABLES `cases` WRITE;
/*!40000 ALTER TABLE `cases` DISABLE KEYS */;
/*!40000 ALTER TABLE `cases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jobs`
--

DROP TABLE IF EXISTS `jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `jobs` (
  `number` int(11) NOT NULL AUTO_INCREMENT,
  `id` varchar(200) DEFAULT NULL,
  `username` varchar(50) DEFAULT NULL,
  `job_type` varchar(100) DEFAULT NULL,
  `details` varchar(500) DEFAULT NULL,
  `time` datetime NOT NULL,
  `status` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`number`),
  KEY `username` (`username`),
  CONSTRAINT `jobs_ibfk_1` FOREIGN KEY (`username`) REFERENCES `user` (`username`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jobs`
--

LOCK TABLES `jobs` WRITE;
/*!40000 ALTER TABLE `jobs` DISABLE KEYS */;
/*!40000 ALTER TABLE `jobs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product`
--

DROP TABLE IF EXISTS `product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product` (
  `productname` varchar(200) NOT NULL,
  `strategy` varchar(10) DEFAULT NULL,
  `max_days` int(11) DEFAULT NULL,
  `max_days_month` int(11) DEFAULT NULL,
  `case_regex` varchar(200) DEFAULT NULL,
  `quota_over_days` int(11) DEFAULT NULL,
  `sf_api` varchar(2000) DEFAULT NULL,
  `sf_job_cron` varchar(200) DEFAULT NULL,
  `sf_job_timezone` varchar(200) DEFAULT NULL,
  `sf_job_query_interval` int(11) DEFAULT NULL,
  PRIMARY KEY (`productname`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product`
--

LOCK TABLES `product` WRITE;
/*!40000 ALTER TABLE `product` DISABLE KEYS */;
/*!40000 ALTER TABLE `product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `salesforce_cases`
--

DROP TABLE IF EXISTS `salesforce_cases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `salesforce_cases` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `case_id` varchar(50) DEFAULT NULL,
  `product` varchar(200) NOT NULL,
  `priority` varchar(10) DEFAULT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `case_id` (`case_id`),
  KEY `product` (`product`),
  CONSTRAINT `salesforce_cases_ibfk_1` FOREIGN KEY (`product`) REFERENCES `product` (`productname`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `salesforce_cases`
--

LOCK TABLES `salesforce_cases` WRITE;
/*!40000 ALTER TABLE `salesforce_cases` DISABLE KEYS */;
/*!40000 ALTER TABLE `salesforce_cases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `salesforce_emails`
--

DROP TABLE IF EXISTS `salesforce_emails`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `salesforce_emails` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user` varchar(50) DEFAULT NULL,
  `email_name` varchar(200) NOT NULL,
  `email_body` varchar(5000) DEFAULT NULL,
  `email_subject` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_name` (`email_name`),
  KEY `user` (`user`),
  CONSTRAINT `salesforce_emails_ibfk_1` FOREIGN KEY (`user`) REFERENCES `user` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `salesforce_emails`
--

LOCK TABLES `salesforce_emails` WRITE;
/*!40000 ALTER TABLE `salesforce_emails` DISABLE KEYS */;
/*!40000 ALTER TABLE `salesforce_emails` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `team`
--

DROP TABLE IF EXISTS `team`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `team` (
  `teamname` varchar(200) NOT NULL,
  `email` varchar(200) DEFAULT NULL,
  `mswebhook` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`teamname`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `team`
--

LOCK TABLES `team` WRITE;
/*!40000 ALTER TABLE `team` DISABLE KEYS */;
/*!40000 ALTER TABLE `team` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `password` varchar(200) NOT NULL,
  `user_since` datetime NOT NULL,
  `teamname` varchar(200) NOT NULL,
  `active` tinyint(1) DEFAULT NULL,
  `shift_start` varchar(100) NOT NULL,
  `shift_end` varchar(100) NOT NULL,
  `timezone` varchar(200) NOT NULL,
  `last_login` datetime NOT NULL,
  `admin` tinyint(1) DEFAULT NULL,
  `first_name` varchar(50) DEFAULT NULL,
  `last_name` varchar(50) DEFAULT NULL,
  `team_email_notifications` tinyint(1) DEFAULT NULL,
  `monitor_case_updates` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `teamname` (`teamname`),
  CONSTRAINT `user_ibfk_1` FOREIGN KEY (`teamname`) REFERENCES `team` (`teamname`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_product`
--

DROP TABLE IF EXISTS `user_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_product` (
  `user_name` varchar(50) NOT NULL,
  `product_name` varchar(200) NOT NULL,
  `active` tinyint(1) DEFAULT NULL,
  `quota` int(11) DEFAULT NULL,
  PRIMARY KEY (`user_name`,`product_name`),
  KEY `product_name` (`product_name`),
  CONSTRAINT `user_product_ibfk_1` FOREIGN KEY (`user_name`) REFERENCES `user` (`username`),
  CONSTRAINT `user_product_ibfk_2` FOREIGN KEY (`product_name`) REFERENCES `product` (`productname`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_product`
--

LOCK TABLES `user_product` WRITE;
/*!40000 ALTER TABLE `user_product` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_product` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-12-30 17:36:46
