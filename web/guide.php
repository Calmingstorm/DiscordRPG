<?php 
// Set timezone to EST
date_default_timezone_set('America/New_York');

// Prevent caching
header("Cache-Control: no-cache, no-store, must-revalidate"); 
header("Pragma: no-cache"); 
header("Expires: 0"); 
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DiscordRPG - Complete Game Guide</title>
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
            --sidebar-width: 280px;
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

        .wrapper {
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background: var(--secondary-bg);
            border-right: 1px solid var(--border-subtle);
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            z-index: 100;
            transition: transform 0.3s ease;
        }

        .sidebar.hidden {
            transform: translateX(-100%);
        }

        .sidebar-header {
            padding: 24px;
            border-bottom: 1px solid var(--border-subtle);
            background: var(--accent-bg);
        }

        .sidebar-header h2 {
            font-family: 'Orbitron', monospace;
            font-size: 1.4em;
            font-weight: 700;
            color: var(--text-accent);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .back-link {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.9em;
            transition: color 0.2s ease;
        }

        .back-link:hover {
            color: var(--text-accent);
            text-decoration: none;
        }

        .sidebar-nav {
            padding: 16px 0;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 24px;
            color: var(--text-primary);
            text-decoration: none;
            transition: all 0.2s ease;
            cursor: pointer;
            border: none;
            background: none;
            width: 100%;
            text-align: left;
            font-size: 0.95em;
            font-weight: 500;
            margin: 1px 0;
        }

        .nav-item:hover {
            background: var(--hover-bg);
            color: var(--text-accent);
            border-left: 4px solid var(--text-accent);
            padding-left: 20px;
            text-decoration: none;
        }

        .nav-item.active {
            background: var(--hover-bg);
            color: var(--text-accent);
            border-left: 4px solid var(--text-accent);
            padding-left: 20px;
            font-weight: 600;
        }

        .nav-item i {
            font-size: 1.1em;
            width: 18px;
            text-align: center;
        }

        /* Main Content */
        .content {
            margin-left: var(--sidebar-width);
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 32px;
            min-height: 100vh;
            width: calc(100vw - var(--sidebar-width));
        }

        .content-wrapper {
            width: 100%;
            max-width: 1000px;
            margin: 0 auto;
        }

        .content-header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border-subtle);
        }

        .content-header h1 {
            font-family: 'Orbitron', monospace;
            font-size: 2.5em;
            font-weight: 700;
            color: var(--text-accent);
            margin-bottom: 12px;
            letter-spacing: 1px;
        }

        .guide-intro {
            font-size: 1.1em;
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto;
        }

        /* Content Sections */
        .section {
            display: none;
            animation: fadeIn 0.3s ease-in-out;
        }

        .section.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .section h2 {
            font-family: 'Orbitron', monospace;
            font-size: 2em;
            font-weight: 600;
            color: var(--text-accent);
            margin-bottom: 24px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--border-accent);
        }

        .section h3 {
            font-family: 'Orbitron', monospace;
            color: var(--text-accent);
            font-size: 1.3em;
            margin: 24px 0 16px 0;
            font-weight: 600;
        }

        /* Mobile Menu Toggle */
        .mobile-menu-toggle {
            display: none;
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 101;
            background: var(--secondary-bg);
            border: 1px solid var(--border-subtle);
            padding: 12px;
            border-radius: 6px;
            cursor: pointer;
            color: var(--text-accent);
            font-size: 1.2em;
        }

        .mobile-menu-toggle:hover {
            background: var(--hover-bg);
        }

        /* Utility Classes */
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin: 24px 0;
        }

        .feature-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 28px;
            transition: all 0.2s ease;
        }

        .feature-card:hover {
            border-color: var(--border-accent);
            box-shadow: var(--shadow-medium);
        }

        .feature-icon {
            font-size: 2.2em;
            color: var(--text-accent);
            margin-bottom: 12px;
            text-align: center;
        }

        .feature-title {
            font-family: 'Orbitron', monospace;
            color: var(--text-accent);
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 12px;
            text-align: center;
        }

        .feature-description {
            color: var(--text-secondary);
            line-height: 1.6;
            font-size: 0.95em;
        }

        .command-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin: 24px 0;
        }

        .command-category {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 28px;
            transition: all 0.2s ease;
        }

        .command-category:hover {
            border-color: var(--border-accent);
            box-shadow: var(--shadow-soft);
        }

        .command-category-title {
            font-family: 'Orbitron', monospace;
            color: var(--text-accent);
            font-size: 1.3em;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .command-list {
            list-style: none;
            padding: 0;
        }

        .command-list li {
            margin-bottom: 8px;
            padding: 8px 12px;
            background: rgba(212, 175, 55, 0.08);
            border-radius: 6px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 0.9em;
        }

        .command-name {
            color: var(--text-accent);
            font-weight: 600;
        }

        .stats-table {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            overflow: hidden;
            margin: 24px 0;
        }

        .stats-table table {
            width: 100%;
            border-collapse: collapse;
        }

        .stats-table th {
            background: var(--accent-bg);
            padding: 16px;
            color: var(--text-accent);
            font-family: 'Orbitron', monospace;
            font-weight: 600;
            font-size: 0.95em;
        }

        .stats-table td {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-subtle);
            color: var(--text-primary);
        }

        .stats-table tr:hover td {
            background: var(--hover-bg);
        }

        .info-box {
            background: var(--accent-bg);
            border: 1px solid var(--border-accent);
            border-radius: 8px;
            padding: 24px;
            margin: 24px 0;
            line-height: 1.6;
        }

        .info-box h3 {
            margin-top: 0;
            margin-bottom: 16px;
            color: var(--text-accent);
            font-family: 'Orbitron', monospace;
            font-size: 1.2em;
        }

        .info-box p {
            margin-bottom: 12px;
            color: var(--text-primary);
        }

        .info-box p:last-child {
            margin-bottom: 0;
        }

        .info-box ol, .info-box ul {
            margin: 16px 0;
            padding-left: 24px;
        }

        .info-box li {
            margin-bottom: 8px;
            color: var(--text-primary);
        }

        .warning-box {
            background: rgba(255, 165, 0, 0.1);
            border: 1px solid rgba(255, 165, 0, 0.3);
            border-radius: 8px;
            padding: 24px;
            margin: 24px 0;
            line-height: 1.6;
        }

        .warning-box h3 {
            margin-top: 0;
            margin-bottom: 16px;
            color: #ffa500;
            font-family: 'Orbitron', monospace;
            font-size: 1.2em;
        }

        .warning-box p {
            margin-bottom: 12px;
            color: var(--text-primary);
        }

        .warning-box p:last-child {
            margin-bottom: 0;
        }

        .success-box {
            background: rgba(34, 139, 34, 0.1);
            border: 1px solid rgba(34, 139, 34, 0.3);
            border-radius: 8px;
            padding: 24px;
            margin: 24px 0;
            line-height: 1.6;
        }

        .success-box h3 {
            margin-top: 0;
            margin-bottom: 16px;
            color: #22c55e;
            font-family: 'Orbitron', monospace;
            font-size: 1.2em;
        }

        .success-box p {
            margin-bottom: 12px;
            color: var(--text-primary);
        }

        .success-box p:last-child {
            margin-bottom: 0;
        }

        .class-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin: 24px 0;
        }

        .class-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 28px;
            transition: all 0.2s ease;
        }

        .class-card:hover {
            border-color: var(--border-accent);
            box-shadow: var(--shadow-medium);
        }

        .class-header {
            display: flex;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-subtle);
        }

        .class-icon {
            font-size: 1.8em;
            margin-right: 12px;
            color: var(--text-accent);
        }

        .class-name {
            font-family: 'Orbitron', monospace;
            font-size: 1.2em;
            font-weight: 600;
            color: var(--text-accent);
        }

        .class-description {
            color: var(--text-secondary);
            margin-bottom: 16px;
            line-height: 1.5;
        }

        .bonus-list {
            list-style: none;
            padding: 0;
        }

        .bonus-list li {
            margin-bottom: 6px;
            padding-left: 16px;
            position: relative;
            color: var(--text-primary);
        }

        .bonus-list li::before {
            content: "•";
            position: absolute;
            left: 0;
            color: var(--text-accent);
            font-weight: bold;
        }

        /* Responsive Design */
        @media (max-width: 1024px) {
            .sidebar {
                transform: translateX(-100%);
            }

            .sidebar.active {
                transform: translateX(0);
            }

            .mobile-menu-toggle {
                display: block;
            }

            .content {
                margin-left: 0;
                padding: 80px 20px 20px 20px;
                width: 100vw;
            }

            .content-wrapper {
                max-width: 100%;
            }
        }

        @media (max-width: 768px) {
            .content-header h1 { font-size: 2em; }
            .feature-grid { grid-template-columns: 1fr; }
            .command-grid { grid-template-columns: 1fr; }
            .class-grid { grid-template-columns: 1fr; }
        }

        @media (max-width: 480px) {
            .content { padding: 80px 15px 15px 15px; }
            .feature-card { padding: 24px; }
            .class-card { padding: 24px; }
            .command-category { padding: 24px; }
            .info-box { padding: 20px; }
            .warning-box { padding: 20px; }
            .success-box { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="wrapper">
        <!-- Mobile Menu Toggle -->
        <button class="mobile-menu-toggle" onclick="toggleSidebar()">
            <i class="fas fa-bars"></i>
        </button>

        <!-- Fixed Sidebar Navigation -->
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h2><i class="fas fa-scroll"></i> DiscordRPG Guide</h2>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <a href="index.php" class="back-link">
                        <i class="fas fa-arrow-left"></i> Back to Leaderboards
                    </a>
                    <a href="top-items.php" class="back-link">
                        <i class="fas fa-trophy"></i> View Top Items
                    </a>
                </div>
            </div>
            <nav class="sidebar-nav">
                <a href="#getting-started" class="nav-item active" data-section="getting-started">
                    <i class="fas fa-play-circle"></i> Getting Started
                </a>
                <a href="#commands" class="nav-item" data-section="commands">
                    <i class="fas fa-terminal"></i> Commands
                </a>
                <a href="#classes" class="nav-item" data-section="classes">
                    <i class="fas fa-shield-alt"></i> Classes
                </a>
                <a href="#races" class="nav-item" data-section="races">
                    <i class="fas fa-dna"></i> Races
                </a>
                <a href="#auto-play" class="nav-item" data-section="auto-play">
                    <i class="fas fa-robot"></i> Auto-Play
                </a>
                <a href="#battles" class="nav-item" data-section="battles">
                    <i class="fas fa-fist-raised"></i> Battle System
                </a>
                <a href="#economy" class="nav-item" data-section="economy">
                    <i class="fas fa-coins"></i> Economy
                </a>
                <a href="#religion" class="nav-item" data-section="religion">
                    <i class="fas fa-praying-hands"></i> Religion
                </a>
                <a href="#gambling" class="nav-item" data-section="gambling">
                    <i class="fas fa-dice"></i> Gambling
                </a>
                <a href="#raids" class="nav-item" data-section="raids">
                    <i class="fas fa-dragon"></i> Raids
                </a>
                <a href="#equipment" class="nav-item" data-section="equipment">
                    <i class="fas fa-cog"></i> Equipment & Armor
                </a>
                <a href="#progression" class="nav-item" data-section="progression">
                    <i class="fas fa-chart-line"></i> Progression
                </a>
                <a href="#faq" class="nav-item" data-section="faq">
                    <i class="fas fa-question-circle"></i> FAQ
                </a>
            </nav>
        </aside>

        <!-- Main Content Area -->
        <main class="content">
            <div class="content-wrapper">
                <div class="content-header">
                    <h1><i class="fas fa-dragon"></i> DiscordRPG Documentation</h1>
                    <div class="guide-intro">
                        Complete guide to mastering the DiscordRPG universe. Navigate using the sidebar to explore different aspects of the game.
                    </div>
                </div>

            <!-- Getting Started Section -->
            <section id="getting-started" class="section active">
                <h2>🚀 Getting Started</h2>
                <p>Welcome to DiscordRPG! This automated RPG runs in the background while you chat in Discord.</p>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">👤</div>
                        <div class="feature-title">Create Character</div>
                        <div class="feature-description">
                            Use <code>!create [name]</code> to join the game. Your character starts as a Novice with basic equipment and 100 gold.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🟢</div>
                        <div class="feature-title">Stay Online</div>
                        <div class="feature-description">
                            Keep your Discord status as <strong>Online (Green)</strong> to participate in automatic adventures, battles, and raids.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📊</div>
                        <div class="feature-title">Check Progress</div>
                        <div class="feature-description">
                            Use <code>!profile</code> to view your stats, equipment, and progress. Track your XP, level, and class evolution.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🌟</div>
                        <div class="feature-title">Evolve Classes</div>
                        <div class="feature-description">
                            At level 5, use <code>!evolve</code> to choose your first class specialization and unlock powerful bonuses.
                        </div>
                    </div>
                </div>

                <div class="info-box">
                    <h3>Quick Start Tips</h3>
                    <ol>
                        <li>Create your character with <code>!create YourName</code></li>
                        <li>Set your Discord status to Online (green circle)</li>
                        <li>Wait for automatic adventures and battles</li>
                        <li>Check progress with <code>!profile</code></li>
                        <li>Evolve at level 5 with <code>!evolve</code></li>
                    </ol>
                </div>

                <div class="warning-box">
                    <h3>Important Requirements</h3>
                    <p><strong>Online Status Required:</strong> You must have Discord status set to "Online" (green) to participate in automatic gameplay. Away, DND, or Invisible status will prevent progression.</p>
                </div>
            </section>

            <!-- Commands Section -->
            <section id="commands" class="section">
                <h2>💬 Commands</h2>
                <p>Complete reference for all available bot commands.</p>
                
                <div class="command-grid">
                    <div class="command-category">
                        <div class="command-category-title">
                            <i class="fas fa-user"></i>
                            Character
                        </div>
                        <ul class="command-list">
                            <li><span class="command-name">!create [name]</span> - Join the game</li>
                            <li><span class="command-name">!profile [@user]</span> - View character stats</li>
                            <li><span class="command-name">!classes</span> - View 8-tier class evolution tree</li>
                            <li><span class="command-name">!classbonuses [class]</span> - Show class benefits</li>
                            <li><span class="command-name">!evolve</span> - Evolve class (levels: 5, 10, 15, 20, 25, 30, 50, 100)</li>
                            <li><span class="command-name">!races</span> - View available races</li>
                            <li><span class="command-name">!race &lt;name&gt;</span> - Select race (permanent!)</li>
                            <li><span class="command-name">!align &lt;good/neutral/evil&gt;</span> - Set alignment</li>
                            <li><span class="command-name">!removeme</span> - Delete character</li>
                        </ul>
                    </div>
                    
                    <div class="command-category">
                        <div class="command-category-title">
                            <i class="fas fa-sword"></i>
                            Equipment
                        </div>
                        <ul class="command-list">
                            <li><span class="command-name">!inventory</span> - View your items & crates</li>
                            <li><span class="command-name">!equipment</span> - View equipped gear & armor bonuses</li>
                            <li><span class="command-name">!equip &lt;id&gt;</span> - Equip an item (weapons or armor)</li>
                            <li><span class="command-name">!unequip &lt;id&gt;</span> - Remove equipped items</li>
                            <li><span class="command-name">!item &lt;id&gt;</span> - View detailed item stats</li>
                            <li><span class="command-name">!sell &lt;id&gt;</span> - Sell item to merchant</li>
                            <li><span class="command-name">!give &lt;user&gt; &lt;id&gt;</span> - Give item to player</li>
                            <li><span class="command-name">!crate &lt;type&gt;</span> - Open a crate</li>
                        </ul>
                    </div>
                    
                    <div class="command-category">
                        <div class="command-category-title">
                            <i class="fas fa-coins"></i>
                            Economy
                        </div>
                        <ul class="command-list">
                            <li><span class="command-name">!market</span> - Browse marketplace</li>
                            <li><span class="command-name">!buy &lt;id&gt;</span> - Purchase item</li>
                            <li><span class="command-name">!offer &lt;id&gt; &lt;price&gt;</span> - List item for sale</li>
                            <li><span class="command-name">!daily</span> - Daily login rewards</li>
                        </ul>
                    </div>
                    
                    <div class="command-category">
                        <div class="command-category-title">
                            <i class="fas fa-dice"></i>
                            Gambling
                        </div>
                        <ul class="command-list">
                            <li><span class="command-name">!gamble &lt;amount&gt;</span> - 40% chance double money</li>
                            <li><span class="command-name">!coinflip &lt;amount&gt; &lt;h/t&gt;</span> - 50/50 coin toss</li>
                            <li><span class="command-name">!slots &lt;amount&gt;</span> - Slot machine game</li>
                            <li><span class="command-name">!blackjack &lt;amount&gt;</span> - Play blackjack</li>
                            <li><span class="command-name">!diceroll &lt;amount&gt;</span> - Roll vs house</li>
                        </ul>
                    </div>
                    
                    <div class="command-category">
                        <div class="command-category-title">
                            <i class="fas fa-praying-hands"></i>
                            Religion
                        </div>
                        <ul class="command-list">
                            <li><span class="command-name">!gods</span> - View available deities</li>
                            <li><span class="command-name">!choose &lt;god&gt;</span> - Pick deity (permanent!)</li>
                            <li><span class="command-name">!pray</span> - Gain favor (4hr cooldown)</li>
                            <li><span class="command-name">!sacrifice &lt;gold&gt;</span> - Offer gold for favor (12hr cd)</li>
                            <li><span class="command-name">!bless [type]</span> - Spend favor on divine blessings</li>
                        </ul>
                    </div>
                    
                    <div class="command-category">
                        <div class="command-category-title">
                            <i class="fas fa-fist-raised"></i>
                            Combat
                        </div>
                        <ul class="command-list">
                            <li><span class="command-name">!battle &lt;@user&gt;</span> - Challenge player</li>
                            <li><span class="command-name">!battles</span> - Battle system guide</li>
                            <li><span class="command-name">!battlestatus</span> - Check battle system</li>
                            <li><span class="command-name">!tournament &lt;prize&gt;</span> - Host tournament</li>
                            <li><span class="command-name">!online</span> - See online players</li>
                        </ul>
                    </div>
                    
                    <div class="command-category">
                        <div class="command-category-title">
                            <i class="fas fa-castle"></i>
                            Raids
                        </div>
                        <ul class="command-list">
                            <li><span class="command-name">!raids</span> - Raid system info</li>
                            <li><span class="command-name">!raidstatus</span> - Check active raids</li>
                        </ul>
                    </div>
                    
                    <div class="command-category">
                        <div class="command-category-title">
                            <i class="fas fa-cog"></i>
                            System
                        </div>
                        <ul class="command-list">
                            <li><span class="command-name">!autoplay status</span> - Check auto-game</li>
                            <li><span class="command-name">!status</span> - Check adventure status</li>
                            <li><span class="command-name">!help [command]</span> - Command details</li>
                            <li><span class="command-name">!ping</span> - Check bot latency</li>
                        </ul>
                    </div>
                </div>
            </section>

            <!-- Classes Section -->
            <section id="classes" class="section">
                <h2>🛡️ Classes</h2>
                <p>Character classes evolve through 8 tiers, unlocking powerful bonuses and abilities. The new class system provides specialized endgame paths!</p>
                
                <div class="info-box">
                    <h3>Evolution Tiers - UPDATED SYSTEM</h3>
                    <p>Classes now evolve through 8 tiers, providing diverse endgame specializations:</p>
                    <p><strong>Tier 1:</strong> Level 5+ (Basic Classes) • <strong>Tier 2:</strong> Level 10+ (Advanced)</p>
                    <p><strong>Tier 3:</strong> Level 15+ (Elite) • <strong>Tier 4:</strong> Level 20+ (Master + Special)</p>
                    <p><strong>Tier 5:</strong> Level 25+ (Advanced Specialization) • <strong>Tier 6:</strong> Level 30+ (Master Specialization)</p>
                    <p><strong>Tier 7:</strong> Level 50+ (Elite Mastery) • <strong>Tier 8:</strong> Level 100+ (Universal Sovereign)</p>
                </div>
                
                <div class="info-box">
                    <h3>🚀 Clean Evolution System - OVERVIEW</h3>
                    
                    <h4 style="color: var(--text-accent); margin: 16px 0 8px 0;">!evolve - Class Evolution</h4>
                    <p><strong>Function:</strong> Evolve your class when you reach the required level</p>
                    <p><strong>Usage:</strong> <code>!evolve</code> - Shows available evolution options</p>
                    <p><strong>Levels:</strong> Evolution available at levels 5, 10, 15, 20, 25, 30, 50, 100</p>
                    <p><strong>Clean progression:</strong> Each class maintains its unique identity throughout all tiers</p>
                    
                    <p><strong>🎯 System:</strong> Clean 8-tier evolution system with no forced convergence points, allowing each class path to maintain its distinct identity all the way to Universal Sovereign.</p>
                </div>
                

                <div class="class-grid">
                    <div class="class-card">
                        <div class="class-header">
                            <div class="class-icon">🛡️</div>
                            <div>
                                <div class="class-name">WARRIOR LINE</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">Tank/Defense Specialist</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Masters of defense and protection, Warriors excel at absorbing damage and holding the front line.
                        </div>
                        <h3 style="color: var(--text-accent); margin: 16px 0 8px 0; font-size: 1em;">Base Bonuses (per tier):</h3>
                        <ul class="bonus-list">
                            <li><strong>+10% Defense</strong> per tier</li>
                            <li><strong>+5% Attack</strong> per tier</li>
                        </ul>
                        <h3 style="color: var(--text-highlight); margin: 16px 0 8px 0; font-size: 1em;">Special Abilities:</h3>
                        <ul class="bonus-list">
                            <li><strong>Berserker:</strong> +20% Attack, 15% Lifesteal</li>
                            <li><strong>Paladin:</strong> +20% Defense, +10% Magic</li>
                        </ul>
                    </div>

                    <div class="class-card">
                        <div class="class-header">
                            <div class="class-icon">🗡️</div>
                            <div>
                                <div class="class-name">THIEF LINE</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">DPS with Utility</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Swift and deadly, Thieves specialize in critical strikes and stealing from enemies.
                        </div>
                        <h3 style="color: var(--text-accent); margin: 16px 0 8px 0; font-size: 1em;">Base Bonuses (per tier):</h3>
                        <ul class="bonus-list">
                            <li><strong>+8% Steal Chance</strong> per tier</li>
                            <li><strong>+5% Crit Chance</strong> per tier</li>
                            <li><strong>+3% Dodge Chance</strong> per tier</li>
                            <li><strong>+10% Speed</strong> per tier</li>
                        </ul>
                        <h3 style="color: var(--text-highlight); margin: 16px 0 8px 0; font-size: 1em;">Special Abilities:</h3>
                        <ul class="bonus-list">
                            <li><strong>Assassin:</strong> +15% Crit Chance</li>
                            <li><strong>Shadow:</strong> +20% Dodge Chance</li>
                        </ul>
                    </div>

                    <div class="class-card">
                        <div class="class-header">
                            <div class="class-icon">🔮</div>
                            <div>
                                <div class="class-name">MAGE LINE</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">Magic Damage Dealer</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Masters of arcane arts, Mages deal devastating magical damage and manipulate reality.
                        </div>
                        <h3 style="color: var(--text-accent); margin: 16px 0 8px 0; font-size: 1em;">Base Bonuses (per tier):</h3>
                        <ul class="bonus-list">
                            <li><strong>+15% Magic</strong> per tier</li>
                            <li><strong>+10% Attack</strong> per tier</li>
                        </ul>
                        <h3 style="color: var(--text-highlight); margin: 16px 0 8px 0; font-size: 1em;">Special Abilities:</h3>
                        <ul class="bonus-list">
                            <li><strong>Necromancer:</strong> 20% Lifesteal</li>
                            <li><strong>Archmage:</strong> +30% Magic (massive bonus!)</li>
                        </ul>
                    </div>

                    <div class="class-card">
                        <div class="class-header">
                            <div class="class-icon">🏹</div>
                            <div>
                                <div class="class-name">RANGER LINE</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">Balanced with Luck</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Nature's warriors, Rangers balance combat prowess with fortune and keen senses.
                        </div>
                        <h3 style="color: var(--text-accent); margin: 16px 0 8px 0; font-size: 1em;">Base Bonuses (per tier):</h3>
                        <ul class="bonus-list">
                            <li><strong>+8% Attack</strong> per tier</li>
                            <li><strong>+12% Speed</strong> per tier</li>
                            <li><strong>+5% Luck</strong> per tier</li>
                        </ul>
                        <h3 style="color: var(--text-highlight); margin: 16px 0 8px 0; font-size: 1em;">Special Abilities:</h3>
                        <ul class="bonus-list">
                            <li><strong>Marksman:</strong> +25% Crit Chance</li>
                        </ul>
                    </div>

                    <div class="class-card">
                        <div class="class-header">
                            <div class="class-icon">⚔️</div>
                            <div>
                                <div class="class-name">RAIDER LINE</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">Raid Specialist</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Elite warriors specialized in group combat, excelling in raids and massive battles.
                        </div>
                        <h3 style="color: var(--text-accent); margin: 16px 0 8px 0; font-size: 1em;">Base Bonuses (per tier):</h3>
                        <ul class="bonus-list">
                            <li><strong>+10% Raid Power</strong> per tier</li>
                            <li><strong>+12% Attack</strong> per tier</li>
                        </ul>
                        <h3 style="color: var(--text-highlight); margin: 16px 0 8px 0; font-size: 1em;">Special Abilities:</h3>
                        <ul class="bonus-list">
                            <li><strong>Warchief:</strong> +30% Raid Power (best for raids!)</li>
                        </ul>
                    </div>

                    <div class="class-card">
                        <div class="class-header">
                            <div class="class-icon">🙏</div>
                            <div>
                                <div class="class-name">RITUALIST LINE</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">Religion/Support</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Divine servants who commune with gods, gaining favor and mystical powers.
                        </div>
                        <h3 style="color: var(--text-accent); margin: 16px 0 8px 0; font-size: 1em;">Base Bonuses (per tier):</h3>
                        <ul class="bonus-list">
                            <li><strong>+5% Favor Gain</strong> per tier</li>
                            <li><strong>+8% Magic</strong> per tier</li>
                            <li><strong>+3% Luck</strong> per tier</li>
                        </ul>
                        <h3 style="color: var(--text-highlight); margin: 16px 0 8px 0; font-size: 1em;">Special Abilities:</h3>
                        <ul class="bonus-list">
                            <li><strong>Prophet:</strong> +30% Favor, +20% Luck</li>
                        </ul>
                    </div>

                </div>
                
                <!-- NEW Ascendant Classes Section -->
                <div class="info-box" style="border-color: #ff6b35; background: rgba(255, 107, 53, 0.1);">
                    <h3 style="color: #ff6b35;">🔥 Advanced Specialization Classes (Tier 6 - Level 30+)</h3>
                    <p>Advanced specialization paths that allow each class line to maintain its unique identity. Each offers distinct bonuses and playstyles!</p>
                </div>
                
                <div class="class-grid">
                    <!-- Warlord Supreme -->
                    <div class="class-card" style="border-color: #dc2626;">
                        <div class="class-header">
                            <div class="class-icon">⚔️</div>
                            <div>
                                <div class="class-name" style="color: #dc2626;">WARLORD SUPREME</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">From Berserker • Pure DPS</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Masters of destruction with unparalleled offensive capabilities. The ultimate damage dealer.
                        </div>
                        <h3 style="color: #dc2626; margin: 16px 0 8px 0; font-size: 1em;">Ascendant Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+50% Attack</strong> (massive damage boost)</li>
                            <li><strong>+30% Defense</strong></li>
                            <li><strong>+15% Critical Chance</strong></li>
                            <li><strong>15% Lifesteal</strong></li>
                        </ul>
                    </div>
                    
                    <!-- Shadowlord -->
                    <div class="class-card" style="border-color: #6b21a8;">
                        <div class="class-header">
                            <div class="class-icon">🌙</div>
                            <div>
                                <div class="class-name" style="color: #6b21a8;">SHADOWLORD</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">From Nightblade • Speed/Stealth</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Masters of speed and stealth, striking from the shadows with deadly precision.
                        </div>
                        <h3 style="color: #6b21a8; margin: 16px 0 8px 0; font-size: 1em;">Ascendant Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+40% Speed</strong></li>
                            <li><strong>+25% Dodge Chance</strong></li>
                            <li><strong>+30% Steal Chance</strong></li>
                            <li><strong>+20% Critical Chance</strong></li>
                        </ul>
                    </div>
                    
                    <!-- Archsorcerer -->
                    <div class="class-card" style="border-color: #2563eb;">
                        <div class="class-header">
                            <div class="class-icon">🔮</div>
                            <div>
                                <div class="class-name" style="color: #2563eb;">ARCHSORCERER</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">From Archmage • Magic Mastery</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Ultimate masters of arcane arts with divine connections and supernatural luck.
                        </div>
                        <h3 style="color: #2563eb; margin: 16px 0 8px 0; font-size: 1em;">Ascendant Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+60% Magic</strong> (incredible magical power)</li>
                            <li><strong>+30% Luck</strong></li>
                            <li><strong>+40% Divine Favor</strong></li>
                        </ul>
                    </div>
                    
                    <!-- Grandmaster Archer -->
                    <div class="class-card" style="border-color: #059669;">
                        <div class="class-header">
                            <div class="class-icon">🎯</div>
                            <div>
                                <div class="class-name" style="color: #059669;">GRANDMASTER ARCHER</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">From Marksman • Precision</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Masters of precision and timing with unmatched accuracy and evasive abilities.
                        </div>
                        <h3 style="color: #059669; margin: 16px 0 8px 0; font-size: 1em;">Ascendant Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+30% Speed</strong></li>
                            <li><strong>+30% Critical Chance</strong></li>
                            <li><strong>+20% Dodge Chance</strong></li>
                        </ul>
                    </div>
                    
                    <!-- Khan -->
                    <div class="class-card" style="border-color: #b45309;">
                        <div class="class-header">
                            <div class="class-icon">👑</div>
                            <div>
                                <div class="class-name" style="color: #b45309;">KHAN</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">From Warchief • Leadership</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Legendary leaders who excel in commanding armies and dominating battlefields.
                        </div>
                        <h3 style="color: #b45309; margin: 16px 0 8px 0; font-size: 1em;">Ascendant Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+50% Raid Power</strong> (best for raids)</li>
                            <li><strong>+30% Attack</strong></li>
                            <li><strong>+30% Defense</strong></li>
                        </ul>
                    </div>
                    
                    <!-- Divine Oracle -->
                    <div class="class-card" style="border-color: #fbbf24;">
                        <div class="class-header">
                            <div class="class-icon">🌟</div>
                            <div>
                                <div class="class-name" style="color: #fbbf24;">DIVINE ORACLE</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">From Prophet • Divine Connection</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Sacred beings with direct divine connections and supernatural fortune.
                        </div>
                        <h3 style="color: #fbbf24; margin: 16px 0 8px 0; font-size: 1em;">Ascendant Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+80% Divine Favor</strong> (massive divine bonus)</li>
                            <li><strong>+40% Luck</strong></li>
                            <li><strong>+20% Magic</strong></li>
                        </ul>
                    </div>
                </div>
                
                <!-- Apex Classes Section -->
                <div class="info-box" style="border-color: #8b5cf6; background: rgba(139, 92, 246, 0.1);">
                    <h3 style="color: #8b5cf6;">💫 Apex Classes (Tier 7 - Level 50+)</h3>
                    <p>Elite evolution of Ascendant classes representing the pinnacle of specialized mastery!</p>
                </div>
                
                <div class="class-grid">
                    <!-- God Emperor -->
                    <div class="class-card" style="border-color: #dc2626; background: linear-gradient(135deg, rgba(220, 38, 38, 0.1), rgba(220, 38, 38, 0.05));">
                        <div class="class-header">
                            <div class="class-icon">👑</div>
                            <div>
                                <div class="class-name" style="color: #dc2626;">GOD EMPEROR</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">From Warlord Supreme • Ultimate Warrior</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Divine rulers of war with unmatched combat prowess and leadership abilities.
                        </div>
                        <h3 style="color: #dc2626; margin: 16px 0 8px 0; font-size: 1em;">Apex Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+80% Attack, +60% Defense</strong></li>
                            <li><strong>+80% Raid Power, +25% Crit</strong></li>
                            <li><strong>20% Lifesteal</strong></li>
                        </ul>
                    </div>
                    
                    <!-- Void Walker -->
                    <div class="class-card" style="border-color: #6b21a8; background: linear-gradient(135deg, rgba(107, 33, 168, 0.1), rgba(107, 33, 168, 0.05));">
                        <div class="class-header">
                            <div class="class-icon">🌌</div>
                            <div>
                                <div class="class-name" style="color: #6b21a8;">VOID WALKER</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">From Shadowlord • Reality Manipulator</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Masters of the void who manipulate reality itself, existing between dimensions.
                        </div>
                        <h3 style="color: #6b21a8; margin: 16px 0 8px 0; font-size: 1em;">Apex Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+70% Speed, +40% Dodge</strong></li>
                            <li><strong>+50% Steal Chance</strong></li>
                            <li><strong>+30% Magic</strong></li>
                        </ul>
                    </div>
                    
                    <!-- Reality Weaver -->
                    <div class="class-card" style="border-color: #2563eb; background: linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(37, 99, 235, 0.05));">
                        <div class="class-header">
                            <div class="class-icon">🌟</div>
                            <div>
                                <div class="class-name" style="color: #2563eb;">REALITY WEAVER</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">From Archsorcerer • Magic Transcendence</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Transcendent beings who weave the fabric of reality with unimaginable magical power.
                        </div>
                        <h3 style="color: #2563eb; margin: 16px 0 8px 0; font-size: 1em;">Apex Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+100% Magic</strong> (ultimate magical mastery)</li>
                            <li><strong>+60% Luck, +70% Divine Favor</strong></li>
                        </ul>
                    </div>
                    
                    <!-- Time Hunter -->
                    <div class="class-card" style="border-color: #059669; background: linear-gradient(135deg, rgba(5, 150, 105, 0.1), rgba(5, 150, 105, 0.05));">
                        <div class="class-header">
                            <div class="class-icon">⏰</div>
                            <div>
                                <div class="class-name" style="color: #059669;">TIME HUNTER</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">From Grandmaster Archer • Temporal Master</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Hunters who have mastered time itself, striking with perfect timing across dimensions.
                        </div>
                        <h3 style="color: #059669; margin: 16px 0 8px 0; font-size: 1em;">Apex Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+80% Speed</strong></li>
                            <li><strong>+50% Critical Chance</strong></li>
                            <li><strong>+30% Dodge Chance</strong></li>
                        </ul>
                    </div>
                    
                    <!-- Worldbreaker -->
                    <div class="class-card" style="border-color: #b45309; background: linear-gradient(135deg, rgba(180, 83, 9, 0.1), rgba(180, 83, 9, 0.05));">
                        <div class="class-header">
                            <div class="class-icon">💥</div>
                            <div>
                                <div class="class-name" style="color: #b45309;">WORLDBREAKER</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">From Khan • Destructive Power</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Conquerors whose very presence reshapes battlefields and breaks the will of armies.
                        </div>
                        <h3 style="color: #b45309; margin: 16px 0 8px 0; font-size: 1em;">Apex Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+70% Attack, +50% Defense</strong></li>
                            <li><strong>+100% Raid Power</strong> (ultimate raid leader)</li>
                        </ul>
                    </div>
                    
                    <!-- Cosmic Sage -->
                    <div class="class-card" style="border-color: #fbbf24; background: linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(251, 191, 36, 0.05));">
                        <div class="class-header">
                            <div class="class-icon">🌌</div>
                            <div>
                                <div class="class-name" style="color: #fbbf24;">COSMIC SAGE</div>
                                <div style="color: var(--text-secondary); font-size: 0.9em;">From Divine Oracle • Universal Wisdom</div>
                            </div>
                        </div>
                        <div class="class-description">
                            Enlightened beings with cosmic awareness and direct communication with universal forces.
                        </div>
                        <h3 style="color: #fbbf24; margin: 16px 0 8px 0; font-size: 1em;">Apex Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+120% Divine Favor</strong> (maximum divine connection)</li>
                            <li><strong>+80% Luck, +50% Magic</strong></li>
                        </ul>
                    </div>
                </div>
                
                <!-- Universal Sovereign Section -->
                <div class="info-box" style="border-color: var(--gold); background: linear-gradient(135deg, rgba(212, 175, 55, 0.15), rgba(212, 175, 55, 0.05));">
                    <h3 style="color: var(--gold);">🏆 Universal Sovereign (Tier 8 - Level 100)</h3>
                    <p><strong>ULTIMATE EVOLUTION:</strong> All Elite Mastery classes can evolve to Universal Sovereign at Level 100!</p>
                    <p><strong>PINNACLE:</strong> The ultimate expression of character development, representing mastery of all paths.</p>
                </div>
                
                <div class="class-grid">
                    <div class="class-card" style="border: 3px solid var(--gold); background: linear-gradient(135deg, rgba(212, 175, 55, 0.2), rgba(212, 175, 55, 0.05)); box-shadow: 0 0 20px rgba(212, 175, 55, 0.3);">
                        <div class="class-header">
                            <div class="class-icon" style="color: var(--gold); font-size: 2em;">👑</div>
                            <div>
                                <div class="class-name" style="color: var(--gold); font-size: 1.3em;">UNIVERSAL SOVEREIGN</div>
                                <div style="color: var(--gold); font-size: 0.9em;">From any Apex class • Ultimate Transcendence</div>
                            </div>
                        </div>
                        <div class="class-description">
                            The ultimate evolution representing mastery over all aspects of existence. Available to all paths at level 100, representing the pinnacle of character development.
                        </div>
                        <h3 style="color: var(--gold); margin: 16px 0 8px 0; font-size: 1.1em;">Transcendent Bonuses:</h3>
                        <ul class="bonus-list">
                            <li><strong>+100% Attack, +100% Defense, +100% Magic</strong></li>
                            <li><strong>+100% Speed, +100% Luck</strong></li>
                            <li><strong>+150% Raid Power, +150% Divine Favor</strong></li>
                            <li><strong>+30% Critical Chance, +30% Dodge Chance</strong></li>
                        </ul>
                        <div style="text-align: center; margin-top: 20px; padding: 15px; background: rgba(212, 175, 55, 0.1); border-radius: 8px;">
                            <strong style="color: var(--gold);">The ultimate expression of power - representing the pinnacle of all evolutionary paths</strong>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Races Section -->
            <section id="races" class="section">
                <h2>🧬 Races</h2>
                <p>Choose your heritage to gain permanent racial bonuses that affect all aspects of gameplay.</p>
                
                <div class="stats-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Race</th>
                                <th>Luck</th>
                                <th>XP Gain</th>
                                <th>Gold Find</th>
                                <th>Favor Gain</th>
                                <th>Specialization</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>Human</strong></td>
                                <td>1.0x</td>
                                <td>1.1x</td>
                                <td>1.0x</td>
                                <td>1.0x</td>
                                <td>Balanced progression</td>
                            </tr>
                            <tr>
                                <td><strong>Elf</strong></td>
                                <td>1.2x</td>
                                <td>1.0x</td>
                                <td>0.9x</td>
                                <td>1.3x</td>
                                <td>Luck and divine favor</td>
                            </tr>
                            <tr>
                                <td><strong>Dwarf</strong></td>
                                <td>0.9x</td>
                                <td>0.9x</td>
                                <td>1.4x</td>
                                <td>0.8x</td>
                                <td>Gold finding specialists</td>
                            </tr>
                            <tr>
                                <td><strong>Orc</strong></td>
                                <td>0.8x</td>
                                <td>1.3x</td>
                                <td>0.8x</td>
                                <td>0.7x</td>
                                <td>Fast XP gain through combat</td>
                            </tr>
                            <tr>
                                <td><strong>Halfling</strong></td>
                                <td>1.4x</td>
                                <td>0.8x</td>
                                <td>1.1x</td>
                                <td>1.1x</td>
                                <td>Ultimate luck</td>
                            </tr>
                            <tr>
                                <td><strong>Gnome</strong></td>
                                <td>1.3x</td>
                                <td>0.9x</td>
                                <td>1.0x</td>
                                <td>1.2x</td>
                                <td>Luck and divine balance</td>
                            </tr>
                            <tr>
                                <td><strong>Dragonborn</strong></td>
                                <td>1.0x</td>
                                <td>1.1x</td>
                                <td>1.1x</td>
                                <td>0.9x</td>
                                <td>Well-rounded</td>
                            </tr>
                            <tr>
                                <td><strong>Tiefling</strong></td>
                                <td>1.2x</td>
                                <td>1.0x</td>
                                <td>1.2x</td>
                                <td>0.5x</td>
                                <td>Luck and gold, no divine favor</td>
                            </tr>
                            <tr>
                                <td><strong>Undead</strong></td>
                                <td>1.5x</td>
                                <td>0.7x</td>
                                <td>0.9x</td>
                                <td>0.0x</td>
                                <td>Supernatural luck, no divine favor</td>
                            </tr>
                            <tr>
                                <td><strong>Demon</strong></td>
                                <td>1.6x</td>
                                <td>0.8x</td>
                                <td>1.3x</td>
                                <td>0.0x</td>
                                <td>Maximum luck and gold, no divine favor</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="info-box">
                    <h3>How Races Work</h3>
                    <p><strong>Choose Once:</strong> Use <code>!race &lt;name&gt;</code> to select your race permanently</p>
                    <p><strong>View Options:</strong> <code>!races</code> shows all available races and their bonuses</p>
                    <p><strong>Multipliers Apply:</strong> Race bonuses affect XP/gold from adventures, battles, raids, and prayers</p>
                    <p><strong>Strategy Matters:</strong> Choose based on your playstyle - luck for gambling, XP for progression, or gold for wealth</p>
                </div>
            </section>

            <!-- Auto-Play Section -->
            <section id="auto-play" class="section">
                <h2>🤖 Auto-Play System</h2>
                <p>DiscordRPG features fully automated gameplay that progresses while you're online.</p>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">🗺️</div>
                        <div class="feature-title">Enhanced Adventures</div>
                        <div class="feature-description">
                            <strong>Every 10-30 minutes</strong><br>
                            32 different adventure types across 5 tiers: Short (5-60min), Medium (45min-3h), Long (2-8h), Epic (4-8h, Lvl 10+), Legendary (8-24h, Lvl 15+)!
                            Rewards: XP, Gold, Items with individual completion embeds
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">⚔️</div>
                        <div class="feature-title">Multi-Scale Battles</div>
                        <div class="feature-description">
                            <strong>Every 2-8 minutes</strong><br>
                            <strong>1v1:</strong> Quick duels • <strong>3v3:</strong> Team battles • <strong>5v5:</strong> Epic armies • <strong>10v10:</strong> Massive battlefields!
                            Battle type depends on online player count.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🏰</div>
                        <div class="feature-title">Epic Raids</div>
                        <div class="feature-description">
                            <strong>Every 35 minutes</strong><br>
                            20-40 players fight legendary bosses together. Massive rewards for victory, consolation for defeat.
                            MVP recognition and legendary loot!
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🟢</div>
                        <div class="feature-title">Online Requirement</div>
                        <div class="feature-description">
                            <strong>Discord Status = Online</strong><br>
                            Away, DND, or Invisible prevents participation.
                            Keep green status for maximum progression!
                        </div>
                    </div>
                </div>

                <div class="info-box">
                    <h3>Battle System Scaling</h3>
                    <p><strong>2-5 players online:</strong> 1v1 duels only</p>
                    <p><strong>6-9 players online:</strong> 55% chance 3v3 team battles, 45% chance 1v1</p>
                    <p><strong>10-19 players online:</strong> 40% chance 3v3, 35% chance 5v5 armies, 25% chance 1v1</p>
                    <p><strong>20+ players online:</strong> 30% chance 3v3, 25% chance 10v10 massive battlefields, 25% chance 5v5, 20% chance 1v1</p>
                </div>

                <div class="adventure-breakdown">
                    <h3>🏆 Adventure Tier Breakdown & Loot Scaling</h3>
                    <p style="margin-bottom: 24px; color: var(--text-secondary);">
                        <strong>Important:</strong> Within each tier, longer/harder adventures give significantly better loot! 
                        Item stats, drop rates, and gold rewards all scale with difficulty.
                    </p>

                    <!-- Short Tier -->
                    <div class="tier-section" style="margin-bottom: 24px; padding: 16px; background: rgba(60, 60, 60, 0.3); border-radius: 8px;">
                        <h4 style="color: #4CAF50; margin-bottom: 12px;">⚡ Short Adventures (5min - 1hr)</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 12px;">
                            <div>
                                <strong>Duration:</strong> 5-10min → 30-60min<br>
                                <strong>Gold:</strong> 50-150 → 300-700<br>
                                <strong>Difficulty:</strong> Level 1 → Level 7
                            </div>
                            <div>
                                <strong>Item Stats:</strong> 4-9 → 8-15<br>
                                <strong>Drop Rate:</strong> 12% → 24%<br>
                                <strong>Examples:</strong> Farmer sheep → Goblin raiders
                            </div>
                            <div style="background: rgba(76, 175, 80, 0.2); padding: 8px; border-radius: 4px;">
                                <strong>Scaling Benefits:</strong><br>
                                • 4x more gold potential<br>
                                • 67% higher item stats<br>
                                • 2x better drop rates
                            </div>
                        </div>
                    </div>

                    <!-- Medium Tier -->
                    <div class="tier-section" style="margin-bottom: 24px; padding: 16px; background: rgba(60, 60, 60, 0.3); border-radius: 8px;">
                        <h4 style="color: #FF9800; margin-bottom: 12px;">⏳ Medium Adventures (45min - 3hr)</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 12px;">
                            <div>
                                <strong>Duration:</strong> 45-90min → 100-180min<br>
                                <strong>Gold:</strong> 400-800 → 900-1,700<br>
                                <strong>Difficulty:</strong> Level 6 → Level 11
                            </div>
                            <div>
                                <strong>Item Stats:</strong> 7-14 → 12-19<br>
                                <strong>Drop Rate:</strong> 22% → 32%<br>
                                <strong>Examples:</strong> Lost treasure → Enemy fortress
                            </div>
                            <div style="background: rgba(255, 152, 0, 0.2); padding: 8px; border-radius: 4px;">
                                <strong>Scaling Benefits:</strong><br>
                                • 2x more gold potential<br>
                                • 36% higher item stats<br>
                                • 45% better drop rates
                            </div>
                        </div>
                    </div>

                    <!-- Long Tier -->
                    <div class="tier-section" style="margin-bottom: 24px; padding: 16px; background: rgba(60, 60, 60, 0.3); border-radius: 8px;">
                        <h4 style="color: #3F51B5; margin-bottom: 12px;">🏔️ Long Adventures (2hr - 8hr)</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 12px;">
                            <div>
                                <strong>Duration:</strong> 2-4hr → 4-7hr<br>
                                <strong>Gold:</strong> 1,000-2,000 → 1,800-3,600<br>
                                <strong>Difficulty:</strong> Level 12 → Level 16
                            </div>
                            <div>
                                <strong>Item Stats:</strong> 13-20 → 17-24<br>
                                <strong>Drop Rate:</strong> 34% → 42%<br>
                                <strong>Examples:</strong> Distant lands → Holy Grail
                            </div>
                            <div style="background: rgba(63, 81, 181, 0.2); padding: 8px; border-radius: 4px;">
                                <strong>Scaling Benefits:</strong><br>
                                • 80% more gold potential<br>
                                • 20% higher item stats<br>
                                • 24% better drop rates
                            </div>
                        </div>
                    </div>

                    <!-- Epic Tier -->
                    <div class="tier-section" style="margin-bottom: 24px; padding: 16px; background: rgba(60, 60, 60, 0.3); border-radius: 8px;">
                        <h4 style="color: #9C27B0; margin-bottom: 12px;">🌟 Epic Adventures (4hr - 8hr)</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 12px;">
                            <div>
                                <strong>Duration:</strong> 4-6hr → 5-8hr<br>
                                <strong>Gold:</strong> 4,500-8,000<br>
                                <strong>Required Level:</strong> 10+ (automatic)
                            </div>
                            <div>
                                <strong>Item Stats:</strong> 18-25 → 26-33<br>
                                <strong>Drop Rate:</strong> 44% → 60%<br>
                                <strong>Examples:</strong> Underdark → Reforge World
                            </div>
                            <div style="background: rgba(156, 39, 176, 0.2); padding: 8px; border-radius: 4px;">
                                <strong>Scaling Benefits:</strong><br>
                                • 75% more gold potential<br>
                                • 32% higher item stats<br>
                                • 36% better drop rates
                            </div>
                        </div>
                    </div>

                    <!-- Legendary Tier -->
                    <div class="tier-section" style="margin-bottom: 24px; padding: 16px; background: rgba(60, 60, 60, 0.3); border-radius: 8px;">
                        <h4 style="color: #FF5722; margin-bottom: 12px;">⚡ Legendary Adventures (8hr - 24hr)</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 12px;">
                            <div>
                                <strong>Duration:</strong> 8-16hr → 12-24hr<br>
                                <strong>Gold:</strong> 15,000-30,000<br>
                                <strong>Required Level:</strong> 15+ (automatic)
                            </div>
                            <div>
                                <strong>Item Stats:</strong> 31-38 → 50+ (max)<br>
                                <strong>Drop Rate:</strong> 70% → 110% (guaranteed+)<br>
                                <strong>Examples:</strong> Transcend limits → Ultimate ascension
                            </div>
                            <div style="background: rgba(255, 87, 34, 0.2); padding: 8px; border-radius: 4px;">
                                <strong>Scaling Benefits:</strong><br>
                                • 200% more gold potential<br>
                                • 32% higher item stats<br>
                                • Guaranteed+ drop rates
                            </div>
                        </div>
                    </div>

                    <div style="background: rgba(255, 193, 7, 0.2); padding: 16px; border-radius: 8px; margin-top: 24px;">
                        <h4 style="color: #FFC107; margin-bottom: 12px;">💡 Pro Tips for Maximum Rewards</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>Level up to access higher difficulties</strong> - each adventure tier has adventures for different level ranges</li>
                            <li><strong>Equipment power affects success rates</strong> - better gear means higher success chances</li>
                            <li><strong>Epic/Legendary adventures provide premium loot</strong> - automatically awarded to level 10+ players every 45 minutes</li>
                        </ul>
                    </div>
                </div>

                <div class="warning-box">
                    <h3>Online Status Critical</h3>
                    <p>Your Discord status must be set to <strong>Online (green circle)</strong> to participate in any automated gameplay. This includes adventures, battles, and raids. Other statuses like Away, Do Not Disturb, or Invisible will completely prevent your character from progressing.</p>
                </div>
            </section>

            <!-- Battle System Section -->
            <section id="battles" class="section">
                <h2>⚔️ Battle System</h2>
                <p>Experience dynamic combat that scales from intimate duels to massive battlefield wars.</p>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">🥊</div>
                        <div class="feature-title">1v1 Duels</div>
                        <div class="feature-description">
                            <strong>Classic Combat</strong><br>
                            Quick duels between similar-level players. Winners get 30% item drop chance, losers get 5% chance. Individual reward embeds show XP, gold, and items.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🛡️</div>
                        <div class="feature-title">3v3 Team Battles</div>
                        <div class="feature-description">
                            <strong>Tactical Combat</strong><br>
                            Team Alpha vs Team Beta! Coordination penalties make strategy important. Enhanced rewards: 80-180 XP winners, 20-60 XP participants.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">⚔️</div>
                        <div class="feature-title">5v5 Epic Armies</div>
                        <div class="feature-description">
                            <strong>Epic Warfare</strong><br>
                            Legendary army clashes with massive coordination challenges. Epic rewards: 120-250 XP winners, 30-80 XP participants.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🏰</div>
                        <div class="feature-title">10v10 Massive Battlefields</div>
                        <div class="feature-description">
                            <strong>Ultimate Warfare</strong><br>
                            Legion Alpha vs Legion Beta in the ultimate test of might! Massive rewards: 180-350 XP winners, 45-120 XP participants.
                        </div>
                    </div>
                </div>

                <div class="stats-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Battle Type</th>
                                <th>Players Required</th>
                                <th>Coordination Penalty</th>
                                <th>Winner Item Drop</th>
                                <th>Loser Item Drop</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>1v1 Duel</strong></td>
                                <td>2+</td>
                                <td>None</td>
                                <td>30%</td>
                                <td>5%</td>
                            </tr>
                            <tr>
                                <td><strong>3v3 Team</strong></td>
                                <td>6+</td>
                                <td>20% (0.8x power)</td>
                                <td>25%</td>
                                <td>5%</td>
                            </tr>
                            <tr>
                                <td><strong>5v5 Army</strong></td>
                                <td>10+</td>
                                <td>25% (0.75x power)</td>
                                <td>25%</td>
                                <td>5%</td>
                            </tr>
                            <tr>
                                <td><strong>10v10 Legion</strong></td>
                                <td>20+</td>
                                <td>35% (0.65x power)</td>
                                <td>25%</td>
                                <td>5%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="info-box">
                    <h3>Battle Mechanics</h3>
                    <p><strong>Level Grouping:</strong> Players are grouped into similar level ranges (within 5 levels) for fair fights</p>
                    <p><strong>Power Calculation:</strong> Character level × 10 + equipment damage + equipment armor + armor bonuses (health, speed, luck×100, crit×100, magic) + random variance</p>
                    <p><strong>Armor Integration:</strong> All armor bonuses (health, speed, luck, crit, magic) directly factor into combat power calculations</p>
                    <p><strong>Coordination Penalty:</strong> Larger battles have coordination challenges that reduce effective power</p>
                    <p><strong>Race Bonuses:</strong> All XP and gold rewards are multiplied by your race bonuses</p>
                    <p><strong>Beautiful Embeds:</strong> All battle results are displayed in clean, colorful Discord embeds</p>
                </div>

                <div class="success-box">
                    <h3>Battle Strategy Tips</h3>
                    <p><strong>Equipment Matters:</strong> Higher damage, armor, and armor bonuses directly increase your battle power</p>
                    <p><strong>Armor Strategy:</strong> Equip full armor sets for maximum defensive bonuses that boost combat effectiveness</p>
                    <p><strong>Level Up:</strong> Each level adds +10 base battle power, making progression important</p>
                    <p><strong>Stay Online:</strong> Only players with Online (green) Discord status participate in auto battles</p>
                    <p><strong>Everyone Wins:</strong> Even battle participants get XP rewards and small item drop chances</p>
                </div>
            </section>

            <!-- Economy Section -->
            <section id="economy" class="section">
                <h2>💰 Economy</h2>
                <p>Trade items, earn gold, and build your wealth through various economic systems.</p>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">🛒</div>
                        <div class="feature-title">Marketplace</div>
                        <div class="feature-description">
                            Buy and sell items with other players. Use <code>!market</code> to browse listings and <code>!offer</code> to sell your items.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🎁</div>
                        <div class="feature-title">Daily Rewards</div>
                        <div class="feature-description">
                            Claim daily login bonuses with <code>!daily</code>. Consecutive logins increase rewards!<br>
                            <strong>Streak Rewards:</strong> Day 3: Common Crate • Day 6: Uncommon Crate • Day 10: Magic Crate • Day 7+: +0.1 Luck
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">💸</div>
                        <div class="feature-title">Item Trading</div>
                        <div class="feature-description">
                            Trade items directly with <code>!give</code> or sell to NPC merchants with <code>!sell</code>.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">⚖️</div>
                        <div class="feature-title">Fair Pricing</div>
                        <div class="feature-description">
                            Market prices are player-driven. Rare items and high-stat equipment command premium prices.
                        </div>
                    </div>
                </div>
            </section>

            <!-- Religion Section -->
            <section id="religion" class="section">
                <h2>🙏 Religion</h2>
                <p>Choose a deity to follow and gain divine powers through prayer and sacrifice.</p>
                
                <div class="stats-table">
                    <table>
                        <thead>
                            <tr>
                                <th>God</th>
                                <th>Luck Multiplier</th>
                                <th>Sacrifice Bonus</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>🌀 Chaos</strong></td>
                                <td>1.2x</td>
                                <td>0.8x</td>
                                <td>High luck, lower favor gain</td>
                            </tr>
                            <tr>
                                <td><strong>⚖️ Order</strong></td>
                                <td>0.9x</td>
                                <td>1.1x</td>
                                <td>Lower luck, higher favor gain</td>
                            </tr>
                            <tr>
                                <td><strong>⚔️ War</strong></td>
                                <td>1.0x</td>
                                <td>1.0x</td>
                                <td>Balanced combat deity</td>
                            </tr>
                            <tr>
                                <td><strong>🌿 Nature</strong></td>
                                <td>1.1x</td>
                                <td>0.9x</td>
                                <td>Good luck with nature's balance</td>
                            </tr>
                            <tr>
                                <td><strong>💀 Death</strong></td>
                                <td>0.8x</td>
                                <td>1.3x</td>
                                <td>Lower luck, much higher favor</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="info-box">
                    <h3>How Religion Works</h3>
                    <p><strong>Choose Once:</strong> Use <code>!choose &lt;god&gt;</code> to select your deity permanently</p>
                    <p><strong>Pray Daily:</strong> <code>!pray</code> every 4 hours for favor (race affects gains)</p>
                    <p><strong>Sacrifice Gold:</strong> <code>!sacrifice &lt;amount&gt;</code> every 12 hours for major favor</p>
                    <p><strong>Benefits:</strong> Gods modify your luck and sacrifice effectiveness</p>
                </div>

                <div class="stats-table">
                    <h3>✨ Divine Blessings</h3>
                    <p>Spend accumulated favor on temporary divine buffs that enhance all activities!</p>
                    <table>
                        <thead>
                            <tr>
                                <th>Blessing</th>
                                <th>Cost</th>
                                <th>Duration</th>
                                <th>Effect</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>🍀 Fortune</strong></td>
                                <td>25 favor</td>
                                <td>2 hours</td>
                                <td>+0.25 Luck (affects all activities)</td>
                            </tr>
                            <tr>
                                <td><strong>💰 Prosperity</strong></td>
                                <td>30 favor</td>
                                <td>1 hour</td>
                                <td>+50% Gold from all sources</td>
                            </tr>
                            <tr>
                                <td><strong>📚 Wisdom</strong></td>
                                <td>40 favor</td>
                                <td>1.5 hours</td>
                                <td>+75% XP from all sources</td>
                            </tr>
                            <tr>
                                <td><strong>🛡️ Protection</strong></td>
                                <td>50 favor</td>
                                <td>6 hours</td>
                                <td>Prevents XP/gold loss from penalties</td>
                            </tr>
                            <tr>
                                <td><strong>🔮 Divination</strong></td>
                                <td>35 favor</td>
                                <td>1 hour</td>
                                <td>Guarantees next adventure success</td>
                            </tr>
                            <tr>
                                <td><strong>⚔️ Valor</strong></td>
                                <td>45 favor</td>
                                <td>2 hours</td>
                                <td>+25% Battle power for all combat</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <div class="info-box">
                        <h4>Divine Blessing Commands</h4>
                        <p><strong>View Blessings:</strong> <code>!bless</code> - See all available blessings and active ones</p>
                        <p><strong>Purchase Blessing:</strong> <code>!bless &lt;type&gt;</code> - Buy a specific blessing with favor</p>
                        <p><strong>Example:</strong> <code>!bless wisdom</code> - Purchase Wisdom blessing for +75% XP</p>
                        <p style="color: var(--text-accent); font-weight: 500;">💡 Tip: Multiple blessing types can be active simultaneously, but you can't stack the same blessing!</p>
                    </div>
                </div>
            </section>

            <!-- Gambling Section -->
            <section id="gambling" class="section">
                <h2>🎰 Gambling</h2>
                <p>Risk your gold in various casino games for potentially massive rewards.</p>
                
                <div class="stats-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Game</th>
                                <th>Win Rate</th>
                                <th>Max Bet</th>
                                <th>Luck Effect</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>Gamble</strong></td>
                                <td>40% (±luck)</td>
                                <td>15,000 gold</td>
                                <td>Yes - affects win chance</td>
                            </tr>
                            <tr>
                                <td><strong>Coinflip</strong></td>
                                <td>50%</td>
                                <td>10,000 gold</td>
                                <td>No - pure chance</td>
                            </tr>
                            <tr>
                                <td><strong>Slots</strong></td>
                                <td>Variable</td>
                                <td>5,000 gold</td>
                                <td>No - weighted symbols</td>
                            </tr>
                            <tr>
                                <td><strong>Blackjack</strong></td>
                                <td>~47%</td>
                                <td>7,500 gold</td>
                                <td>No - card based</td>
                            </tr>
                            <tr>
                                <td><strong>Diceroll</strong></td>
                                <td>~50%</td>
                                <td>3,000 gold</td>
                                <td>No - pure RNG</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="warning-box">
                    <h3>Gambling Risks</h3>
                    <p>All gambling has cooldowns to prevent spam. Only gamble what you can afford to lose!</p>
                    <p><strong>Luck matters:</strong> Only the <code>!gamble</code> command is affected by your luck stat.</p>
                </div>
            </section>

            <!-- Raids Section -->
            <section id="raids" class="section">
                <h2>🏰 Raids</h2>
                <p>Epic group battles against legendary bosses that require teamwork and strategy.</p>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">⏰</div>
                        <div class="feature-title">Raid Schedule</div>
                        <div class="feature-description">
                            <strong>Every 35 minutes</strong><br>
                            Automatic raids start with 20-40 random online players selected to fight epic bosses together.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">👥</div>
                        <div class="feature-title">Team Combat</div>
                        <div class="feature-description">
                            <strong>Group Strategy</strong><br>
                            Success depends on team composition, player levels, and coordination. Higher level players contribute more.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🐉</div>
                        <div class="feature-title">Epic Bosses</div>
                        <div class="feature-description">
                            <strong>10 Unique Bosses</strong><br>
                            Face legendary creatures like Ancient Dragons, Demon Lords, and Cosmic Entities with massive HP pools.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">💎</div>
                        <div class="feature-title">Massive Rewards</div>
                        <div class="feature-description">
                            <strong>Victory Spoils</strong><br>
                            Successful raids grant large XP, gold, and high-quality equipment. Raiders get multiplied rewards.
                        </div>
                    </div>
                </div>
                
                <div class="stats-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Boss</th>
                                <th>Type</th>
                                <th>HP Range</th>
                                <th>Special Abilities</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>Ancient Dragon</strong></td>
                                <td>Fire</td>
                                <td>15,000 - 25,000</td>
                                <td>Breath attack, armor penetration</td>
                            </tr>
                            <tr>
                                <td><strong>Demon Lord</strong></td>
                                <td>Dark</td>
                                <td>18,000 - 28,000</td>
                                <td>Life drain, corruption aura</td>
                            </tr>
                            <tr>
                                <td><strong>Frost Giant</strong></td>
                                <td>Ice</td>
                                <td>12,000 - 22,000</td>
                                <td>Area freeze, massive damage</td>
                            </tr>
                            <tr>
                                <td><strong>Void Wraith</strong></td>
                                <td>Shadow</td>
                                <td>20,000 - 30,000</td>
                                <td>Phase shifting, void magic</td>
                            </tr>
                            <tr>
                                <td><strong>Titan Golem</strong></td>
                                <td>Earth</td>
                                <td>25,000 - 35,000</td>
                                <td>Massive defense, earth spikes</td>
                            </tr>
                            <tr>
                                <td><strong>Storm Elemental</strong></td>
                                <td>Lightning</td>
                                <td>16,000 - 26,000</td>
                                <td>Chain lightning, storm rage</td>
                            </tr>
                            <tr>
                                <td><strong>Undead Lich</strong></td>
                                <td>Necromancy</td>
                                <td>22,000 - 32,000</td>
                                <td>Undead summons, death magic</td>
                            </tr>
                            <tr>
                                <td><strong>Celestial Guardian</strong></td>
                                <td>Holy</td>
                                <td>20,000 - 30,000</td>
                                <td>Divine shields, healing</td>
                            </tr>
                            <tr>
                                <td><strong>Kraken</strong></td>
                                <td>Sea</td>
                                <td>18,000 - 28,000</td>
                                <td>Tentacle attacks, whirlpool</td>
                            </tr>
                            <tr>
                                <td><strong>Cosmic Entity</strong></td>
                                <td>Cosmic</td>
                                <td>30,000 - 40,000</td>
                                <td>Reality distortion, ultimate power</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="info-box">
                    <h3>Raid Strategy Tips</h3>
                    <p><strong>Stay Online:</strong> Only online players (green status) are selected for raids</p>
                    <p><strong>Level Matters:</strong> Higher level players deal more damage and have better survival chances</p>
                    <p><strong>Class Bonuses:</strong> Raiders benefit from raid-specific class multipliers (Warchief = +30%!)</p>
                    <p><strong>Team Success:</strong> All participants share in victory rewards, encouraging teamwork</p>
                </div>
            </section>

            <!-- Equipment Section -->
            <section id="equipment" class="section">
                <h2>⚔️ Equipment & Armor System</h2>
                <p>Master the complete equipment system with weapons, armor slots, and specialized stat bonuses.</p>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">🗡️</div>
                        <div class="feature-title">Weapons</div>
                        <div class="feature-description">
                            <strong>Damage Dealers:</strong> Swords, Axes, Wands, Bows, etc.<br>
                            Provide attack damage and some armor. Only one primary weapon can be equipped at a time.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🛡️</div>
                        <div class="feature-title">5-Piece Armor System</div>
                        <div class="feature-description">
                            <strong>Full Protection:</strong> Head, Chest, Legs, Hands, Feet<br>
                            Each slot provides specialized defensive bonuses. Armor pieces provide NO damage - only defensive stats!
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">✨</div>
                        <div class="feature-title">Armor Bonuses</div>
                        <div class="feature-description">
                            <strong>Advanced Stats:</strong> Health, Speed, Luck, Crit, Magic<br>
                            Each armor type specializes in different bonuses. All bonuses factor into combat calculations!
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📦</div>
                        <div class="feature-title">Dynamic Generation</div>
                        <div class="feature-description">
                            <strong>Smart Drops:</strong> 60% weapons, 40% armor<br>
                            Items generated based on content difficulty. All armor drops follow specialized stat distributions.
                        </div>
                    </div>
                </div>

                <div class="stats-table">
                    <h3>🛡️ Armor Slot Specializations</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Armor Slot</th>
                                <th>Primary Stats</th>
                                <th>Secondary Stats</th>
                                <th>Specialization</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>🗿 Helmet</strong></td>
                                <td>Armor (40%), Luck (30%)</td>
                                <td>Magic (20%), Health (10%)</td>
                                <td>Mental protection & fortune</td>
                            </tr>
                            <tr>
                                <td><strong>🦺 Chestplate</strong></td>
                                <td>Armor (50%), Health (40%)</td>
                                <td>Speed (10%)</td>
                                <td>Core defense & vitality</td>
                            </tr>
                            <tr>
                                <td><strong>👖 Leggings</strong></td>
                                <td>Armor (60%), Health (30%)</td>
                                <td>Speed (10%)</td>
                                <td>Heavy protection & mobility</td>
                            </tr>
                            <tr>
                                <td><strong>🧤 Gauntlets</strong></td>
                                <td>Crit (40%), Armor (30%)</td>
                                <td>Speed (20%), Magic (10%)</td>
                                <td>Combat precision & dexterity</td>
                            </tr>
                            <tr>
                                <td><strong>👟 Boots</strong></td>
                                <td>Speed (40%), Armor (40%)</td>
                                <td>Luck (20%)</td>
                                <td>Movement & agility</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="info-box">
                    <h3>🎯 Combat Integration</h3>
                    <p><strong>All Armor Bonuses Factor Into Combat:</strong> Health, Speed, Luck, Crit, and Magic bonuses are fully integrated into all battle calculations including manual battles, auto battles, and raids!</p>
                    <p><strong>Damage Restriction:</strong> Armor pieces provide NO damage bonuses - only defensive and utility stats. This maintains clear distinction between weapons and armor.</p>
                    <p><strong>Power Calculation:</strong> Armor bonuses are converted to battle power (luck/crit × 100, others direct addition) and added to your total combat effectiveness.</p>
                </div>

                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">📊</div>
                        <div class="feature-title">Stat Types</div>
                        <div class="feature-description">
                            <strong>❤️ Health:</strong> Increases survivability<br>
                            <strong>💨 Speed:</strong> Improves reaction time<br>
                            <strong>🍀 Luck:</strong> Affects all RNG events<br>
                            <strong>💥 Crit:</strong> Critical hit chance<br>
                            <strong>✨ Magic:</strong> Magical power
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🎲</div>
                        <div class="feature-title">Item Quality</div>
                        <div class="feature-description">
                            <strong>Rarity Tiers:</strong> Common → Divine<br>
                            Based on total stat points. Higher tier items have better stat distributions and values.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">⚙️</div>
                        <div class="feature-title">Auto-Unequip</div>
                        <div class="feature-description">
                            <strong>Smart Management:</strong> Equipment conflicts<br>
                            Automatically unequips conflicting items when equipping new gear. Clear conflict resolution.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📦</div>
                        <div class="feature-title">Crate System</div>
                        <div class="feature-description">
                            <strong>All Tiers:</strong> Common → Mystery<br>
                            Contains both weapons and armor with full stat bonuses. Higher tiers guarantee better items.
                        </div>
                    </div>
                </div>
                
                <div class="success-box">
                    <h3>Equipment Strategy</h3>
                    <p><strong>Weapons First:</strong> Prioritize weapon damage for immediate combat improvement</p>
                    <p><strong>Full Armor Set:</strong> Equip all 5 armor slots for maximum defensive bonuses</p>
                    <p><strong>Stat Synergy:</strong> Match armor bonuses to your class (Luck for Thieves, Magic for Mages, etc.)</p>
                    <p><strong>Combat Power:</strong> Remember that ALL armor bonuses directly increase your battle effectiveness!</p>
                </div>

                <div class="warning-box">
                    <h3>Equipment Tips</h3>
                    <p><strong>Manual Equipping:</strong> Use <code>!equip &lt;id&gt;</code> to equip items - nothing equips automatically!</p>
                    <p><strong>View Details:</strong> Use <code>!item &lt;id&gt;</code> to see complete item stats including armor bonuses</p>
                    <p><strong>Check Totals:</strong> Use <code>!equipment</code> to see your total armor bonuses and combat stats</p>
                    <p><strong>Inventory Management:</strong> Items show armor bonuses with emojis for easy identification</p>
                </div>
            </section>

            <!-- Progression Section -->
            <section id="progression" class="section">
                <h2>📈 Progression</h2>
                <p>Advance your character through multiple progression systems and reach legendary status.</p>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">🎯</div>
                        <div class="feature-title">Level Up</div>
                        <div class="feature-description">
                            <strong>Formula:</strong> Level = 1 + √(XP/100)<br>
                            Gain XP from adventures, battles, and raids. Each level increases base stats.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🔄</div>
                        <div class="feature-title">Class Evolution</div>
                        <div class="feature-description">
                            <strong>Levels 5, 10, 15, 20, 25, 30, 50, 100:</strong><br>
                            Choose new class specializations through 8 tiers. Plan your path carefully!
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">⚖️</div>
                        <div class="feature-title">Alignment</div>
                        <div class="feature-description">
                            <strong>Good, Neutral, Evil:</strong><br>
                            Affects god choices and some game mechanics. Choose wisely.
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🏆</div>
                        <div class="feature-title">Endgame</div>
                        <div class="feature-description">
                            <strong>Ascendant → Apex → Universal Sovereign:</strong><br>
                            Choose specialized endgame paths at level 30+, culminating in Universal Sovereign at level 100.
                        </div>
                    </div>
                </div>
                
                <div class="success-box">
                    <h3>Progression Strategy</h3>
                    <p><strong>Early Game (1-5):</strong> Stay online, let auto-play work, focus on reaching level 5</p>
                    <p><strong>Mid Game (5-20):</strong> Choose classes wisely, participate in raids, build wealth</p>
                    <p><strong>Late Game (20-100):</strong> Optimize builds, dominate leaderboards, master your specialization path</p>
                </div>
            </section>

            <!-- FAQ Section -->
            <section id="faq" class="section">
                <h2>❓ Frequently Asked Questions</h2>
                <p>Common questions and answers about DiscordRPG gameplay.</p>
                
                <div class="info-box">
                    <h3>Q: Why isn't my character progressing?</h3>
                    <p>A: Make sure your Discord status is set to <strong>Online (green)</strong>. Away, DND, or Invisible statuses prevent participation in auto-gameplay.</p>
                </div>

                <div class="info-box">
                    <h3>Q: When can I evolve my class?</h3>
                    <p>A: Classes can evolve at levels 5, 10, 15, 20, 25, 30, 50, and 100. Use <code>!evolve</code> when you reach these levels to see available options and advance along your chosen specialization path.</p>
                </div>
                
                <div class="info-box" style="border-color: #00d4aa;">
                    <h3>Q: How does the class evolution system work?</h3>
                    <p>A: <strong>Clean Evolution System:</strong> Each class line maintains its unique identity through all 8 tiers without forced convergence points.</p>
                    <p><strong>Progression:</strong> Use <code>!evolve</code> at levels 5, 10, 15, 20, 25, 30, 50, and 100 to advance your specialization.</p>
                    <p><strong>Universal Sovereign (Level 100):</strong> All paths can reach this ultimate class representing mastery of your chosen specialization.</p>
                </div>

                <div class="info-box">
                    <h3>Q: Are race and god choices permanent?</h3>
                    <p>A: Yes! Both race and god selections are permanent and cannot be changed. Choose carefully based on your preferred playstyle.</p>
                </div>

                <div class="info-box">
                    <h3>Q: How does the battle system work?</h3>
                    <p>A: Battles are automatic and scale based on online players: 1v1 (2+ players), 3v3 (6+ players), 5v5 (10+ players), 10v10 (20+ players). Larger battles have coordination penalties but bigger rewards!</p>
                </div>

                <div class="info-box">
                    <h3>Q: How does the raid system work?</h3>
                    <p>A: Raids happen automatically every 35 minutes. 20-40 random online players are selected to fight epic bosses together. Stay online to participate!</p>
                </div>

                <div class="info-box">
                    <h3>Q: What are the adventure tiers?</h3>
                    <p>A: Adventures come in 5 tiers! Regular adventures (Short/Medium/Long) are based on character level. Epic adventures (4-8h, level 10+) and Legendary adventures (8-24h, level 15+) are special automatic parallel adventures that run alongside regular adventures. Epic/Legendary provide massive rewards but have lower success rates!</p>
                </div>

                <div class="info-box">
                    <h3>Q: What's the level formula?</h3>
                    <p>A: Level = 1 + √(XP/100). For example, 10,000 XP = Level 11. The XP requirement increases exponentially.</p>
                </div>

                <div class="info-box">
                    <h3>Q: Do losers get rewards in battles?</h3>
                    <p>A: Yes! Winners get higher XP/gold and 25-30% item drop chance, but losers still get XP and 5% item drop chance. Everyone benefits from participation!</p>
                </div>

                <div class="info-box">
                    <h3>Q: How does the armor system work?</h3>
                    <p>A: DiscordRPG features a 5-slot armor system (head, chest, legs, hands, feet) with specialized stat bonuses. Armor provides NO damage - only defensive stats like armor, health, speed, luck, crit, and magic. All armor bonuses factor directly into combat calculations!</p>
                </div>

                <div class="info-box">
                    <h3>Q: Can I play this manually?</h3>
                    <p>A: DiscordRPG is designed to be fully automated! Just stay online and let the game progress naturally. You can use commands to check progress and make strategic choices.</p>
                </div>
                
                <div class="info-box" style="border-color: #00d4aa;">
                    <h3>Q: What's special about the 8-tier evolution system?</h3>
                    <p>A: <strong>No Forced Convergence:</strong> Each class maintains its unique identity throughout all tiers. Warriors stay warriors, Mages stay mages, etc.</p>
                    <p>A: <strong>Clear Progression:</strong> Evolution levels are 5, 10, 15, 20, 25, 30, 50, 100 - no complex requirements or permanent choice points.</p>
                    <p>A: <strong>Universal Sovereign:</strong> All paths reach the same ultimate class at level 100, representing mastery of your chosen specialization.</p>
                </div>
            </section>

            <!-- Footer -->
            <div style="text-align: center; padding: 40px; background: var(--card-bg); border: 1px solid var(--border-subtle); border-radius: 8px; margin-top: 40px;">
                <h2 style="font-family: 'Orbitron', monospace; color: var(--text-accent); margin-bottom: 16px;">
                    Ready to Begin Your Adventure?
                </h2>
                <p style="margin-bottom: 24px; font-size: 1.1em; color: var(--text-secondary);">
                    Join the DiscordRPG universe and become a legendary warrior!
                </p>
                <div style="display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; margin-bottom: 20px;">
                    <a href="index.php" style="display: inline-flex; align-items: center; gap: 8px; background: var(--secondary-bg); color: var(--text-primary); padding: 12px 20px; border-radius: 6px; text-decoration: none; font-weight: 500; transition: all 0.2s ease; border: 1px solid var(--border-subtle);">
                        <i class="fas fa-trophy"></i> View Leaderboards
                    </a>
                    <a href="top-items.php" style="display: inline-flex; align-items: center; gap: 8px; background: var(--secondary-bg); color: var(--text-primary); padding: 12px 20px; border-radius: 6px; text-decoration: none; font-weight: 500; transition: all 0.2s ease; border: 1px solid var(--border-subtle);">
                        <i class="fas fa-crown"></i> Top Items
                    </a>
                    <a href="#getting-started" class="nav-item" data-section="getting-started" style="display: inline-flex; align-items: center; gap: 8px; background: var(--accent-bg); color: var(--text-accent); padding: 12px 20px; border-radius: 6px; text-decoration: none; font-weight: 500; transition: all 0.2s ease; border: 1px solid var(--border-accent);">
                        <i class="fas fa-play"></i> Start Playing
                    </a>
                </div>
                <p style="opacity: 0.7; font-size: 0.9em;">
                    Use <code>!help</code> in Discord for quick command reference
                </p>
            </div>
            </div>
        </main>
    </div>
    
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const navItems = document.querySelectorAll('.nav-item');
        const sections = document.querySelectorAll('.section');
        const sidebar = document.getElementById('sidebar');
        
        // Handle navigation clicks
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetSection = item.getAttribute('data-section');
                
                if (!targetSection) return;
                
                // Update active nav item
                navItems.forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');
                
                // Show target section
                sections.forEach(section => {
                    if (section.id === targetSection) {
                        section.classList.add('active');
                    } else {
                        section.classList.remove('active');
                    }
                });
                
                // Update URL hash
                window.location.hash = targetSection;
                
                // Hide sidebar on mobile after selection
                if (window.innerWidth <= 1024) {
                    sidebar.classList.remove('active');
                    updateMobileToggle();
                }
            });
        });
        
        // Handle initial load with hash
        const hash = window.location.hash.slice(1);
        if (hash) {
            const targetItem = document.querySelector(`[data-section="${hash}"]`);
            if (targetItem) {
                targetItem.click();
            }
        }
        
        // Handle browser back/forward
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.slice(1);
            const targetItem = document.querySelector(`[data-section="${hash}"]`);
            if (targetItem) {
                targetItem.click();
            }
        });
    });

    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('active');
        updateMobileToggle();
    }

    function updateMobileToggle() {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.querySelector('.mobile-menu-toggle');
        
        if (sidebar.classList.contains('active')) {
            toggle.innerHTML = '<i class="fas fa-times"></i>';
        } else {
            toggle.innerHTML = '<i class="fas fa-bars"></i>';
        }
    }

    // Handle responsive behavior
    window.addEventListener('resize', () => {
        const sidebar = document.getElementById('sidebar');
        if (window.innerWidth > 1024) {
            sidebar.classList.remove('active');
            updateMobileToggle();
        }
    });

    // Initialize mobile toggle
    updateMobileToggle();
    </script>
</body>
</html>