<?php

declare(strict_types=1);

namespace Mcp\Tests;

use Mcp\McpHandler;
use Mcp\Tools;
use Mcp\UserRepository;
use PDO;
use PHPUnit\Framework\TestCase;

/** Runs against the seeded MySQL from data/db/init, using the read-only account. */
abstract class McpTestCase extends TestCase
{
    protected McpHandler $handler;

    protected function setUp(): void
    {
        $pdo = new PDO(
            sprintf('mysql:host=%s;dbname=%s;charset=utf8mb4', getenv('DB_HOST') ?: 'mysql', getenv('DB_NAME') ?: 'demo'),
            getenv('DB_USER') ?: 'readonly',
            getenv('DB_PASSWORD') ?: '',
            [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
        );
        $this->handler = new McpHandler(new Tools(new UserRepository($pdo)));
    }

    /** @return array<string, mixed> decoded tool result payload */
    protected function callTool(string $name, array $arguments): array
    {
        $response = $this->handler->handle([
            'jsonrpc' => '2.0', 'id' => 1, 'method' => 'tools/call',
            'params' => ['name' => $name, 'arguments' => $arguments],
        ]);
        $this->assertArrayHasKey('result', $response);

        return $response['result'];
    }

    protected function payload(array $result): array
    {
        return json_decode($result['content'][0]['text'], true, 512, JSON_THROW_ON_ERROR);
    }
}
