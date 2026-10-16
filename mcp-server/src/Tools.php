<?php

declare(strict_types=1);

namespace Mcp;

/**
 * The two MCP tools. Each handler returns an MCP tool result:
 * {content: [{type: text, text: <json>}], isError: bool}.
 */
final class Tools
{
    public function __construct(private readonly UserRepository $users)
    {
    }

    /** @return list<array<string, mixed>> */
    public function definitions(): array
    {
        return [
            [
                'name' => 'find_user_profile',
                'description' => 'Find a user profile (id, email, name, created_at) by user ID or email. Provide at least one.',
                'inputSchema' => [
                    'type' => 'object',
                    'properties' => [
                        'user_id' => ['type' => 'integer', 'description' => 'User ID'],
                        'email' => ['type' => 'string', 'description' => 'User email'],
                    ],
                ],
            ],
            [
                'name' => 'get_user_activity',
                'description' => 'Get the activity records (id, action, created_at) of a user by user ID, newest first.',
                'inputSchema' => [
                    'type' => 'object',
                    'properties' => [
                        'user_id' => ['type' => 'integer', 'description' => 'User ID'],
                    ],
                    'required' => ['user_id'],
                ],
            ],
        ];
    }

    /** @param array<string, mixed> $arguments */
    public function call(string $name, array $arguments): ?array
    {
        return match ($name) {
            'find_user_profile' => $this->findUserProfile($arguments),
            'get_user_activity' => $this->getUserActivity($arguments),
            default => null,
        };
    }

    /** @param array<string, mixed> $args */
    private function findUserProfile(array $args): array
    {
        $hasId = isset($args['user_id']) && $args['user_id'] !== '';
        $email = isset($args['email']) && is_string($args['email']) ? trim($args['email']) : '';

        if (!$hasId && $email === '') {
            return self::error('Validation error: provide user_id or email.');
        }

        $user = null;
        if ($hasId) {
            if (!is_numeric($args['user_id'])) {
                return self::error('Validation error: user_id must be an integer.');
            }
            $user = $this->users->findById((int) $args['user_id']);
        }
        if ($user === null && $email !== '') {
            $user = $this->users->findByEmail($email);
        }

        return $user === null ? self::error('User not found.') : self::ok($user);
    }

    /** @param array<string, mixed> $args */
    private function getUserActivity(array $args): array
    {
        if (!isset($args['user_id']) || !is_numeric($args['user_id'])) {
            return self::error('Validation error: user_id (integer) is required.');
        }
        $userId = (int) $args['user_id'];

        if ($this->users->findById($userId) === null) {
            return self::error('User not found.');
        }

        return self::ok(['user_id' => $userId, 'activity' => $this->users->activityForUser($userId)]);
    }

    private static function ok(array $data): array
    {
        return [
            'content' => [['type' => 'text', 'text' => json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)]],
            'isError' => false,
        ];
    }

    private static function error(string $message): array
    {
        return ['content' => [['type' => 'text', 'text' => $message]], 'isError' => true];
    }
}
