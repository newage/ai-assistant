<?php

declare(strict_types=1);

namespace Mcp;

use PDO;

final class UserRepository
{
    public function __construct(private readonly PDO $pdo)
    {
    }

    public function findById(int $id): ?array
    {
        $stmt = $this->pdo->prepare('SELECT id, email, name, created_at FROM users WHERE id = :id');
        $stmt->execute(['id' => $id]);

        return $stmt->fetch(PDO::FETCH_ASSOC) ?: null;
    }

    public function findByEmail(string $email): ?array
    {
        $stmt = $this->pdo->prepare('SELECT id, email, name, created_at FROM users WHERE email = :email');
        $stmt->execute(['email' => $email]);

        return $stmt->fetch(PDO::FETCH_ASSOC) ?: null;
    }

    /** @return list<array<string, mixed>> */
    public function activityForUser(int $userId): array
    {
        $stmt = $this->pdo->prepare(
            'SELECT id, action, created_at FROM user_activity WHERE user_id = :id ORDER BY created_at DESC, id DESC'
        );
        $stmt->execute(['id' => $userId]);

        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
}
