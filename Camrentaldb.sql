/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.7.2-MariaDB, for Win64 (AMD64)
--
-- Host: 192.168.1.131    Database: camera_store
-- ------------------------------------------------------
-- Server version	11.8.5-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `category_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `image_url` text DEFAULT NULL,
  PRIMARY KEY (`category_id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES
(1,'DSLR Camera','Digital SLR cameras','https://cdn.mos.cms.futurecdn.net/uwHcpwnff6LW6AdGCnd9K9.jpg'),
(2,'Action Camera','Action cameras for outdoor use','https://lnwgadget.com/wp-content/uploads/2025/01/2f3e608557f64b064bf68c07c1a234c8@origin-1024x1024.jpg'),
(3,'Lens','Camera lenses','https://fotofile.co.th/wp-content/uploads/2025/11/Canon-RF45mm-f1.2-STM-Lens-3.jpg'),
(4,'Accessories','Tripods, bags and more','https://s.alicdn.com/@sc04/kf/H0cd19aa8d08a437bb05145529fb837a2j.jpg_300x300.jpg'),
(5,'Drone','โดรนถ่ายภาพมุมสูง','https://cdn.thewirecutter.com/wp-content/media/2023/11/dronesforphotovideo-2048px-DSC4837-3x2-1.jpg?auto=webp&quality=75&crop=3:2&width=1024'),
(6,'Lighting','ไฟสตูดิโอและไฟต่อเนื่อง','https://www.prophotostudio.net/wp-content/uploads/2023/09/Neewer-LED.webp'),
(7,'Audio','ไมโครโฟนและเครื่องบันทึกเสียง','https://www.shutterstock.com/image-photo/audio-sound-mixer-buttons-sliders-260nw-2283393445.jpg');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `deposit_transactions`
--

DROP TABLE IF EXISTS `deposit_transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `deposit_transactions` (
  `transaction_id` int(11) NOT NULL AUTO_INCREMENT,
  `rental_id` int(11) NOT NULL,
  `transaction_type` enum('receive','refund','confiscate','penalty') NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `note` text DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`transaction_id`),
  KEY `fk_dt_user` (`created_by`),
  KEY `idx_dt_rental_id` (`rental_id`),
  KEY `idx_dt_type` (`transaction_type`),
  KEY `idx_dt_created_at` (`created_at`),
  CONSTRAINT `fk_dt_rental` FOREIGN KEY (`rental_id`) REFERENCES `rentals` (`rental_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_dt_user` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `deposit_transactions`
--

LOCK TABLES `deposit_transactions` WRITE;
/*!40000 ALTER TABLE `deposit_transactions` DISABLE KEYS */;
INSERT INTO `deposit_transactions` VALUES
(1,1,'receive',5000.00,'Deposit received at queue creation',10,'2026-03-25 17:08:03'),
(2,1,'penalty',500.00,'Penalty settled at return',10,'2026-03-25 17:10:03'),
(3,2,'receive',4000.00,'Deposit received at queue creation',10,'2026-03-25 17:17:40'),
(4,2,'refund',3500.00,'Refund after return (penalty 500.0)',9,'2026-03-25 17:20:03');
/*!40000 ALTER TABLE `deposit_transactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `equipment_images`
--

DROP TABLE IF EXISTS `equipment_images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `equipment_images` (
  `image_id` int(11) NOT NULL AUTO_INCREMENT,
  `equipment_id` int(11) NOT NULL,
  `image_url` text NOT NULL,
  `is_primary` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`image_id`),
  KEY `equipment_id` (`equipment_id`),
  CONSTRAINT `equipment_images_ibfk_1` FOREIGN KEY (`equipment_id`) REFERENCES `equipments` (`equipment_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `equipment_images`
--

