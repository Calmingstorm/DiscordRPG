<?php
/**
 * DiscordRPG Top Items Leaderboard
 * Shows top 10 items for each equipment slot
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

// Function to get top items by slot type
function getTopItems($pdo, $slot_type, $sort_by = 'damage', $limit = 10) {
    try {
        $sql = "
            SELECT i.name, i.type, i.damage, i.armor, i.value, i.health_bonus, 
                   i.speed_bonus, i.luck_bonus, i.crit_bonus, i.magic_bonus,
                   p.name as owner_name
            FROM inventory i 
            JOIN profile p ON i.owner = p.user_id 
            WHERE i.slot_type = :slot_type
            ORDER BY i.$sort_by DESC 
            LIMIT :limit
        ";
        
        $stmt = $pdo->prepare($sql);
        $stmt->bindParam(':slot_type', $slot_type);
        $stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
        $stmt->execute();
        
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    } catch (Exception $e) {
        return [];
    }
}

// Function to get top weapons (highest damage + armor combined)
function getTopWeapons($pdo, $limit = 10) {
    try {
        $sql = "
            SELECT i.name, i.type, i.damage, i.armor, i.value,
                   p.name as owner_name, (i.damage + i.armor) as total_power
            FROM inventory i 
            JOIN profile p ON i.owner = p.user_id 
            WHERE i.slot_type = 'weapon'
            ORDER BY (i.damage + i.armor) DESC 
            LIMIT :limit
        ";
        
        $stmt = $pdo->prepare($sql);
        $stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
        $stmt->execute();
        
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    } catch (Exception $e) {
        return [];
    }
}

// Function to format bonus stats
function formatBonuses($item) {
    $bonuses = [];
    if ($item['health_bonus'] > 0) $bonuses[] = "+{$item['health_bonus']}❤️";
    if ($item['speed_bonus'] > 0) $bonuses[] = "+{$item['speed_bonus']}💨";
    if ($item['luck_bonus'] > 0) $bonuses[] = "+" . number_format($item['luck_bonus'], 2) . "🍀";
    if ($item['crit_bonus'] > 0) $bonuses[] = "+" . number_format($item['crit_bonus'] * 100, 1) . "%💥";
    if ($item['magic_bonus'] > 0) $bonuses[] = "+{$item['magic_bonus']}✨";
    
    return $bonuses ? " • " . implode(' ', $bonuses) : "";
}

// Get data for each slot
$top_weapons = getTopWeapons($pdo);
$top_shields = getTopItems($pdo, 'shield', 'armor');
$top_helmets = getTopItems($pdo, 'head', 'armor');
$top_chestplates = getTopItems($pdo, 'chest', 'armor');
$top_leggings = getTopItems($pdo, 'legs', 'armor');
$top_gauntlets = getTopItems($pdo, 'hands', 'armor');
$top_boots = getTopItems($pdo, 'feet', 'armor');

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DiscordRPG - Top Items</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f0f23;
            --bg-card: #1a1a2e;
            --bg-secondary: #16213e;
            --text-primary: #ffffff;
            --text-secondary: #a3a3a3;
            --text-accent: #22c55e;
            --border: #334155;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --warning: #f59e0b;
            --danger: #ef4444;
            --gradient: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: var(--gradient);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            text-align: center;
        }

        .header h1 {
            font-family: 'Orbitron', monospace;
            font-size: 2.5rem;
            font-weight: 900;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #3b82f6, #22c55e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .nav-links {
            margin-top: 20px;
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .nav-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: var(--accent);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .nav-btn:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
        }

        .items-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }

        .slot-card {
            background: var(--gradient);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 25px;
        }

        .slot-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border);
        }

        .slot-icon {
            font-size: 1.5rem;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--accent);
            border-radius: 10px;
        }

        .slot-title {
            font-family: 'Orbitron', monospace;
            font-size: 1.2rem;
            font-weight: 700;
        }

        .item-list {
            list-style: none;
        }

        .item-entry {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            margin: 8px 0;
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 8px;
            transition: all 0.3s ease;
        }

        .item-entry:hover {
            background: rgba(59, 130, 246, 0.15);
            border-color: rgba(59, 130, 246, 0.3);
        }

        .item-info {
            flex: 1;
        }

        .item-name {
            font-weight: 600;
            color: var(--text-accent);
            margin-bottom: 4px;
        }

        .item-stats {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .item-owner {
            text-align: right;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .rank-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            background: var(--accent);
            color: white;
            border-radius: 50%;
            font-size: 0.75rem;
            font-weight: 700;
            margin-right: 10px;
        }

        .rank-1 { background: #ffd700; color: #000; }
        .rank-2 { background: #c0c0c0; color: #000; }
        .rank-3 { background: #cd7f32; color: #fff; }

        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .items-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1><i class="fas fa-trophy"></i> Top Items Leaderboard</h1>
            <p style="margin-top: 10px; color: var(--text-secondary);">Legendary equipment and their owners</p>
            
            <div class="nav-links">
                <a href="index.php" class="nav-btn">
                    <i class="fas fa-home"></i>
                    Home
                </a>
                <a href="guide.php" class="nav-btn">
                    <i class="fas fa-scroll"></i>
                    Guide
                </a>
                <a href="javascript:location.reload()" class="nav-btn">
                    <i class="fas fa-sync-alt"></i>
                    Refresh
                </a>
            </div>
        </div>

        <!-- Items Grid -->
        <div class="items-grid">
            <!-- Weapons -->
            <div class="slot-card">
                <div class="slot-header">
                    <div class="slot-icon"><i class="fas fa-sword"></i></div>
                    <h3 class="slot-title">Top Weapons</h3>
                </div>
                <ul class="item-list">
                    <?php foreach ($top_weapons as $index => $item): ?>
                        <li class="item-entry">
                            <span class="rank-badge rank-<?php echo min($index + 1, 3); ?>"><?php echo $index + 1; ?></span>
                            <div class="item-info">
                                <div class="item-name"><?php echo htmlspecialchars($item['name']); ?></div>
                                <div class="item-stats">
                                    <?php echo $item['damage']; ?>⚔️ <?php echo $item['armor']; ?>🛡️ 
                                    • Total: <?php echo $item['total_power']; ?> 
                                    • 💰<?php echo abbreviate_number($item['value']); ?>
                                </div>
                            </div>
                            <div class="item-owner">
                                <i class="fas fa-user"></i>
                                <?php echo htmlspecialchars($item['owner_name']); ?>
                            </div>
                        </li>
                    <?php endforeach; ?>
                </ul>
            </div>

            <!-- Shields -->
            <div class="slot-card">
                <div class="slot-header">
                    <div class="slot-icon"><i class="fas fa-shield-alt"></i></div>
                    <h3 class="slot-title">Top Shields</h3>
                </div>
                <ul class="item-list">
                    <?php foreach ($top_shields as $index => $item): ?>
                        <li class="item-entry">
                            <span class="rank-badge rank-<?php echo min($index + 1, 3); ?>"><?php echo $index + 1; ?></span>
                            <div class="item-info">
                                <div class="item-name"><?php echo htmlspecialchars($item['name']); ?></div>
                                <div class="item-stats">
                                    <?php echo $item['damage']; ?>⚔️ <?php echo $item['armor']; ?>🛡️
                                    <?php echo formatBonuses($item); ?>
                                    • 💰<?php echo abbreviate_number($item['value']); ?>
                                </div>
                            </div>
                            <div class="item-owner">
                                <i class="fas fa-user"></i>
                                <?php echo htmlspecialchars($item['owner_name']); ?>
                            </div>
                        </li>
                    <?php endforeach; ?>
                </ul>
            </div>

            <!-- Helmets -->
            <div class="slot-card">
                <div class="slot-header">
                    <div class="slot-icon"><i class="fas fa-hat-wizard"></i></div>
                    <h3 class="slot-title">Top Helmets</h3>
                </div>
                <ul class="item-list">
                    <?php foreach ($top_helmets as $index => $item): ?>
                        <li class="item-entry">
                            <span class="rank-badge rank-<?php echo min($index + 1, 3); ?>"><?php echo $index + 1; ?></span>
                            <div class="item-info">
                                <div class="item-name"><?php echo htmlspecialchars($item['name']); ?></div>
                                <div class="item-stats">
                                    <?php echo $item['armor']; ?>🛡️
                                    <?php echo formatBonuses($item); ?>
                                    • 💰<?php echo abbreviate_number($item['value']); ?>
                                </div>
                            </div>
                            <div class="item-owner">
                                <i class="fas fa-user"></i>
                                <?php echo htmlspecialchars($item['owner_name']); ?>
                            </div>
                        </li>
                    <?php endforeach; ?>
                </ul>
            </div>

            <!-- Chestplates -->
            <div class="slot-card">
                <div class="slot-header">
                    <div class="slot-icon"><i class="fas fa-vest"></i></div>
                    <h3 class="slot-title">Top Chestplates</h3>
                </div>
                <ul class="item-list">
                    <?php foreach ($top_chestplates as $index => $item): ?>
                        <li class="item-entry">
                            <span class="rank-badge rank-<?php echo min($index + 1, 3); ?>"><?php echo $index + 1; ?></span>
                            <div class="item-info">
                                <div class="item-name"><?php echo htmlspecialchars($item['name']); ?></div>
                                <div class="item-stats">
                                    <?php echo $item['armor']; ?>🛡️
                                    <?php echo formatBonuses($item); ?>
                                    • 💰<?php echo abbreviate_number($item['value']); ?>
                                </div>
                            </div>
                            <div class="item-owner">
                                <i class="fas fa-user"></i>
                                <?php echo htmlspecialchars($item['owner_name']); ?>
                            </div>
                        </li>
                    <?php endforeach; ?>
                </ul>
            </div>

            <!-- Leggings -->
            <div class="slot-card">
                <div class="slot-header">
                    <div class="slot-icon"><i class="fas fa-socks"></i></div>
                    <h3 class="slot-title">Top Leggings</h3>
                </div>
                <ul class="item-list">
                    <?php foreach ($top_leggings as $index => $item): ?>
                        <li class="item-entry">
                            <span class="rank-badge rank-<?php echo min($index + 1, 3); ?>"><?php echo $index + 1; ?></span>
                            <div class="item-info">
                                <div class="item-name"><?php echo htmlspecialchars($item['name']); ?></div>
                                <div class="item-stats">
                                    <?php echo $item['armor']; ?>🛡️
                                    <?php echo formatBonuses($item); ?>
                                    • 💰<?php echo abbreviate_number($item['value']); ?>
                                </div>
                            </div>
                            <div class="item-owner">
                                <i class="fas fa-user"></i>
                                <?php echo htmlspecialchars($item['owner_name']); ?>
                            </div>
                        </li>
                    <?php endforeach; ?>
                </ul>
            </div>

            <!-- Gauntlets -->
            <div class="slot-card">
                <div class="slot-header">
                    <div class="slot-icon"><i class="fas fa-mitten"></i></div>
                    <h3 class="slot-title">Top Gauntlets</h3>
                </div>
                <ul class="item-list">
                    <?php foreach ($top_gauntlets as $index => $item): ?>
                        <li class="item-entry">
                            <span class="rank-badge rank-<?php echo min($index + 1, 3); ?>"><?php echo $index + 1; ?></span>
                            <div class="item-info">
                                <div class="item-name"><?php echo htmlspecialchars($item['name']); ?></div>
                                <div class="item-stats">
                                    <?php echo $item['armor']; ?>🛡️
                                    <?php echo formatBonuses($item); ?>
                                    • 💰<?php echo abbreviate_number($item['value']); ?>
                                </div>
                            </div>
                            <div class="item-owner">
                                <i class="fas fa-user"></i>
                                <?php echo htmlspecialchars($item['owner_name']); ?>
                            </div>
                        </li>
                    <?php endforeach; ?>
                </ul>
            </div>

            <!-- Boots -->
            <div class="slot-card">
                <div class="slot-header">
                    <div class="slot-icon"><i class="fas fa-shoe-prints"></i></div>
                    <h3 class="slot-title">Top Boots</h3>
                </div>
                <ul class="item-list">
                    <?php foreach ($top_boots as $index => $item): ?>
                        <li class="item-entry">
                            <span class="rank-badge rank-<?php echo min($index + 1, 3); ?>"><?php echo $index + 1; ?></span>
                            <div class="item-info">
                                <div class="item-name"><?php echo htmlspecialchars($item['name']); ?></div>
                                <div class="item-stats">
                                    <?php echo $item['armor']; ?>🛡️
                                    <?php echo formatBonuses($item); ?>
                                    • 💰<?php echo abbreviate_number($item['value']); ?>
                                </div>
                            </div>
                            <div class="item-owner">
                                <i class="fas fa-user"></i>
                                <?php echo htmlspecialchars($item['owner_name']); ?>
                            </div>
                        </li>
                    <?php endforeach; ?>
                </ul>
            </div>
        </div>

        <!-- Footer -->
        <div style="text-align: center; padding: 20px; color: var(--text-secondary); border-top: 1px solid var(--border); margin-top: 30px;">
            <p><i class="fas fa-clock"></i> Last updated: <?php echo date('M j, Y • g:i A'); ?></p>
            <p style="margin-top: 10px;">🔮 DiscordRPG Web Portal • <a href="index.php" style="color: var(--text-accent);">View Leaderboards</a></p>
        </div>
    </div>
</body>
</html>