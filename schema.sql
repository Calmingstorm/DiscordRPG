-- DiscordRPG MariaDB Schema
-- Requires MariaDB 10.6+ or MySQL 8.0+
-- Character set: utf8mb4

CREATE TABLE `adventures` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) DEFAULT NULL,
  `adventure_name` varchar(255) DEFAULT NULL,
  `difficulty` int(11) DEFAULT NULL,
  `started_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `finish_at` timestamp NULL DEFAULT NULL,
  `status` varchar(32) DEFAULT 'active',
  PRIMARY KEY (`id`),
  KEY `idx_adventures_user` (`user_id`,`status`),
  CONSTRAINT `adventures_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=37135 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `alliance` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `icon` varchar(512) DEFAULT NULL,
  `owner` bigint(20) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `owner` (`owner`),
  CONSTRAINT `alliance_ibfk_1` FOREIGN KEY (`owner`) REFERENCES `guild` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `battle_logs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `attacker` bigint(20) DEFAULT NULL,
  `defender` bigint(20) DEFAULT NULL,
  `winner` bigint(20) DEFAULT NULL,
  `battle_type` varchar(64) DEFAULT NULL,
  `damage_dealt` int(11) DEFAULT NULL,
  `damage_taken` int(11) DEFAULT NULL,
  `money_stolen` int(11) DEFAULT NULL,
  `fought_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `defender` (`defender`),
  KEY `idx_battle_logs_users` (`attacker`,`defender`),
  CONSTRAINT `battle_logs_ibfk_1` FOREIGN KEY (`attacker`) REFERENCES `profile` (`user_id`),
  CONSTRAINT `battle_logs_ibfk_2` FOREIGN KEY (`defender`) REFERENCES `profile` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=149 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `children` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `parent1` bigint(20) DEFAULT NULL,
  `parent2` bigint(20) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `age` int(11) DEFAULT 0,
  `gender` varchar(16) DEFAULT NULL,
  `born_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `parent1` (`parent1`),
  KEY `parent2` (`parent2`),
  CONSTRAINT `children_ibfk_1` FOREIGN KEY (`parent1`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `children_ibfk_2` FOREIGN KEY (`parent2`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `cities` (
  `name` varchar(255) NOT NULL,
  `owner` bigint(20) DEFAULT NULL,
  `level` int(11) DEFAULT 1,
  `buildings_thief` int(11) DEFAULT 0,
  `buildings_raid` int(11) DEFAULT 0,
  `buildings_trade` int(11) DEFAULT 0,
  `buildings_adventure` int(11) DEFAULT 0,
  PRIMARY KEY (`name`),
  KEY `owner` (`owner`),
  CONSTRAINT `cities_ibfk_1` FOREIGN KEY (`owner`) REFERENCES `alliance` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `cooldowns` (
  `user_id` bigint(20) NOT NULL,
  `daily` timestamp NULL DEFAULT NULL,
  `vote` timestamp NULL DEFAULT NULL,
  `adventure` timestamp NULL DEFAULT NULL,
  `pray` timestamp NULL DEFAULT NULL,
  `sacrifice` timestamp NULL DEFAULT NULL,
  `steal` timestamp NULL DEFAULT NULL,
  `hunt` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  KEY `idx_cooldowns_user` (`user_id`),
  CONSTRAINT `cooldowns_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `crate_history` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) DEFAULT NULL,
  `crate_type` varchar(64) DEFAULT NULL,
  `item_name` varchar(255) DEFAULT NULL,
  `item_stats` int(11) DEFAULT NULL,
  `opened_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `crate_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=142 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `divine_blessings` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) DEFAULT NULL,
  `effect` varchar(64) NOT NULL,
  `value` double NOT NULL,
  `expires_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `blessing_name` varchar(128) NOT NULL,
  `purchased_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_divine_blessings_user` (`user_id`,`expires_at`),
  CONSTRAINT `divine_blessings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `epic_adventures` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) DEFAULT NULL,
  `adventure_type` varchar(32) NOT NULL,
  `adventure_name` varchar(255) NOT NULL,
  `difficulty` int(11) NOT NULL,
  `started_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `finish_at` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `status` varchar(32) DEFAULT 'active',
  `base_xp_reward` int(11) NOT NULL,
  `base_gold_reward` int(11) NOT NULL,
  `item_quality_min` int(11) NOT NULL,
  `item_quality_max` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_epic_adventures_user` (`user_id`,`status`),
  KEY `idx_epic_adventures_finish` (`finish_at`,`status`),
  CONSTRAINT `epic_adventures_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5843 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `equipped_slots` (
  `user_id` bigint(20) NOT NULL,
  `slot` varchar(32) NOT NULL,
  `item_id` bigint(20) NOT NULL,
  `equipped_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`user_id`,`slot`),
  UNIQUE KEY `uq_item` (`item_id`),
  KEY `idx_equipped_slots_user` (`user_id`),
  CONSTRAINT `equipped_slots_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `equipped_slots_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `inventory` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `event_participation` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) DEFAULT NULL,
  `event_type` varchar(64) DEFAULT NULL,
  `event_data` text DEFAULT NULL,
  `participated_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `event_participation_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `gods` (
  `name` varchar(64) NOT NULL,
  `description` text DEFAULT NULL,
  `luck_bonus` double DEFAULT 1,
  `sacrifice_multiplier` double DEFAULT 1,
  `top_followers` text DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `guild` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `icon` varchar(512) DEFAULT NULL,
  `owner` bigint(20) DEFAULT NULL,
  `balance` bigint(20) DEFAULT 0,
  `memberlimit` int(11) DEFAULT 50,
  `wins` int(11) DEFAULT 0,
  `loses` int(11) DEFAULT 0,
  `level` int(11) DEFAULT 1,
  `xp` int(11) DEFAULT 0,
  `privacy` tinyint(1) DEFAULT 1,
  `color` int(11) DEFAULT NULL,
  `upgrade` int(11) DEFAULT 0,
  `alliance` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `owner` (`owner`),
  CONSTRAINT `guild_ibfk_1` FOREIGN KEY (`owner`) REFERENCES `profile` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `guild_members` (
  `guild_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `rank` varchar(64) DEFAULT 'Member',
  `joined_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`guild_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `guild_members_ibfk_1` FOREIGN KEY (`guild_id`) REFERENCES `guild` (`id`) ON DELETE CASCADE,
  CONSTRAINT `guild_members_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `inventory` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `owner` bigint(20) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `value` int(11) DEFAULT 0,
  `type` varchar(32) NOT NULL,
  `damage` int(11) DEFAULT 0,
  `armor` int(11) DEFAULT 0,
  `hand` varchar(16) DEFAULT NULL,
  `equipped` tinyint(1) DEFAULT 0,
  `health_bonus` int(11) DEFAULT 0,
  `speed_bonus` int(11) DEFAULT 0,
  `luck_bonus` double DEFAULT 0,
  `crit_bonus` double DEFAULT 0,
  `magic_bonus` int(11) DEFAULT 0,
  `slot_type` varchar(32) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_inventory_owner` (`owner`),
  KEY `idx_inventory_equipped` (`owner`,`equipped`),
  KEY `idx_inventory_slot_type` (`slot_type`),
  CONSTRAINT `inventory_ibfk_1` FOREIGN KEY (`owner`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=47320 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `market` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `item_id` bigint(20) DEFAULT NULL,
  `price` int(11) NOT NULL,
  `listed_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `item_id` (`item_id`),
  KEY `idx_market_price` (`price`),
  CONSTRAINT `market_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `inventory` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=87 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `marriages` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user1` bigint(20) DEFAULT NULL,
  `user2` bigint(20) DEFAULT NULL,
  `married_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `lovescore` int(11) DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_marriage` (`user1`,`user2`),
  KEY `user2` (`user2`),
  CONSTRAINT `marriages_ibfk_1` FOREIGN KEY (`user1`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `marriages_ibfk_2` FOREIGN KEY (`user2`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `penalties` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) DEFAULT NULL,
  `penalty_type` varchar(64) NOT NULL,
  `penalty_seconds` int(11) NOT NULL,
  `applied_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_penalties_user` (`user_id`),
  CONSTRAINT `penalties_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=207 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `personal_quests` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) DEFAULT NULL,
  `quest_title` varchar(255) NOT NULL,
  `quest_theme` varchar(128) NOT NULL,
  `quest_context` text DEFAULT NULL,
  `current_chapter` int(11) DEFAULT 1,
  `total_chapters` int(11) DEFAULT 3,
  `status` varchar(32) DEFAULT 'active',
  `started_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `completed_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_personal_quests_user` (`user_id`,`status`),
  CONSTRAINT `personal_quests_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=666 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `pets` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `owner` bigint(20) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `hunger` int(11) DEFAULT 100,
  `thirst` int(11) DEFAULT 100,
  `love` int(11) DEFAULT 0,
  `joy` int(11) DEFAULT 100,
  `last_fed` timestamp NOT NULL DEFAULT current_timestamp(),
  `last_watered` timestamp NOT NULL DEFAULT current_timestamp(),
  `last_played` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `owner` (`owner`),
  CONSTRAINT `pets_ibfk_1` FOREIGN KEY (`owner`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `profile` (
  `user_id` bigint(20) NOT NULL,
  `name` varchar(255) NOT NULL,
  `money` bigint(20) DEFAULT 0,
  `xp` bigint(20) DEFAULT 0,
  `level` int(11) DEFAULT 1,
  `class` varchar(64) DEFAULT 'Novice',
  `race` varchar(64) DEFAULT 'Human',
  `pvpwins` int(11) DEFAULT 0,
  `pvplosses` int(11) DEFAULT 0,
  `deaths` int(11) DEFAULT 0,
  `kills` int(11) DEFAULT 0,
  `completed` int(11) DEFAULT 0,
  `god` varchar(64) DEFAULT NULL,
  `favor` int(11) DEFAULT 0,
  `luck` double DEFAULT 1,
  `marriage` bigint(20) DEFAULT NULL,
  `guild` int(11) DEFAULT NULL,
  `background` varchar(512) DEFAULT 'https://i.imgur.com/default.png',
  `description` text DEFAULT NULL,
  `colour` int(11) DEFAULT 0,
  `donations` int(11) DEFAULT 0,
  `raidstats` int(11) DEFAULT 0,
  `atkmultiply` double DEFAULT 1,
  `defmultiply` double DEFAULT 1,
  `crates_common` int(11) DEFAULT 0,
  `crates_uncommon` int(11) DEFAULT 0,
  `crates_rare` int(11) DEFAULT 0,
  `crates_magic` int(11) DEFAULT 0,
  `crates_legendary` int(11) DEFAULT 0,
  `crates_mystery` int(11) DEFAULT 0,
  `last_date` varchar(32) DEFAULT NULL,
  `streak` int(11) DEFAULT 0,
  `vote_ban` int(11) DEFAULT 0,
  `has_character` tinyint(1) DEFAULT 1,
  `reset_points` int(11) DEFAULT 2,
  `last_adventure` varchar(64) DEFAULT NULL,
  `adventure_alert` tinyint(1) DEFAULT 1,
  `alignment` varchar(32) DEFAULT 'neutral',
  `epic_adventures_completed` int(11) DEFAULT 0,
  `legendary_adventures_completed` int(11) DEFAULT 0,
  `last_epic_adventure` varchar(64) DEFAULT NULL,
  `ascension_respec_used` tinyint(1) DEFAULT 0,
  `previous_class` varchar(64) DEFAULT NULL,
  `sell_confirmation` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `quest_chapters` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `quest_id` bigint(20) DEFAULT NULL,
  `chapter_number` int(11) NOT NULL,
  `chapter_title` varchar(255) NOT NULL,
  `chapter_narrative` text NOT NULL,
  `objective_type` varchar(64) NOT NULL,
  `objective_target` int(11) NOT NULL,
  `objective_progress` int(11) DEFAULT 0,
  `objective_description` text NOT NULL,
  `rewards_xp` int(11) DEFAULT 0,
  `rewards_gold` int(11) DEFAULT 0,
  `rewards_crate` varchar(64) DEFAULT NULL,
  `status` varchar(32) DEFAULT 'locked',
  `started_at` timestamp NULL DEFAULT NULL,
  `completed_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_quest_chapter` (`quest_id`,`chapter_number`),
  KEY `idx_quest_chapters_quest` (`quest_id`,`status`),
  CONSTRAINT `quest_chapters_ibfk_1` FOREIGN KEY (`quest_id`) REFERENCES `personal_quests` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2565 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `quest_history` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) DEFAULT NULL,
  `quest_title` varchar(255) NOT NULL,
  `quest_theme` varchar(128) NOT NULL,
  `chapters_completed` int(11) DEFAULT NULL,
  `total_xp_earned` int(11) DEFAULT 0,
  `total_gold_earned` int(11) DEFAULT 0,
  `completion_narrative` text DEFAULT NULL,
  `completed_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `quest_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=292 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `raid_bosses` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `hp` int(11) NOT NULL,
  `max_hp` int(11) NOT NULL,
  `attack` int(11) NOT NULL,
  `defense` int(11) NOT NULL,
  `active` tinyint(1) DEFAULT 1,
  `participants` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `server_settings` (
  `guild_id` bigint(20) NOT NULL,
  `prefix` varchar(16) DEFAULT '!',
  `language` varchar(16) DEFAULT 'en_US',
  `currency_emoji` varchar(32) DEFAULT NULL,
  `welcome_channel` bigint(20) DEFAULT NULL,
  `game_channel` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`guild_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `tournaments` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_by` bigint(20) DEFAULT NULL,
  `prize_money` int(11) DEFAULT 0,
  `participants` text DEFAULT NULL,
  `winner` bigint(20) DEFAULT NULL,
  `started_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `ended_at` timestamp NULL DEFAULT NULL,
  `status` varchar(32) DEFAULT 'pending',
  PRIMARY KEY (`id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `tournaments_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `profile` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `trade_offers` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `from_user` bigint(20) DEFAULT NULL,
  `to_user` bigint(20) DEFAULT NULL,
  `item_id` bigint(20) DEFAULT NULL,
  `price` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `status` varchar(32) DEFAULT 'pending',
  PRIMARY KEY (`id`),
  KEY `from_user` (`from_user`),
  KEY `to_user` (`to_user`),
  KEY `item_id` (`item_id`),
  CONSTRAINT `trade_offers_ibfk_1` FOREIGN KEY (`from_user`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `trade_offers_ibfk_2` FOREIGN KEY (`to_user`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `trade_offers_ibfk_3` FOREIGN KEY (`item_id`) REFERENCES `inventory` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `transactions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `from_user` bigint(20) DEFAULT NULL,
  `to_user` bigint(20) DEFAULT NULL,
  `amount` int(11) DEFAULT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `info` text DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_transactions_users` (`from_user`,`to_user`)
) ENGINE=InnoDB AUTO_INCREMENT=6157 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `user_settings` (
  `user_id` bigint(20) NOT NULL,
  `language` varchar(16) DEFAULT 'en_US',
  `notifications` tinyint(1) DEFAULT 1,
  `dm_notifications` tinyint(1) DEFAULT 0,
  `mention_notifications` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `user_settings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `profile` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Default gods
INSERT IGNORE INTO gods (name, description, luck_bonus, sacrifice_multiplier) VALUES
    ('Chaos', 'God of randomness and disorder', 1.2, 0.8),
    ('Order', 'God of structure and planning', 0.9, 1.1),
    ('War', 'God of combat and conflict', 1.0, 1.0),
    ('Nature', 'God of life and growth', 1.1, 0.9),
    ('Death', 'God of endings and rebirth', 0.8, 1.3);