LOCK TABLES `equipment_images` WRITE;
/*!40000 ALTER TABLE `equipment_images` DISABLE KEYS */;
INSERT INTO `equipment_images` VALUES
(1,1,'https://d28clw9klscyzj.cloudfront.net/legacy/assets/2017-02-14/files/eos-800d_1495-8.jpg',1),
(2,1,'https://assets.prophotos.ru/data/articles/0001/9367/142032/original.jpg',0),
(3,2,'https://www.ambmag.com.au/wp-content/uploads/2024/05/GoProHero7-1.jpg',1),
(4,3,'https://inwfile.com/s-o/2ly9zl.jpg',1),
(5,4,'https://inwfile.com/s-fv/81selo.jpg',1),
(6,5,'https://www.bigcamera.co.th/media/catalog/product/cache/6cfb1b58b487867e47102a5ca923201b/s/o/sony-fe-24-70mm-f2-8-gm-ii-4_3.png',1),
(7,6,'https://www.djibangkok.com/wp-content/uploads/2022/05/DJI-Mini3-pro-with-dji-rc.jpg',1),
(8,7,'https://www.ec-mall.com/media/catalog/product/cache/9e060b1b3b357cb140b27d2b51b02644/3/4/3425e8f6cef7e891ebb34815558833d5c3fcbcf333c6b69448146f20df9e124b.jpeg',1),
(9,8,'https://www.digital2home.com/wp-content/uploads/2021/04/rode-wireless-go-2-1-5.jpg',1),
(10,9,'https://magento1.bigcamera.co.th/media/wysiwyg/gopro/gopro-hero-11-black/gopro-hero-11-black_2.jpg',1),
(11,1002,'https://f.ptcdn.info/928/010/000/1381757024-a7r351zpsc-o.jpg',1),
(35,1001,'https://images.unsplash.com/photo-1502920917128-1aa500764cbd?auto=format&fit=crop&w=1000&q=80',1),
(36,1001,'https://images.unsplash.com/photo-1516724562728-afc824a36e84?auto=format&fit=crop&w=1000&q=80',0),
(37,1001,'https://images.unsplash.com/photo-1512790182412-b19e6d62bc39?auto=format&fit=crop&w=1000&q=80',0),
(42,10,'https://www.best2home.com/BackOffice/pages/product/images/15058152141-%20canon18-55mm%20is%20stm.jpg',1),
(43,10,'https://www.best2home.com/BackOffice/pages/product/images/15058153905%20-%20canon18-55mm%20is%20stm.jpg',0);
/*!40000 ALTER TABLE `equipment_images` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `equipments`
--

DROP TABLE IF EXISTS `equipments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `equipments` (
  `equipment_id` int(11) NOT NULL AUTO_INCREMENT,
  `category_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `brand` varchar(100) DEFAULT NULL,
  `serial_number` varchar(100) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `daily_rate` decimal(10,2) NOT NULL,
  `deposit_rate` decimal(10,2) NOT NULL,
  `status` enum('available','rented','maintenance') DEFAULT 'available',
  PRIMARY KEY (`equipment_id`),
  UNIQUE KEY `serial_number` (`serial_number`),
  KEY `category_id` (`category_id`),
  CONSTRAINT `equipments_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1004 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `equipments`
--

LOCK TABLES `equipments` WRITE;
/*!40000 ALTER TABLE `equipments` DISABLE KEYS */;
INSERT INTO `equipments` VALUES
(1,1,'Canon EOS 800D','Canon','SN-CN800D-001','กล้อง DSLR ใช้งานง่าย เหมาะสำหรับผู้เริ่มต้นไปจนถึงระดับกลาง',500.00,3000.00,'available'),
(2,2,'GoPro Hero 7 Black','GoPro','SN-GP07B-001','กล้อง Action Cam ถ่ายวิดีโอ 4K กันน้ำลึก 10 เมตร (ระวังสระน้ำเกลือให้ดี!)',300.00,2000.00,'available'),
(3,3,'Canon EF 50mm f/1.8 STM','Canon','SN-CN50F18-001','เลนส์ฟิกซ์ยอดฮิต ถ่ายคนสวย หลังละลาย',200.00,1000.00,'available'),
(4,1,'Sony A7 III','Sony','SN-SNA73-001','กล้อง Mirrorless Full Frame ยอดนิยมสำหรับสายวิดีโอและภาพนิ่ง',800.00,5000.00,'available'),
(5,3,'Sony FE 24-70mm f/2.8 GM','Sony','SN-SN2470-001','เลนส์ซูมเกรดโปร คมกริบทุกระยะ',600.00,4000.00,'available'),
(6,5,'DJI Mini 3 Pro','DJI','SN-DJIM3P-001','โดรนน้ำหนักเบา ไม่ต้องขอใบอนุญาต บินง่าย',700.00,3000.00,'available'),
(7,6,'Godox SL60W','Godox','SN-GD60W-001','ไฟต่อเนื่องสำหรับจัดสตูดิโอถ่ายวิดีโอ',200.00,1000.00,'available'),
(8,7,'Rode Wireless GO II','Rode','SN-RDWG2-001','ไมค์ไวร์เลสคู่ ใช้งานง่าย เสียงชัดเจน',300.00,1500.00,'available'),
(9,2,'GoPro Hero 11 Black','GoPro','SN-GP11B-001','Action Cam รุ่นใหม่ล่าสุด (คำเตือน: ห้ามนำลงสระน้ำเกลือเด็ดขาด ป้องกันเครื่องเสียหาย)',400.00,2500.00,'available'),
(10,3,'EFs 18-55','Canon','sfsdd18-55df','เลนส์ระยะ 18-55 มม',1500.00,100.00,'available'),
(1001,1,'Canon EOS R5','Canon','CN-R5-001','Full-frame mirrorless camera',1500.00,5000.00,'available'),
(1002,1,'Sony A7 IV','Sony','SY-A7IV-001','Hybrid full-frame camera',1200.00,4000.00,'available');
/*!40000 ALTER TABLE `equipments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rental_condition_images`
--

DROP TABLE IF EXISTS `rental_condition_images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `rental_condition_images` (
  `image_id` int(11) NOT NULL AUTO_INCREMENT,
  `rental_id` int(11) NOT NULL,
  `phase` enum('before','after') NOT NULL,
  `image_url` text NOT NULL,
  `note` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`image_id`),
  KEY `idx_rci_rental_id` (`rental_id`),
  KEY `idx_rci_phase` (`phase`),
  CONSTRAINT `fk_rci_rental` FOREIGN KEY (`rental_id`) REFERENCES `rentals` (`rental_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rental_condition_images`
--

LOCK TABLES `rental_condition_images` WRITE;
/*!40000 ALTER TABLE `rental_condition_images` DISABLE KEYS */;
/*!40000 ALTER TABLE `rental_condition_images` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rental_form_details`
--

DROP TABLE IF EXISTS `rental_form_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `rental_form_details` (
  `rental_id` int(11) NOT NULL,
  `contact_phone` varchar(20) NOT NULL,
  `pickup_location` varchar(255) NOT NULL,
  `purpose` varchar(255) DEFAULT NULL,
  `note` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`rental_id`),
  CONSTRAINT `fk_rfd_rental` FOREIGN KEY (`rental_id`) REFERENCES `rentals` (`rental_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rental_form_details`
--

LOCK TABLES `rental_form_details` WRITE;
/*!40000 ALTER TABLE `rental_form_details` DISABLE KEYS */;
INSERT INTO `rental_form_details` VALUES
(1,'0886494155','สยาม','งานแต่ง','เเ','2026-03-25 17:08:03'),
(2,'0886494155','บ้าน','ถ่ายสตูดิโอ','','2026-03-25 17:17:40');
/*!40000 ALTER TABLE `rental_form_details` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rental_status_logs`
--

DROP TABLE IF EXISTS `rental_status_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `rental_status_logs` (
  `log_id` int(11) NOT NULL AUTO_INCREMENT,
  `rental_id` int(11) NOT NULL,
  `from_status` enum('pending','active','completed','cancelled') DEFAULT NULL,
  `to_status` enum('pending','active','completed','cancelled') NOT NULL,
  `remark` text DEFAULT NULL,
  `changed_by` int(11) DEFAULT NULL,
  `changed_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`log_id`),
  KEY `fk_rsl_user` (`changed_by`),
  KEY `idx_rsl_rental_id` (`rental_id`),
  KEY `idx_rsl_changed_at` (`changed_at`),
  CONSTRAINT `fk_rsl_rental` FOREIGN KEY (`rental_id`) REFERENCES `rentals` (`rental_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_rsl_user` FOREIGN KEY (`changed_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rental_status_logs`
--

LOCK TABLES `rental_status_logs` WRITE;
/*!40000 ALTER TABLE `rental_status_logs` DISABLE KEYS */;
INSERT INTO `rental_status_logs` VALUES
(1,1,NULL,'pending','Created from rental request',10,'2026-03-25 17:08:03'),
(2,1,'pending','pending','ต้องตรวจสอบแล้วตรงสภาพจริง',9,'2026-03-25 17:09:09'),
(3,1,'pending','active','Updated by sun',9,'2026-03-25 17:09:16'),
(4,1,'active','completed','Returned by renter',10,'2026-03-25 17:10:03'),
(5,2,NULL,'pending','Created from rental request',10,'2026-03-25 17:17:40'),
(6,2,'pending','active','Updated by sun',9,'2026-03-25 17:19:18'),
(7,2,'active','active','Customer submitted return request; waiting admin inspection',10,'2026-03-25 17:19:42'),
(8,2,'active','completed','Admin inspected return and closed rental (penalty: 500.00)',9,'2026-03-25 17:20:03');
/*!40000 ALTER TABLE `rental_status_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rentals`
--

DROP TABLE IF EXISTS `rentals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `rentals` (
  `rental_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `equipment_id` int(11) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `actual_return_date` date DEFAULT NULL,
  `total_rent_price` decimal(10,2) DEFAULT NULL,
  `penalty_fee` decimal(10,2) DEFAULT 0.00,
  `deposit_status` enum('pending','paid','refunded','confiscated') DEFAULT 'pending',
  `rental_status` enum('pending','active','completed','cancelled') DEFAULT 'pending',
  `condition_before` text DEFAULT NULL,
  `condition_after` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`rental_id`),
  KEY `user_id` (`user_id`),
  KEY `equipment_id` (`equipment_id`),
  CONSTRAINT `rentals_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `rentals_ibfk_2` FOREIGN KEY (`equipment_id`) REFERENCES `equipments` (`equipment_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rentals`
--

LOCK TABLES `rentals` WRITE;
/*!40000 ALTER TABLE `rentals` DISABLE KEYS */;
INSERT INTO `rentals` VALUES
(1,10,1001,'2026-03-26','2026-03-27','2026-03-25',3000.00,500.00,'paid','completed','สภาพปกติไม่มีรอยขีดข่วน','มีรอยขีดข่วนเล็กน้อย','2026-03-25 17:08:03'),
(2,10,1002,'2026-03-26','2026-03-27','2026-03-25',2400.00,500.00,'refunded','completed',NULL,'มีรอยขีดข่วนเล็กน้อย','2026-03-25 17:17:40');
/*!40000 ALTER TABLE `rentals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `phone` varchar(20) NOT NULL,
  `id_card_number` varchar(13) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `role` varchar(20) DEFAULT 'customer',
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES
(1,'admin_sun','ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f','admin@camerarental.com','0801112222','1100000000000','ร้านเช่ากล้อง ใกล้มหาวิทยาลัย','admin','2026-03-24 19:40:14'),
(2,'customer_01','ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f','customer@gmail.com','0903334444','1100000000001','ต.สามพระยา จ.เพชรบุรี','customer','2026-03-24 19:40:14'),
(3,'admin_patchasara','ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f','patchasara@camerarental.com','0809998888','1100000000002','คณะ ICT มหาวิทยาลัยศิลปากร','admin','2026-03-24 19:46:54'),
(4,'customer_02','ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f','cust02@gmail.com','0812223333','1100000000003','หอพักแถวพระราม 9','customer','2026-03-24 19:46:54'),
(5,'customer_03','ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f','cust03@gmail.com','0823334444','1100000000004','กรุงเทพมหานคร','customer','2026-03-24 19:46:54'),
(9,'sun','e82081c360d3babce8aa4ebffe6e519facbd4ee116c43157e809c7cfb68ecc0e','pongsakorn.sun11548@gmail.com','0821911199','1101501275973','1325/47','admin','2026-03-24 21:57:56'),
(10,'sun1','e82081c360d3babce8aa4ebffe6e519facbd4ee116c43157e809c7cfb68ecc0e','pongsakorn.sun115481@gmail.com','0886494155','1101501275973','fgdd','customer','2026-03-24 22:33:00'),
(11,'admin_demo','8d969eef6ecad3c29a3a629280e686cff8fabdc2da7f697f21a11f8b7f7f3fcb','admin@example.com','0811111111','1234567890123','Bangkok','admin','2026-03-24 22:38:57'),
(12,'user_demo','8d969eef6ecad3c29a3a629280e686cff8fabdc2da7f697f21a11f8b7f7f3fcb','user@example.com','0822222222','2234567890123','Chiang Mai','customer','2026-03-24 22:38:57');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'camera_store'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-03-26  1:03:19
