# ************************************************************
# Sequel Pro SQL dump
# Version 4096
#
# http://www.sequelpro.com/
# http://code.google.com/p/sequel-pro/
#
# Host: 127.0.0.1 (MySQL 5.6.21)
# Database: bc
# Generation Time: 2014-12-17 19:09:50 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table game
# ------------------------------------------------------------

DROP TABLE IF EXISTS `game`;

CREATE TABLE `game` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `source_id` int(11) unsigned NOT NULL,
  `source_ref` varchar(100) NOT NULL DEFAULT '',
  `white_elo` int(11) unsigned DEFAULT NULL,
  `black_elo` int(11) unsigned DEFAULT NULL,
  `ECO` char(8) NOT NULL DEFAULT '',
  `result` tinyint(11) NOT NULL,
  `white_computer` tinyint(11) unsigned NOT NULL,
  `black_computer` tinyint(11) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table move
# ------------------------------------------------------------

DROP TABLE IF EXISTS `move`;

CREATE TABLE `move` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `game_id` int(11) unsigned NOT NULL,
  `scoring_run_id` int(11) unsigned NOT NULL,
  `ply` smallint(11) NOT NULL,
  `equity_loss` int(11) NOT NULL,
  `white_equity` smallint(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `game_id` (`game_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table scoring_run
# ------------------------------------------------------------

DROP TABLE IF EXISTS `scoring_run`;

CREATE TABLE `scoring_run` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `job_ref` varchar(500) NOT NULL DEFAULT '',
  `engine` varchar(255) NOT NULL DEFAULT '',
  `engine_version` varchar(255) NOT NULL DEFAULT '',
  `engine_settings` varchar(20000) NOT NULL DEFAULT '',
  `run_start` datetime NOT NULL,
  `run_end` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table source
# ------------------------------------------------------------

DROP TABLE IF EXISTS `source`;

CREATE TABLE `source` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;




/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
