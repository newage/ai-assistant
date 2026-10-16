<?php

declare(strict_types=1);

namespace Mcp\Tests;

final class ProtocolTest extends McpTestCase
{
    public function testInitialize(): void
    {
        $r = $this->handler->handle(['jsonrpc' => '2.0', 'id' => 1, 'method' => 'initialize', 'params' => []]);

        $this->assertArrayHasKey('tools', $r['result']['capabilities']);
        $this->assertSame('2025-03-26', $r['result']['protocolVersion']);
    }

    public function testToolsListContainsExactlyTheTwoTools(): void
    {
        $r = $this->handler->handle(['jsonrpc' => '2.0', 'id' => 2, 'method' => 'tools/list']);

        $names = array_column($r['result']['tools'], 'name');
        sort($names);
        $this->assertSame(['find_user_profile', 'get_user_activity'], $names);
    }

    public function testNotificationHasNoResponse(): void
    {
        $this->assertNull($this->handler->handle(['jsonrpc' => '2.0', 'method' => 'notifications/initialized']));
    }

    public function testUnknownMethod(): void
    {
        $r = $this->handler->handle(['jsonrpc' => '2.0', 'id' => 3, 'method' => 'nope']);

        $this->assertSame(-32601, $r['error']['code']);
    }

    public function testUnknownTool(): void
    {
        $r = $this->handler->handle([
            'jsonrpc' => '2.0', 'id' => 4, 'method' => 'tools/call', 'params' => ['name' => 'drop_tables'],
        ]);

        $this->assertSame(-32602, $r['error']['code']);
    }

    public function testReadOnlyAccountCannotWrite(): void
    {
        $pdo = new \PDO(
            sprintf('mysql:host=%s;dbname=%s', getenv('DB_HOST') ?: 'mysql', getenv('DB_NAME') ?: 'demo'),
            getenv('DB_USER') ?: 'readonly',
            getenv('DB_PASSWORD') ?: '',
            [\PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION]
        );
        $this->expectException(\PDOException::class);
        $pdo->exec("INSERT INTO users (email, name) VALUES ('w@example.com', 'W')");
    }
}
