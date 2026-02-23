<?php
/**
 * DiscordRPG Database Configuration
 *
 * This file reads database credentials from the bot's .env file.
 * Adjust the $env_path below to point to your DiscordRPG .env file.
 */

// Path to your DiscordRPG .env file
$env_path = __DIR__ . '/../.env';

function get_discordrpg_pdo(): PDO {
    global $env_path;

    if (!file_exists($env_path)) {
        throw new RuntimeException(
            "Environment file not found at: $env_path\n" .
            "Copy .env.example to .env and fill in your database credentials."
        );
    }

    $env = [];
    foreach (file($env_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);
        if ($line === '' || $line[0] === '#') continue;
        if (strpos($line, '=') === false) continue;
        [$key, $value] = explode('=', $line, 2);
        $env[trim($key)] = trim($value);
    }

    $host = $env['DB_HOST'] ?? 'localhost';
    $name = $env['DB_NAME'] ?? 'discordrpg';
    $user = $env['DB_USER'] ?? '';
    $pass = $env['DB_PASS'] ?? '';

    $pdo = new PDO(
        "mysql:host=$host;dbname=$name;charset=utf8mb4",
        $user,
        $pass
    );
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    return $pdo;
}
