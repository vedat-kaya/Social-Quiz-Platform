-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Anamakine: 127.0.0.1
-- Üretim Zamanı: 25 Ara 2025, 18:47:33
-- Sunucu sürümü: 10.4.32-MariaDB
-- PHP Sürümü: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Veritabanı: `quizes`
--

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `questions`
--

CREATE TABLE `questions` (
  `question_id` int(11) NOT NULL,
  `quiz_id` int(11) NOT NULL,
  `question_text` text NOT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `option_a` varchar(255) NOT NULL,
  `option_b` varchar(255) NOT NULL,
  `option_c` varchar(255) NOT NULL,
  `option_d` varchar(255) NOT NULL,
  `correct_answer` varchar(10) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Tablo döküm verisi `questions`
--

INSERT INTO `questions` (`question_id`, `quiz_id`, `question_text`, `image_url`, `option_a`, `option_b`, `option_c`, `option_d`, `correct_answer`) VALUES
(1, 2, 'Cevap a dır', NULL, 'a', 'b', 'c', 'd', 'a'),
(2, 2, 'ugauaiu', NULL, 'ugau', 'aui', 'agu', 'aiu', 'a'),
(3, 2, 'gauuia', NULL, 'aiuaiu', 'aiuuiaui', 'aauiuiaui', 'auiuiaiu', 'a'),
(4, 2, 'ugauaug', NULL, 'aguau', 'aguauagu', 'iauauaiu', 'auiuiaiua', 'a'),
(5, 6, '', 'popi.jpg', '', '', '', '', ''),
(6, 6, '', 'popi.jpg', '', '', '', '', ''),
(7, 7, '', 'witcher.jpg', '', '', '', '', ''),
(8, 7, '', 'witcher.png', '', '', '', '', ''),
(9, 8, '', '1282154.jpg', '', '', '', '', ''),
(10, 9, '', 'witcher.jpg', '', '', '', '', ''),
(11, 9, '', 'witcher.jpg', '', '', '', '', ''),
(12, 10, '', '20250627_104936.jpg', '', '', '', '', ''),
(13, 10, '', 'popi.jpg', '', '', '', '', ''),
(14, 10, '', 'default_avatar.png', '', '', '', '', ''),
(15, 10, '', 'default_quiz_cover.png', '', '', '', '', ''),
(16, 10, '', 'arkaplan.jpg', '', '', '', '', ''),
(17, 11, '', 'foto1.jpg', '', '', '', '', ''),
(18, 11, '', 'foto2.jpg', '', '', '', '', ''),
(19, 11, '', 'foto3.jpg', '', '', '', '', ''),
(20, 11, '', 'foto4.jpg', '', '', '', '', ''),
(21, 11, '', 'foto5.jpg', '', '', '', '', ''),
(22, 11, '', 'foto6.jpg', '', '', '', '', ''),
(23, 11, '', 'foto7.jpg', '', '', '', '', ''),
(24, 11, '', 'foto8.jpg', '', '', '', '', ''),
(25, 11, '', 'foto9.jpg', '', '', '', '', ''),
(26, 11, '', 'foto10.jpg', '', '', '', '', ''),
(27, 12, 'Naber ya kıskanç mısın', NULL, 'Evet', 'Hayır', 'Biraz', 'Belki', 'a'),
(28, 17, 'Sevgilinden izinsiz bi yere gidebilir misin?', NULL, 'Tabiki  ben erkeğim ', 'İzin almasamda haber veririm', 'Evet izin almam gerekiyor', 'Konum atıyorum(İBNEYİM)', 'd'),
(29, 17, 'Sigara kullanıyor musun', NULL, 'Evet', 'Hayır', 'Arada kullanırım', 'Kullanıyorum hem de ince(slim)', 'd'),
(30, 17, 'Sevgiliniz sizden bişeyler yasaklar mı?', NULL, 'Hayır kimse benden bişey yasaklıyamaz', 'Evet ama bende ondan yasaklarım', 'Evet hatta bi keresinde bi sokağı bile yasakladı ', 'Yasaklamamıza gerek kalmaz genelde', 'c'),
(31, 17, 'Babet çorap hakkındakı fikirleriniz nelerdir ?', NULL, 'Evet bazen giyilebilir', 'Başka çorap giyemiyorum rahatsız ediyor', 'Giymem ama başkaları giyebilir', 'Asla ', 'b'),
(32, 24, '', 'winston-slim-blue-delik-sigara-1.jpg', '', '', '', '', ''),
(33, 24, '', 'winston-slim-blue-delik-sigara-1.jpg', '', '', '', '', ''),
(34, 25, 'batman', 'winston-slim-blue-delik-sigara-1.jpg', '', '', '', '', ''),
(35, 25, 'spiderman', 'winston-slim-blue-delik-sigara-1.jpg', '', '', '', '', ''),
(36, 28, 'uiauaguauiu', NULL, 'gauiauiaua', 'uiauiaiuaiu', 'iuauagiaugauia', 'ugauiaugaugau', 'a'),
(37, 29, '', 'foto1.jpg', '', '', '', '', ''),
(38, 29, '', 'foto2.jpg', '', '', '', '', ''),
(39, 29, '', 'foto3.jpg', '', '', '', '', ''),
(40, 29, '', 'foto4.jpg', '', '', '', '', ''),
(41, 29, '', 'foto5.jpg', '', '', '', '', ''),
(42, 29, '', 'foto6.jpg', '', '', '', '', ''),
(43, 29, '', 'foto7.jpg', '', '', '', '', ''),
(44, 29, '', 'foto8.jpg', '', '', '', '', ''),
(45, 29, '', 'foto9.jpg', '', '', '', '', ''),
(46, 29, '', 'foto10.jpg', '', '', '', '', ''),
(47, 30, '', 'indir_2.jpg', '', '', '', '', ''),
(48, 30, '', 'The_Witcher_3_Wallpaper.jpg', '', '', '', '', ''),
(49, 30, '', 'indir.jpg', '', '', '', '', ''),
(50, 30, '', 'MR_OLLS_MR_OLLS_on_X.jpg', '', '', '', '', ''),
(51, 31, 'Sevgilinden izinsiz bi yere gidebilir misin?', NULL, 'Tabiki ben erkeğim', 'İzin almasamda haber veririm', 'Evet izin almam gerekiyor', 'CANLI KONUM ATIYORUM.', 'd'),
(52, 31, 'Sigara kullanıyor musun ', NULL, 'Evet', 'Hayır', 'Ara Sıra', 'Kullanıyorum hem de SLİM', 'd'),
(53, 31, 'Sevgilinizle birbirinizin alanlarına saygı duyar mısınız?', NULL, 'Elbette birbirimizin alanlarına saygı duyarız.', 'Çoğunlukla sorun yaşamamak için birbirimize karışmayız.', 'Hayır genelde birbirimize karışırız.', '7. Caddeye gitmediğim sürece sorunumuz olmaz.', 'd'),
(54, 31, 'Babet çorap giyer misiniz', NULL, 'Evet', 'Hayır', 'Zorundaysam eğer giyerim', 'Başka çorap giyemiyorum rahatsız ediyor', 'd'),
(55, 33, '', '3c493bfb-ce15-4193-b3f2-3251d5e9b000_Game_of_thrones.jpg', '', '', '', '', ''),
(56, 33, '', '05feb77c-8ece-404e-b643-4b7bc94769cf_profile_image.jpg', '', '', '', '', ''),
(57, 33, '', '6400ff0b-b7c3-47e8-a6ed-196b229d2076_indir_1.jpg', '', '', '', '', ''),
(58, 34, 'uatutautaeutuae', NULL, 'uatututu', 'utautuet', 'uaetuteut', 'uatutu', 'a'),
(59, 35, 'UİEAÜÜUEİÜİUÜEİE', NULL, 'UİEÜUİEÜİUİ', 'ÜEİUÜUİÜU', 'ÜUEİUÜUÜ', 'İUEÜİUÜUİÜİU', 'a'),
(60, 37, '', 'bcd8a417-3f05-49c8-9830-cd51192418f1_Game_of_thrones.jpg', '', '', '', '', ''),
(61, 37, '', 'c2fbc4d1-acc3-4192-a5c1-e03bb2b485df_indir_1.jpg', '', '', '', '', ''),
(62, 37, '', 'f2df1f71-8fdf-47e4-8fe9-bba3ec3030b1_the_witcher_.jpg', '', '', '', '', ''),
(63, 38, '', 'b95c9376-d74e-4a6b-b583-330a1973e61b_Game_of_thrones.jpg', '', '', '', '', ''),
(64, 38, '', 'd6b5c997-82dd-4189-896d-12197bd6ae24_the_witcher_.jpg', '', '', '', '', ''),
(65, 38, '', '34fd36f1-a7a6-47bd-a361-ff1a9973f11b_indir.jpg', '', '', '', '', ''),
(66, 38, '', '09ca063c-dbdc-4a73-b746-40b0324ee319_MR_OLLS_MR_OLLS_on_X.jpg', '', '', '', '', ''),
(67, 39, '', '5d6e7a63-14fc-46d4-875e-95ac77e49852_Game_of_thrones.jpg', '', '', '', '', ''),
(68, 39, '', '60e76074-2dc5-44c7-9bd1-fd74bf0f0b6f_indir_1.jpg', '', '', '', '', ''),
(69, 39, '', '313e38d6-1973-4ca6-97df-d9fc038ec404_indir.jpg', '', '', '', '', ''),
(70, 39, '', '07118e49-1aa9-4bf1-9873-cd83f4cd9646_MR_OLLS_MR_OLLS_on_X.jpg', '', '', '', '', ''),
(71, 39, '', '1c02c8e8-7066-4820-801e-21ecfa982c1a_indir_3.jpg', '', '', '', '', ''),
(72, 39, '', 'd44c09d9-e5df-4a84-980d-ad762c3e9436_The_witcher_4.jpg', '', '', '', '', ''),
(73, 40, 'üateaüomiümkaeüke', NULL, 'maemaemamke', 'aküüakaekaüt', 'emamüaemaemea', 'maemaemaeamü', 'a'),
(74, 41, '', '08d49106-3600-48de-9deb-216c08617a5e_Game_of_thrones.jpg', '', '', '', '', ''),
(75, 42, 'Brienne of Tarth', 'edf67932-2010-4fd7-8e0a-a9c8d1598831_Brienne_of_Tarth.jpg', '', '', '', '', ''),
(76, 42, 'Arya Stark', '11043c8e-67a3-4ee6-a1c9-4e1b20925fa1_Arya_Stark.jpg', '', '', '', '', ''),
(77, 42, 'Barristan Selmy', '79301656-8d5e-4ec2-bcde-067f0444743a_Barristan_Selmy.jpg', '', '', '', '', ''),
(78, 42, 'Bran Stark', 'fba3c047-8e80-40b2-ab72-d119b7a93253_Bran_Stark.jpg', '', '', '', '', ''),
(79, 42, 'Bronn', 'a48cd8d5-25cf-4c04-a8b5-9a3577fde906_Bronn.jpg', '', '', '', '', ''),
(80, 42, 'Brynden Tully', 'c7530da3-b798-454f-a267-9d7b7a1ca47a_Brynden_Tully.jpg', '', '', '', '', ''),
(81, 42, 'Catelyn Stark', 'abe0d747-dda3-4d4d-bfcb-b1068a8a5da9_Catelyn_Stark.jpg', '', '', '', '', ''),
(82, 42, 'Cersei Lannister', '9dd5cf14-dcd6-4de2-bf83-29567d376499_Cersei_Lannister.jpg', '', '', '', '', ''),
(83, 42, 'Daenerys Targaryen', 'a2611ae8-b36b-46b8-805e-ac8dae8efc91_Daenerys_Targaryen.jpg', '', '', '', '', ''),
(84, 42, 'Davos Seaworth', '52b360e2-ebbd-4f14-a46e-30cdc5346572_Davos_Seaworth.jpg', '', '', '', '', ''),
(85, 42, 'Eddard Stark', '1a0b43c9-bbb0-492b-98cc-6fe215e2ae6f_Eddard_Stark.jpg', '', '', '', '', ''),
(86, 42, 'Euron Greyjoy', '043752e9-a534-4d45-846f-967207a288b8_Euron_Greyjoy.jpg', '', '', '', '', ''),
(87, 42, 'Gendry', '2909e8cf-864e-4416-8611-7735ee5f3441_Gendry.jpg', '', '', '', '', ''),
(88, 42, 'Hodor', 'f5c0a4c2-a9fc-4d49-86be-cb42f412c51a_Hodor.jpg', '', '', '', '', ''),
(89, 42, 'Jaime Lannister', '7c7fbefc-4790-485d-b21c-1facc0cc6be3_Jaime_Lannister.jpg', '', '', '', '', ''),
(90, 42, 'Janos Slynt', '960387ce-1184-4600-b461-7737df691728_Janos_Slynt.jpg', '', '', '', '', ''),
(91, 42, 'Jaqen H\'ghar', '13c1c6ef-d1c9-425e-8bc2-d4b917db427a_Jaqen_Hghar.jpg', '', '', '', '', ''),
(92, 42, 'Jeor Mormont', '6dcf29c6-b4b0-4096-873e-58a806290dcd_Jeor_Mormont.jpg', '', '', '', '', ''),
(93, 42, 'Joffrey Baratheon', '7400cc22-8ec5-416a-98a6-9ad64dc9804b_Joffrey_Baratheon.jpg', '', '', '', '', ''),
(94, 42, 'Jon Snow', '15006a3b-0460-4fc5-9118-3e3bd0cfc503_Jon_Snow.jpg', '', '', '', '', ''),
(95, 42, 'Khal Drogo', 'd2165afd-c39b-4157-ab9c-2902d4371ca9_Khal_Drogo.jpg', '', '', '', '', ''),
(96, 42, 'Lady Melisandre', '9503f2f3-c530-4fc5-9e5c-d97e10e1b77d_Lady_Melisandre.jpg', '', '', '', '', ''),
(97, 42, 'Lord Petyr Baelish', 'c087048a-2955-4786-944a-273e71eb3850_Lord_Petyr_Baelish.jpg', '', '', '', '', ''),
(98, 42, 'Mance Rayder', '84dd9077-80ff-497d-87cb-b369accf970e_Mance_Rayder.jpg', '', '', '', '', ''),
(99, 42, 'Margaery Tyrell', '130aa6b0-3581-4e81-8600-685005f16795_Margaery_Tyrell.jpg', '', '', '', '', ''),
(100, 42, 'Missandei', '152a74a9-ed17-4460-9bac-507a910db11d_Missandei.jpg', '', '', '', '', ''),
(101, 42, 'Oberyn Martell', '0968e051-a012-40f7-b53a-21f30347ea68_Oberyn_Martell.jpg', '', '', '', '', ''),
(102, 42, 'Ramsay Bolton', '70a3328d-14b8-438a-af24-9f3fe4842b2c_Ramsay_Bolton.jpg', '', '', '', '', ''),
(103, 42, 'Renly Baratheon', 'ea737a7e-6151-426c-a704-584422e59977_Renly_Baratheon.jpg', '', '', '', '', ''),
(104, 42, 'Robb Stark', 'eb7e856f-8c92-4680-afbc-031584b0e3dc_Robb_Stark.jpg', '', '', '', '', ''),
(105, 42, 'Robert Baratheon', '4e23a66f-2b93-4105-bd52-4343f935206f_Robert_Baratheon.jpg', '', '', '', '', ''),
(106, 42, 'Samwell Tarly', '57237aea-7f51-4d98-8c88-a1e62abf8194_Samwell_Tarly.jpg', '', '', '', '', ''),
(107, 42, 'Sandor “The Hound” Clegane', 'd10d272d-0449-4e4c-bd86-5056c3e9f53d_Sandor_The_Hound_Clegane.jpg', '', '', '', '', ''),
(108, 42, 'Sansa Stark', 'ef5e4a79-41c7-40b9-87dc-68ca0b6af256_Sansa_Stark.jpg', '', '', '', '', ''),
(109, 42, 'Ser Jorah Mormont', '65967727-bd0a-4f29-ac67-09ef60c4a237_Ser_Jorah_Mormont.jpg', '', '', '', '', ''),
(110, 42, 'Sor Alliser Thorne', 'a7a1512f-dc27-41d8-820c-97c35c53d176_Sor_Alliser_Thorne.jpg', '', '', '', '', ''),
(111, 42, 'Stannis Baratheon', '1763be5a-b98e-4132-93e8-eabc1f16ddea_Stannis_Baratheon.jpg', '', '', '', '', ''),
(112, 42, 'Theon Greyjoy', 'a5faae91-f1fd-497c-835e-f1b401efa559_Theon_Greyjoy.jpg', '', '', '', '', ''),
(113, 42, 'Tommen Baratheon', '045c3ff9-cf11-4238-9c85-355204f85ea9_Tommen_Baratheon.jpg', '', '', '', '', ''),
(114, 42, 'Tormund Giantsbane', '714983c9-a6ae-41e1-bdc7-2fbfcadb0929_Tormund_Giantsbane.jpg', '', '', '', '', ''),
(115, 42, 'Tyrion Lannister ', '032d755c-97e4-4e0b-b426-dbec56e32ba9_Tyrion_Lannister_.jpg', '', '', '', '', ''),
(116, 42, 'Tywin Lannister', '515dc258-5f96-43e4-aa01-d326d7913147_Tywin_Lannister.jpg', '', '', '', '', ''),
(117, 42, 'Varys', '6900f4aa-dad6-4e2e-8027-44193ea93010_Varys.jpg', '', '', '', '', ''),
(118, 42, 'Ygritte', '8441fab5-35ea-4187-ad4b-0106ccce1744_Ygritte.jpg', '', '', '', '', ''),
(119, 42, 'Olenna Tyrell', '5d750233-e97b-4da6-8c0c-9a4a34ef7c4b_indir_15.jpg', '', '', '', '', '');

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `quizzes`
--

CREATE TABLE `quizzes` (
  `quiz_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `quiz_type` varchar(50) NOT NULL DEFAULT 'bilgi_yarismasi',
  `cover_image_url` varchar(255) DEFAULT 'default_quiz_cover.png',
  `views` int(11) NOT NULL DEFAULT 0,
  `likes` int(11) NOT NULL DEFAULT 0,
  `cover_image` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `category` varchar(50) NOT NULL DEFAULT 'Genel'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Tablo döküm verisi `quizzes`
--

INSERT INTO `quizzes` (`quiz_id`, `user_id`, `title`, `description`, `quiz_type`, `cover_image_url`, `views`, `likes`, `cover_image`, `created_at`, `category`) VALUES
(42, 1, 'Hangi Game of Thrones karakterini daha çok seviyorsun?', 'İster turnuva ister kör sıralama yap eğer diziyi seviyorsan hadi çöz.', 'turnuva', 'd8c7e26c-77d9-4c10-bd58-cb051c0e0aa6_Wolf.jpg', 2, 1, '', '2025-12-23 16:49:27', 'Film');

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `quiz_likes`
--

CREATE TABLE `quiz_likes` (
  `like_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `quiz_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Tablo döküm verisi `quiz_likes`
--

INSERT INTO `quiz_likes` (`like_id`, `user_id`, `quiz_id`) VALUES
(11, 1, 42);

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `quiz_results`
--

CREATE TABLE `quiz_results` (
  `id` int(11) NOT NULL,
  `quiz_id` int(11) NOT NULL,
  `result_key` varchar(5) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `quiz_saves`
--

CREATE TABLE `quiz_saves` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `quiz_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Tablo döküm verisi `quiz_saves`
--

INSERT INTO `quiz_saves` (`id`, `user_id`, `quiz_id`, `created_at`) VALUES
(1, 1, 40, '2025-12-23 15:24:35'),
(2, 1, 42, '2025-12-23 17:01:55');

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `saved_quizzes`
--

CREATE TABLE `saved_quizzes` (
  `save_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `quiz_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `profile_pic_url` varchar(255) DEFAULT 'default_avatar.png',
  `register_date` timestamp NOT NULL DEFAULT current_timestamp(),
  `is_admin` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Tablo döküm verisi `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `username`, `password`, `profile_pic_url`, `register_date`, `is_admin`, `created_at`) VALUES
(1, 'Vedat', 'vedatline@gmail.com', 'vedatkaya', '$5$rounds=535000$Xi0.hGn9lDM/P27B$f7zqrkjBwxajMRYU8zLi.zeSG4RbGHsZfu8xjvjuza2', 'f40eb65e-291d-4aff-8d64-2c521e2f9898_Ciri.jpg', '2025-11-07 17:55:56', 1, '2025-12-23 10:16:10'),
(2, 'Deneme2', 'deneme@gmail.com', 'deneme2', '$5$rounds=535000$7RWli3D5eQyaxpk7$WxxSFA6XhErcrX4Pg973UQo1kE0UpnvIiwMfcn2nn22', 'default.png', '2025-11-12 00:49:19', 0, '2025-12-23 10:16:10'),
(3, 'gaguguau', 'vedoo@gmail.com', 'vedoo', '$5$rounds=535000$0gvQBqadguL/ZEaG$izUBv.0choMzUj08uB2dJ.E93vhN9kTjH7G2i3bN20B', 'default.png', '2025-12-23 11:16:23', 0, '2025-12-23 11:16:23');

--
-- Dökümü yapılmış tablolar için indeksler
--

--
-- Tablo için indeksler `questions`
--
ALTER TABLE `questions`
  ADD PRIMARY KEY (`question_id`);

--
-- Tablo için indeksler `quizzes`
--
ALTER TABLE `quizzes`
  ADD PRIMARY KEY (`quiz_id`);

--
-- Tablo için indeksler `quiz_likes`
--
ALTER TABLE `quiz_likes`
  ADD PRIMARY KEY (`like_id`),
  ADD UNIQUE KEY `unique_like` (`user_id`,`quiz_id`),
  ADD KEY `quiz_id` (`quiz_id`);

--
-- Tablo için indeksler `quiz_results`
--
ALTER TABLE `quiz_results`
  ADD PRIMARY KEY (`id`);

--
-- Tablo için indeksler `quiz_saves`
--
ALTER TABLE `quiz_saves`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`,`quiz_id`);

--
-- Tablo için indeksler `saved_quizzes`
--
ALTER TABLE `saved_quizzes`
  ADD PRIMARY KEY (`save_id`);

--
-- Tablo için indeksler `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Dökümü yapılmış tablolar için AUTO_INCREMENT değeri
--

--
-- Tablo için AUTO_INCREMENT değeri `questions`
--
ALTER TABLE `questions`
  MODIFY `question_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=120;

--
-- Tablo için AUTO_INCREMENT değeri `quizzes`
--
ALTER TABLE `quizzes`
  MODIFY `quiz_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=43;

--
-- Tablo için AUTO_INCREMENT değeri `quiz_likes`
--
ALTER TABLE `quiz_likes`
  MODIFY `like_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- Tablo için AUTO_INCREMENT değeri `quiz_results`
--
ALTER TABLE `quiz_results`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Tablo için AUTO_INCREMENT değeri `quiz_saves`
--
ALTER TABLE `quiz_saves`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Tablo için AUTO_INCREMENT değeri `saved_quizzes`
--
ALTER TABLE `saved_quizzes`
  MODIFY `save_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Tablo için AUTO_INCREMENT değeri `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Dökümü yapılmış tablolar için kısıtlamalar
--

--
-- Tablo kısıtlamaları `quiz_likes`
--
ALTER TABLE `quiz_likes`
  ADD CONSTRAINT `quiz_likes_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `quiz_likes_ibfk_2` FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`quiz_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
