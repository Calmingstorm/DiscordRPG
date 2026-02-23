<?php
/**
 * DiscordRPG Web Leaderboards
 * Displays stats from SQLite database
 */

// Set timezone to EST
date_default_timezone_set('America/New_York');

// Prevent caching
header("Cache-Control: no-cache, no-store, must-revalidate");
header("Pragma: no-cache");
header("Expires: 0");

// Abbreviate large numbers (e.g., 3.5M, 1.2B, 4.7T)
function abbreviate_number($num) {
    if ($num >= 1e12) {
        return number_format($num / 1e12, 1) . 'T';
    } elseif ($num >= 1e9) {
        return number_format($num / 1e9, 1) . 'B';
    } elseif ($num >= 1e6) {
        return number_format($num / 1e6, 1) . 'M';
    } elseif ($num >= 1e4) {
        return number_format($num / 1e3, 1) . 'K';
    }
    return number_format($num);
}

require_once __DIR__ . '/db_config.php';

try {
    $pdo = get_discordrpg_pdo();
} catch (Exception $e) {
    die("Database connection failed: " . $e->getMessage());
}

// Get guild info
$guild_name = "The Calming Storm";

// Get leaderboard data with additional fields
function getLeaderboard($pdo, $type, $limit = 10) {
    switch ($type) {
        case 'level':
            $sql = "SELECT name, level, xp, class, race FROM profile ORDER BY level DESC, xp DESC LIMIT ?";
            break;
        case 'money':
            $sql = "SELECT name, level, money, class FROM profile ORDER BY money DESC LIMIT ?";
            break;
        case 'pvp':
            $sql = "SELECT name, level, pvpwins, pvplosses, (pvpwins + pvplosses) as total_fights, class FROM profile WHERE (pvpwins + pvplosses) > 0 ORDER BY pvpwins DESC LIMIT ?";
            break;
        case 'adventures':
            $sql = "SELECT name, level, completed, class FROM profile ORDER BY completed DESC LIMIT ?";
            break;
        case 'equipment_power':
            $sql = "SELECT 
                        p.name, p.level, p.class, p.race,
                        -- Calculate approximate base stats + equipment power to match !profile Total Power
                        -- Base stats approximation based on class progression
                        ROUND(
                            CASE 
                                -- Calibrated based on actual profile data
                                WHEN p.class = 'Sorcerer' THEN p.level * 0.6 + 2.2  -- Level 18 = 13 attack
                                WHEN p.class = 'Warlord' THEN p.level * 0.5 + 3  -- Level 18 = 12 attack
                                WHEN p.class IN ('Warrior', 'Swordsman', 'Knight', 'Berserker', 'Paladin') THEN p.level * 0.7 + 3
                                WHEN p.class IN ('Thief', 'Rogue', 'Assassin', 'Bandit', 'Shadow', 'Nightblade') THEN p.level * 0.6 + 3  
                                WHEN p.class IN ('Mage', 'Wizard', 'Warlock', 'Archmage', 'Necromancer') THEN p.level * 0.6 + 2
                                WHEN p.class IN ('Ranger', 'Hunter', 'Tracker', 'Bowmaster', 'Beastmaster', 'Marksman') THEN p.level * 0.65 + 3
                                WHEN p.class IN ('Raider', 'Viking', 'Chieftain', 'Ravager', 'Conqueror', 'Warchief') THEN p.level * 0.6 + 3
                                ELSE p.level * 0.6 + 2
                            END +
                            CASE 
                                -- Calibrated based on actual profile data
                                WHEN p.class = 'Sorcerer' THEN p.level * 0.4 + 2.8  -- Level 18 = 10 defense
                                WHEN p.class = 'Warlord' THEN p.level * 0.6 + 3.2  -- Level 18 = 14 defense
                                WHEN p.class IN ('Warrior', 'Swordsman', 'Knight', 'Berserker', 'Paladin') THEN p.level * 0.6 + 3
                                WHEN p.class IN ('Thief', 'Rogue', 'Assassin', 'Bandit', 'Shadow', 'Nightblade') THEN p.level * 0.5 + 2
                                WHEN p.class IN ('Mage', 'Wizard', 'Warlock', 'Archmage', 'Necromancer') THEN p.level * 0.4 + 3
                                WHEN p.class IN ('Ranger', 'Hunter', 'Tracker', 'Bowmaster', 'Beastmaster', 'Marksman') THEN p.level * 0.5 + 3  
                                WHEN p.class IN ('Raider', 'Viking', 'Chieftain', 'Ravager', 'Conqueror', 'Warchief') THEN p.level * 0.55 + 3
                                ELSE p.level * 0.4 + 3
                            END
                        ) +
                        COALESCE(SUM(i.damage + i.armor + 
                            COALESCE(i.health_bonus, 0) + 
                            COALESCE(i.speed_bonus, 0) + 
                            COALESCE(i.luck_bonus * 100, 0) + 
                            COALESCE(i.crit_bonus * 100, 0) + 
                            COALESCE(i.magic_bonus, 0)), 0) as equipment_power
                    FROM profile p
                    LEFT JOIN inventory i ON p.user_id = i.owner AND i.equipped = 1
                    GROUP BY p.user_id, p.name, p.level, p.class, p.race
                    ORDER BY equipment_power DESC 
                    LIMIT ?";
            break;
        case 'raids':
            $sql = "SELECT name, level, raidstats, class FROM profile WHERE raidstats > 0 ORDER BY raidstats DESC LIMIT ?";
            break;
        default:
            return [];
    }
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute([$limit]);
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}

// Get recent activity feed
function getRecentActivity($pdo, $limit = 10) {
    $activities = [];
    
    // Recent level ups (high level players)
    try {
        $levelups = $pdo->prepare("SELECT name, level, class FROM profile WHERE level >= 10 ORDER BY level DESC LIMIT ?");
        $levelups->execute([5]);
        foreach ($levelups->fetchAll(PDO::FETCH_ASSOC) as $player) {
            $activities[] = [
                'type' => 'level',
                'icon' => 'fas fa-level-up-alt',
                'color' => 'var(--text-accent)',
                'text' => "{$player['name']} reached Level {$player['level']}!",
                'class' => $player['class']
            ];
        }
    } catch (Exception $e) {}
    
    // Legendary items (high value items)
    try {
        $items = $pdo->prepare("
            SELECT i.name as item_name, i.damage, i.armor, i.value, p.name as owner_name
            FROM inventory i 
            JOIN profile p ON i.owner = p.user_id 
            WHERE (i.damage + i.armor) >= 30 OR i.value >= 5000
            ORDER BY (i.damage + i.armor + i.value/100) DESC 
            LIMIT ?
        ");
        $items->execute([3]);
        foreach ($items->fetchAll(PDO::FETCH_ASSOC) as $item) {
            $activities[] = [
                'type' => 'item',
                'icon' => 'fas fa-gem',
                'color' => '#ff6b35',
                'text' => "{$item['owner_name']} found legendary {$item['item_name']}!",
                'stats' => "{$item['damage']}⚔️ {$item['armor']}🛡️"
            ];
        }
    } catch (Exception $e) {}
    
    // Rich players
    try {
        $wealthy = $pdo->prepare("SELECT name, money FROM profile WHERE money >= 50000 ORDER BY money DESC LIMIT ?");
        $wealthy->execute([3]);
        foreach ($wealthy->fetchAll(PDO::FETCH_ASSOC) as $player) {
            $activities[] = [
                'type' => 'wealth',
                'icon' => 'fas fa-coins',
                'color' => 'var(--gold)',
                'text' => "{$player['name']} amassed " . abbreviate_number($player['money']) . " gold!",
                'amount' => abbreviate_number($player['money'])
            ];
        }
    } catch (Exception $e) {}
    
    // Recent raid victories
    try {
        $raiders = $pdo->prepare("SELECT name, raidstats, class FROM profile WHERE raidstats >= 5 ORDER BY raidstats DESC LIMIT ?");
        $raiders->execute([3]);
        foreach ($raiders->fetchAll(PDO::FETCH_ASSOC) as $raider) {
            $activities[] = [
                'type' => 'raid',
                'icon' => 'fas fa-dragon',
                'color' => '#e74c3c',
                'text' => "{$raider['name']} conquered {$raider['raidstats']} raids!",
                'class' => $raider['class']
            ];
        }
    } catch (Exception $e) {}
    
    // Shuffle and limit
    shuffle($activities);
    return array_slice($activities, 0, $limit);
}

// Get adventure tier statistics
function getAdventureTierStats($pdo) {
    try {
        // Get currently active adventures
        $regular_stmt = $pdo->query("
            SELECT 
                COUNT(*) as total_adventures,
                SUM(CASE WHEN 
                    strftime('%s', finish_at) - strftime('%s', started_at) <= 3600 
                    THEN 1 ELSE 0 END) as short_est,
                SUM(CASE WHEN 
                    strftime('%s', finish_at) - strftime('%s', started_at) > 3600 
                    AND strftime('%s', finish_at) - strftime('%s', started_at) <= 10800 
                    THEN 1 ELSE 0 END) as medium_est,
                SUM(CASE WHEN 
                    strftime('%s', finish_at) - strftime('%s', started_at) > 10800 
                    THEN 1 ELSE 0 END) as long_est
            FROM adventures 
            WHERE status = 'active'
        ");
        $regular_stats = $regular_stmt->fetch(PDO::FETCH_ASSOC);
        
        // Get active epic/legendary adventures (if table exists)
        try {
            $epic_stmt = $pdo->query("
                SELECT 
                    SUM(CASE WHEN adventure_type = 'epic' THEN 1 ELSE 0 END) as epic_count,
                    SUM(CASE WHEN adventure_type = 'legendary' THEN 1 ELSE 0 END) as legendary_count
                FROM epic_adventures 
                WHERE status = 'active'
            ");
            $epic_stats = $epic_stmt->fetch(PDO::FETCH_ASSOC);
        } catch (Exception $e) {
            // Table doesn't exist yet, use zeros
            $epic_stats = ['epic_count' => 0, 'legendary_count' => 0];
        }
        
        return [
            'total_adventures' => $regular_stats['total_adventures'] + ($epic_stats['epic_count'] ?? 0) + ($epic_stats['legendary_count'] ?? 0),
            'short_est' => $regular_stats['short_est'] ?? 0,
            'medium_est' => $regular_stats['medium_est'] ?? 0,
            'long_est' => $regular_stats['long_est'] ?? 0,
            'epic_est' => $epic_stats['epic_count'] ?? 0,
            'legendary_est' => $epic_stats['legendary_count'] ?? 0
        ];
    } catch (Exception $e) {
        return [
            'total_adventures' => 0,
            'short_est' => 0, 
            'medium_est' => 0,
            'long_est' => 0, 
            'epic_est' => 0,
            'legendary_est' => 0
        ];
    }
}

// Get online players count (estimate based on recent activity)
function getOnlinePlayersEstimate($pdo) {
    try {
        // Consider players "online" if they have high level or recent activity
        $stmt = $pdo->query("SELECT COUNT(*) FROM profile WHERE level >= 5");
        return $stmt->fetchColumn();
    } catch (Exception $e) {
        return 0;
    }
}

// Get enhanced stats
$total_players = $pdo->query("SELECT COUNT(*) FROM profile")->fetchColumn();
$total_adventures = $pdo->query("SELECT COUNT(*) FROM adventures")->fetchColumn();
$total_items = $pdo->query("SELECT COUNT(*) FROM inventory")->fetchColumn();
$total_gold = $pdo->query("SELECT SUM(money) FROM profile")->fetchColumn();
$max_level = $pdo->query("SELECT MAX(level) FROM profile")->fetchColumn();
$total_pvp_battles = $pdo->query("SELECT SUM(pvpwins + pvplosses) FROM profile")->fetchColumn();

// Get new enhanced stats
$online_players_est = getOnlinePlayersEstimate($pdo);
$total_raids = $pdo->query("SELECT SUM(raidstats) FROM profile")->fetchColumn();
$adventure_tier_stats = getAdventureTierStats($pdo);

// Get class distribution
$class_stats = $pdo->query("SELECT class, COUNT(*) as count FROM profile GROUP BY class ORDER BY count DESC")->fetchAll(PDO::FETCH_ASSOC);

// Get race distribution  
$race_stats = $pdo->query("SELECT race, COUNT(*) as count FROM profile GROUP BY race ORDER BY count DESC")->fetchAll(PDO::FETCH_ASSOC);

// Get recent activity
$recent_activity = getRecentActivity($pdo, 8);

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DiscordRPG Leaderboards - <?php echo htmlspecialchars($guild_name); ?></title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-bg: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            --secondary-bg: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%);
            --accent-bg: linear-gradient(135deg, #3a3a3a 0%, #4a4a4a 100%);
            --card-bg: rgba(42, 42, 42, 0.9);
            --card-border: rgba(100, 100, 100, 0.2);
            --text-primary: #e0e0e0;
            --text-secondary: #b0b0b0;
            --text-accent: #d4af37;
            --text-highlight: #8b4513;
            --border-subtle: rgba(212, 175, 55, 0.2);
            --border-accent: rgba(212, 175, 55, 0.4);
            --shadow-soft: 0 4px 12px rgba(0, 0, 0, 0.3);
            --shadow-medium: 0 6px 16px rgba(0, 0, 0, 0.4);
            --hover-bg: rgba(212, 175, 55, 0.1);
            --gold: #d4af37;
            --silver: #c0c0c0;
            --bronze: #cd7f32;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--primary-bg);
            background-attachment: fixed;
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header Section */
        .header {
            text-align: center;
            margin-bottom: 50px;
            position: relative;
        }

        .main-title {
            font-family: 'Orbitron', monospace;
            font-size: clamp(2.5em, 6vw, 4.5em);
            font-weight: 700;
            color: var(--text-accent);
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            letter-spacing: 1px;
        }

        .guild-name {
            font-size: 1.2em;
            margin-bottom: 20px;
            color: var(--text-secondary);
            font-weight: 400;
        }

        .last-updated {
            background: var(--secondary-bg);
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            padding: 6px 16px;
            display: inline-block;
            font-size: 0.85em;
            color: var(--text-secondary);
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 25px;
            margin-bottom: 50px;
        }

        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            transition: all 0.2s ease;
        }

        .stat-card:hover {
            border-color: var(--border-accent);
            box-shadow: var(--shadow-medium);
            background: rgba(42, 42, 42, 0.95);
        }

        .stat-icon {
            font-size: 2.2em;
            margin-bottom: 12px;
            color: var(--text-accent);
        }

        .stat-number {
            font-family: 'Orbitron', monospace;
            font-size: 2em;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
        }

        .stat-label {
            font-size: 0.95em;
            color: var(--text-secondary);
            font-weight: 500;
        }

        /* Leaderboards Grid */
        .leaderboards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }

        .leaderboard {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 24px;
            transition: all 0.2s ease;
        }

        .leaderboard:hover {
            box-shadow: var(--shadow-soft);
        }

        .leaderboard-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-subtle);
        }

        .leaderboard-icon {
            font-size: 1.5em;
            margin-right: 12px;
            color: var(--text-accent);
        }

        .leaderboard h2 {
            font-family: 'Orbitron', monospace;
            font-size: 1.3em;
            font-weight: 600;
            color: var(--text-accent);
            letter-spacing: 0.5px;
        }

        /* Player Cards */
        .player {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            margin: 6px 0;
            background: rgba(60, 60, 60, 0.3);
            border: 1px solid rgba(100, 100, 100, 0.2);
            border-radius: 6px;
            transition: all 0.2s ease;
        }

        .player:hover {
            background: var(--hover-bg);
            border-color: var(--border-subtle);
        }

        .player-left {
            display: flex;
            align-items: center;
            flex: 1;
        }

        .rank {
            font-family: 'Orbitron', monospace;
            font-weight: 600;
            font-size: 0.95em;
            margin-right: 12px;
            min-width: 30px;
            text-align: center;
        }

        .rank-1 { color: var(--gold); }
        .rank-2 { color: var(--silver); }
        .rank-3 { color: var(--bronze); }

        .medal {
            font-size: 1.2em;
            margin-right: 8px;
        }

        .player-info {
            flex: 1;
        }

        .player-name {
            font-weight: 500;
            font-size: 1em;
            margin-bottom: 2px;
            color: var(--text-primary);
        }

        .player-class {
            font-size: 0.8em;
            color: var(--text-secondary);
        }

        .player-value {
            text-align: right;
            font-family: 'Orbitron', monospace;
            font-weight: 500;
        }

        .value-main {
            font-size: 1.1em;
            color: var(--text-accent);
        }

        .value-sub {
            font-size: 0.75em;
            color: var(--text-secondary);
            margin-top: 2px;
        }

        /* Additional Stats Section */
        .additional-stats {
            margin-top: 40px;
            padding: 24px;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
        }

        .additional-stats h3 {
            font-family: 'Orbitron', monospace;
            color: var(--text-accent);
            margin-bottom: 16px;
            text-align: center;
            font-size: 1.3em;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .class-distribution {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
        }

        .class-item {
            background: rgba(60, 60, 60, 0.3);
            border: 1px solid rgba(100, 100, 100, 0.2);
            border-radius: 6px;
            padding: 12px;
            text-align: center;
            transition: all 0.2s ease;
        }

        .class-item:hover {
            background: var(--hover-bg);
            border-color: var(--border-subtle);
        }

        .class-count {
            font-family: 'Orbitron', monospace;
            font-size: 1.3em;
            color: var(--text-accent);
            font-weight: 600;
            margin-bottom: 4px;
        }

        /* Recent Activity Styles */
        .recent-activity {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 24px;
        }

        .recent-activity h3 {
            font-family: 'Orbitron', monospace;
            color: var(--text-accent);
            margin-bottom: 20px;
            text-align: center;
            font-size: 1.3em;
            font-weight: 600;
        }

        .activity-feed {
            display: grid;
            gap: 12px;
        }

        .activity-item {
            display: flex;
            align-items: center;
            padding: 12px;
            background: rgba(60, 60, 60, 0.3);
            border: 1px solid rgba(100, 100, 100, 0.2);
            border-radius: 6px;
            transition: all 0.2s ease;
        }

        .activity-item:hover {
            background: var(--hover-bg);
            border-color: var(--border-subtle);
        }

        .activity-icon {
            font-size: 1.2em;
            margin-right: 12px;
            width: 24px;
            text-align: center;
        }

        .activity-text {
            font-weight: 500;
            color: var(--text-primary);
            flex: 1;
        }

        .activity-stats {
            font-size: 0.8em;
            color: var(--text-secondary);
            margin-top: 2px;
        }

        .activity-class {
            font-size: 0.8em;
            color: var(--text-accent);
            margin-top: 2px;
        }

        /* Adventure Tiers Styles */
        .adventure-tiers {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 40px;
        }

        .adventure-tiers h3 {
            font-family: 'Orbitron', monospace;
            color: var(--text-accent);
            margin-bottom: 20px;
            text-align: center;
            font-size: 1.3em;
            font-weight: 600;
        }

        .tier-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }

        .tier-card {
            background: rgba(60, 60, 60, 0.3);
            border: 1px solid rgba(100, 100, 100, 0.2);
            border-radius: 6px;
            padding: 16px;
            text-align: center;
            transition: all 0.2s ease;
        }

        .tier-card:hover {
            background: var(--hover-bg);
            border-color: var(--border-subtle);
        }

        .tier-icon {
            font-size: 1.5em;
            margin-bottom: 8px;
        }

        .tier-name {
            font-family: 'Orbitron', monospace;
            font-weight: 600;
            color: var(--text-accent);
            margin-bottom: 8px;
        }

        .tier-count {
            font-family: 'Orbitron', monospace;
            font-size: 1.2em;
            color: var(--text-primary);
            font-weight: 600;
            margin-bottom: 4px;
        }

        .tier-duration {
            font-size: 0.8em;
            color: var(--text-secondary);
        }

        /* Distribution Stats Styles */
        .distribution-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }

        .distribution-section {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 24px;
        }

        .distribution-section h3 {
            font-family: 'Orbitron', monospace;
            color: var(--text-accent);
            margin-bottom: 16px;
            text-align: center;
            font-size: 1.3em;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .race-distribution {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
        }

        .race-item {
            background: rgba(60, 60, 60, 0.3);
            border: 1px solid rgba(100, 100, 100, 0.2);
            border-radius: 6px;
            padding: 12px;
            text-align: center;
            transition: all 0.2s ease;
        }

        .race-item:hover {
            background: var(--hover-bg);
            border-color: var(--border-subtle);
        }

        .race-count {
            font-family: 'Orbitron', monospace;
            font-size: 1.3em;
            color: var(--text-accent);
            font-weight: 600;
            margin-bottom: 4px;
        }

        /* Refresh Button */
        .refresh-section {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
        }

        .refresh-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--secondary-bg);
            color: var(--text-primary);
            padding: 10px 20px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s ease;
            border: 1px solid var(--border-subtle);
            font-size: 0.95em;
        }

        .refresh-btn:hover {
            background: var(--hover-bg);
            border-color: var(--border-accent);
            text-decoration: none;
            color: var(--text-accent);
            transform: translateY(-1px);
            box-shadow: var(--shadow-soft);
        }

        .refresh-icon {
            animation: spin 2s linear infinite paused;
        }

        .refresh-btn:hover .refresh-icon {
            animation-play-state: running;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        /* Responsive Design */
        @media (max-width: 1200px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }

        @media (max-width: 768px) {
            .container { padding: 15px; }
            .main-title { font-size: 2.5em; }
            .leaderboards { grid-template-columns: 1fr; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }

        @media (max-width: 480px) {
            .stats-grid { grid-template-columns: 1fr; }
            .player { padding: 12px; }
            .leaderboard { padding: 20px; }
        }

        /* Loading Animation */
        .loading {
            display: none;
            text-align: center;
            padding: 50px;
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-top: 3px solid var(--gold);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1 class="main-title">
                <i class="fas fa-sword"></i>
                DiscordRPG Leaderboards
                <i class="fas fa-shield-alt"></i>
            </h1>
            <div class="guild-name">
                <i class="fas fa-crown"></i> Guild: <?php echo htmlspecialchars($guild_name); ?>
            </div>
            <div class="last-updated">
                <i class="fas fa-clock"></i> Last updated: <?php echo date('M j, Y • g:i A'); ?>
                <span style="margin-left: 15px; color: #22c55e;">
                    <i class="fas fa-circle" style="animation: pulse 2s infinite;"></i> Live Data
                </span>
            </div>
            <div style="margin-top: 15px; display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
                <a href="guide.php" class="refresh-btn">
                    <i class="fas fa-scroll"></i>
                    Game Guide
                </a>
                <a href="top-items.php" class="refresh-btn">
                    <i class="fas fa-trophy"></i>
                    Top Items
                </a>
            </div>
        </div>

        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-users"></i></div>
                <div class="stat-number"><?php echo number_format($total_players); ?></div>
                <div class="stat-label">Total Players</div>
            </div>
            <div class="stat-card" style="border-color: var(--border-accent);">
                <div class="stat-icon" style="color: #22c55e;"><i class="fas fa-circle"></i></div>
                <div class="stat-number"><?php echo number_format($online_players_est); ?></div>
                <div class="stat-label">Active Players</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-map"></i></div>
                <div class="stat-number"><?php echo number_format($total_adventures); ?></div>
                <div class="stat-label">Adventures</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-dragon"></i></div>
                <div class="stat-number"><?php echo number_format($total_raids); ?></div>
                <div class="stat-label">Raids Won</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-gem"></i></div>
                <div class="stat-number"><?php echo number_format($total_items); ?></div>
                <div class="stat-label">Items Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-coins"></i></div>
                <div class="stat-number"><?php echo abbreviate_number($total_gold); ?></div>
                <div class="stat-label">Total Gold</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-level-up-alt"></i></div>
                <div class="stat-number"><?php echo $max_level; ?></div>
                <div class="stat-label">Max Level</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-fist-raised"></i></div>
                <div class="stat-number"><?php echo number_format($total_pvp_battles); ?></div>
                <div class="stat-label">PvP Battles</div>
            </div>
        </div>

        <!-- Leaderboards -->
        <div class="leaderboards">
            <!-- Level Leaderboard -->
            <div class="leaderboard">
                <div class="leaderboard-header">
                    <div class="leaderboard-icon"><i class="fas fa-trophy"></i></div>
                    <h2>Top Levels</h2>
                </div>
                <?php 
                $levels = getLeaderboard($pdo, 'level');
                foreach ($levels as $i => $player): 
                    $medal = $i == 0 ? "🥇" : ($i == 1 ? "🥈" : ($i == 2 ? "🥉" : ""));
                    $rank_class = $i < 3 ? "rank-" . ($i + 1) : "";
                ?>
                <div class="player">
                    <div class="player-left">
                        <?php if ($medal): ?>
                            <span class="medal"><?php echo $medal; ?></span>
                        <?php endif; ?>
                        <span class="rank <?php echo $rank_class; ?>">#<?php echo $i + 1; ?></span>
                        <div class="player-info">
                            <div class="player-name"><?php echo htmlspecialchars($player['name']); ?></div>
                            <div class="player-class"><?php echo htmlspecialchars($player['class']) . ' ' . htmlspecialchars($player['race']); ?></div>
                        </div>
                    </div>
                    <div class="player-value">
                        <div class="value-main">Level <?php echo $player['level']; ?></div>
                        <div class="value-sub"><?php echo abbreviate_number($player['xp']); ?> XP</div>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>

            <!-- Wealth Leaderboard -->
            <div class="leaderboard">
                <div class="leaderboard-header">
                    <div class="leaderboard-icon"><i class="fas fa-coins"></i></div>
                    <h2>Richest Players</h2>
                </div>
                <?php 
                $wealth = getLeaderboard($pdo, 'money');
                foreach ($wealth as $i => $player): 
                    $medal = $i == 0 ? "🥇" : ($i == 1 ? "🥈" : ($i == 2 ? "🥉" : ""));
                    $rank_class = $i < 3 ? "rank-" . ($i + 1) : "";
                ?>
                <div class="player">
                    <div class="player-left">
                        <?php if ($medal): ?>
                            <span class="medal"><?php echo $medal; ?></span>
                        <?php endif; ?>
                        <span class="rank <?php echo $rank_class; ?>">#<?php echo $i + 1; ?></span>
                        <div class="player-info">
                            <div class="player-name"><?php echo htmlspecialchars($player['name']); ?></div>
                            <div class="player-class">Level <?php echo $player['level']; ?> <?php echo htmlspecialchars($player['class']); ?></div>
                        </div>
                    </div>
                    <div class="player-value">
                        <div class="value-main"><?php echo abbreviate_number($player['money']); ?></div>
                        <div class="value-sub">gold</div>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>

            <!-- PvP Leaderboard -->
            <div class="leaderboard">
                <div class="leaderboard-header">
                    <div class="leaderboard-icon"><i class="fas fa-sword"></i></div>
                    <h2>PvP Champions</h2>
                </div>
                <?php 
                $pvp = getLeaderboard($pdo, 'pvp');
                foreach ($pvp as $i => $player): 
                    $medal = $i == 0 ? "🥇" : ($i == 1 ? "🥈" : ($i == 2 ? "🥉" : ""));
                    $rank_class = $i < 3 ? "rank-" . ($i + 1) : "";
                    $winrate = $player['total_fights'] > 0 ? round(($player['pvpwins'] / $player['total_fights']) * 100, 1) : 0;
                ?>
                <div class="player">
                    <div class="player-left">
                        <?php if ($medal): ?>
                            <span class="medal"><?php echo $medal; ?></span>
                        <?php endif; ?>
                        <span class="rank <?php echo $rank_class; ?>">#<?php echo $i + 1; ?></span>
                        <div class="player-info">
                            <div class="player-name"><?php echo htmlspecialchars($player['name']); ?></div>
                            <div class="player-class">Level <?php echo $player['level']; ?> <?php echo htmlspecialchars($player['class']); ?></div>
                        </div>
                    </div>
                    <div class="player-value">
                        <div class="value-main"><?php echo $player['pvpwins']; ?> wins</div>
                        <div class="value-sub"><?php echo $winrate; ?>% winrate</div>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>

            <!-- Adventure Leaderboard -->
            <div class="leaderboard">
                <div class="leaderboard-header">
                    <div class="leaderboard-icon"><i class="fas fa-map"></i></div>
                    <h2>Top Adventurers</h2>
                </div>
                <?php 
                $adventures = getLeaderboard($pdo, 'adventures');
                foreach ($adventures as $i => $player): 
                    $medal = $i == 0 ? "🥇" : ($i == 1 ? "🥈" : ($i == 2 ? "🥉" : ""));
                    $rank_class = $i < 3 ? "rank-" . ($i + 1) : "";
                ?>
                <div class="player">
                    <div class="player-left">
                        <?php if ($medal): ?>
                            <span class="medal"><?php echo $medal; ?></span>
                        <?php endif; ?>
                        <span class="rank <?php echo $rank_class; ?>">#<?php echo $i + 1; ?></span>
                        <div class="player-info">
                            <div class="player-name"><?php echo htmlspecialchars($player['name']); ?></div>
                            <div class="player-class">Level <?php echo $player['level']; ?> <?php echo htmlspecialchars($player['class']); ?></div>
                        </div>
                    </div>
                    <div class="player-value">
                        <div class="value-main"><?php echo $player['completed']; ?></div>
                        <div class="value-sub">completed</div>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>

            <!-- Combat Power Leaderboard -->
            <div class="leaderboard" style="border-color: var(--border-accent);">
                <div class="leaderboard-header">
                    <div class="leaderboard-icon" style="color: #ff6b35;"><i class="fas fa-magic"></i></div>
                    <h2>Combat Power</h2>
                </div>
                <?php 
                $equipment = getLeaderboard($pdo, 'equipment_power');
                foreach ($equipment as $i => $player): 
                    $medal = $i == 0 ? "🥇" : ($i == 1 ? "🥈" : ($i == 2 ? "🥉" : ""));
                    $rank_class = $i < 3 ? "rank-" . ($i + 1) : "";
                ?>
                <div class="player">
                    <div class="player-left">
                        <?php if ($medal): ?>
                            <span class="medal"><?php echo $medal; ?></span>
                        <?php endif; ?>
                        <span class="rank <?php echo $rank_class; ?>">#<?php echo $i + 1; ?></span>
                        <div class="player-info">
                            <div class="player-name"><?php echo htmlspecialchars($player['name']); ?></div>
                            <div class="player-class">Level <?php echo $player['level']; ?> <?php echo htmlspecialchars($player['class']); ?></div>
                        </div>
                    </div>
                    <div class="player-value">
                        <div class="value-main"><?php echo number_format($player['equipment_power']); ?></div>
                        <div class="value-sub">combat power</div>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>

            <!-- Raid Champions Leaderboard -->
            <div class="leaderboard">
                <div class="leaderboard-header">
                    <div class="leaderboard-icon"><i class="fas fa-dragon"></i></div>
                    <h2>Raid Champions</h2>
                </div>
                <?php 
                $raids = getLeaderboard($pdo, 'raids');
                foreach ($raids as $i => $player): 
                    $medal = $i == 0 ? "🥇" : ($i == 1 ? "🥈" : ($i == 2 ? "🥉" : ""));
                    $rank_class = $i < 3 ? "rank-" . ($i + 1) : "";
                ?>
                <div class="player">
                    <div class="player-left">
                        <?php if ($medal): ?>
                            <span class="medal"><?php echo $medal; ?></span>
                        <?php endif; ?>
                        <span class="rank <?php echo $rank_class; ?>">#<?php echo $i + 1; ?></span>
                        <div class="player-info">
                            <div class="player-name"><?php echo htmlspecialchars($player['name']); ?></div>
                            <div class="player-class">Level <?php echo $player['level']; ?> <?php echo htmlspecialchars($player['class']); ?></div>
                        </div>
                    </div>
                    <div class="player-value">
                        <div class="value-main"><?php echo $player['raidstats']; ?></div>
                        <div class="value-sub">raids won</div>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>

        </div>

        <!-- Recent Activity Feed -->
        <div class="recent-activity" style="margin-bottom: 40px;">
            <h3><i class="fas fa-bolt"></i> Recent Activity</h3>
            <div class="activity-feed">
                <?php foreach ($recent_activity as $activity): ?>
                <div class="activity-item">
                    <div class="activity-icon">
                        <i class="<?php echo $activity['icon']; ?>" style="color: <?php echo $activity['color']; ?>;"></i>
                    </div>
                    <div class="activity-content">
                        <div class="activity-text"><?php echo htmlspecialchars($activity['text']); ?></div>
                        <?php if (isset($activity['stats'])): ?>
                            <div class="activity-stats"><?php echo $activity['stats']; ?></div>
                        <?php endif; ?>
                        <?php if (isset($activity['class'])): ?>
                            <div class="activity-class"><?php echo htmlspecialchars($activity['class']); ?></div>
                        <?php endif; ?>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
        </div>

        <!-- Adventure Tiers Statistics -->
        <div class="adventure-tiers">
            <h3><i class="fas fa-map"></i> Active Adventures</h3>
            <div class="tier-grid">
                <div class="tier-card">
                    <div class="tier-icon">⚡</div>
                    <div class="tier-name">Short</div>
                    <div class="tier-count"><?php echo number_format($adventure_tier_stats['short_est']); ?></div>
                    <div class="tier-duration">5min - 1hr</div>
                </div>
                <div class="tier-card">
                    <div class="tier-icon">🗡️</div>
                    <div class="tier-name">Medium</div>
                    <div class="tier-count"><?php echo number_format($adventure_tier_stats['medium_est']); ?></div>
                    <div class="tier-duration">45min - 3hr</div>
                </div>
                <div class="tier-card">
                    <div class="tier-icon">🏰</div>
                    <div class="tier-name">Long</div>
                    <div class="tier-count"><?php echo number_format($adventure_tier_stats['long_est']); ?></div>
                    <div class="tier-duration">2hr - 8hr</div>
                </div>
                <div class="tier-card">
                    <div class="tier-icon">🌟</div>
                    <div class="tier-name">Epic</div>
                    <div class="tier-count"><?php echo number_format($adventure_tier_stats['epic_est']); ?></div>
                    <div class="tier-duration">4-8 hours (Lvl 10+)</div>
                </div>
                <div class="tier-card">
                    <div class="tier-icon">⚡</div>
                    <div class="tier-name">Legendary</div>
                    <div class="tier-count"><?php echo number_format($adventure_tier_stats['legendary_est']); ?></div>
                    <div class="tier-duration">8-24 hours (Lvl 15+)</div>
                </div>
            </div>
        </div>

        <!-- Enhanced Distribution Stats -->
        <div class="distribution-stats">
            <div class="distribution-section">
                <h3><i class="fas fa-chart-bar"></i> Class Distribution</h3>
                <div class="class-distribution">
                    <?php foreach ($class_stats as $class_stat): ?>
                    <div class="class-item">
                        <div class="class-count"><?php echo $class_stat['count']; ?></div>
                        <div><?php echo htmlspecialchars($class_stat['class']); ?></div>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>
            
            <div class="distribution-section">
                <h3><i class="fas fa-dna"></i> Race Distribution</h3>
                <div class="race-distribution">
                    <?php foreach ($race_stats as $race_stat): ?>
                    <div class="race-item">
                        <div class="race-count"><?php echo $race_stat['count']; ?></div>
                        <div><?php echo htmlspecialchars($race_stat['race']); ?></div>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>
        </div>


        <!-- Refresh Section -->
        <div class="refresh-section">
            <a href="javascript:location.reload()" class="refresh-btn">
                <i class="fas fa-sync-alt refresh-icon"></i>
                Refresh Leaderboards
            </a>
            <p style="margin-top: 15px; opacity: 0.7;">
                <i class="fas fa-info-circle"></i>
                Leaderboards update automatically as players progress in the game
            </p>
        </div>
    </div>

    <script>
        // Add some interactive effects
        document.addEventListener('DOMContentLoaded', function() {
            // Stagger animation for player cards
            const players = document.querySelectorAll('.player');
            players.forEach((player, index) => {
                player.style.opacity = '0';
                player.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    player.style.transition = 'all 0.5s ease';
                    player.style.opacity = '1';
                    player.style.transform = 'translateY(0)';
                }, index * 50);
            });

            // Auto-refresh every 5 minutes
            setInterval(() => {
                location.reload();
            }, 300000);

            // Add loading state for refresh
            document.querySelector('.refresh-btn').addEventListener('click', function(e) {
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            });
        });
    </script>
</body>
</html>